from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.content import Content, ContentCategory, ContentCategoryRelation, ContentTag
from app.schemas.content import ContentCreate, ContentUpdate, ContentCategory as ContentCategoryEnum
from uuid import UUID
from fastapi import HTTPException

def get_category_by_name(db: Session, category_name: ContentCategoryEnum) -> Optional[ContentCategory]:
    """カテゴリ名 (Enum値) で ContentCategory を検索するヘルパー関数"""
    # Enum の .value で実際の文字列値を取得して比較
    return db.query(ContentCategory).filter(ContentCategory.name == category_name.value).first()

def create_content(db: Session, content: ContentCreate) -> Content:
    # 1. モデルに渡す基本データを取得 (Enum は値に変換される)
    content_data = content.model_dump(exclude={'category', 'tags', 'created_by_id', 'author', 'difficulty', 'content_type'}) # content_type も除外

    # ★★★ duration の値をチェック・変換 ★★★
    if 'duration' in content_data and not isinstance(content_data['duration'], (int, type(None))):
        try:
            # 空文字列などを None に変換、数値文字列は int に変換
            duration_val = content_data['duration']
            # str(duration_val).strip() で空白文字のみの場合も空として扱う
            content_data['duration'] = int(duration_val) if duration_val is not None and str(duration_val).strip() else None
        except (ValueError, TypeError):
            # 変換できない場合は None にする (またはエラーにする)
            print(f"警告: duration の値 '{content_data['duration']}' を整数に変換できませんでした。None として扱います。")
            content_data['duration'] = None

    # 2. Content インスタンスを作成し、Enum メンバーを明示的に渡す
    db_content = Content(
        **content_data,                   # 他のデータはそのまま渡す
        content_type=content.content_type.name  # DBのEnumが大文字ラベル(SLIDE等)を期待するため、nameを渡す
    )

    # 3. DBに追加してIDを割り当て
    db.add(db_content)
    try:
      db.flush() # ID を確定させるために flush
    except Exception as e:
        db.rollback()
        print(f"データベース flush エラー (Content 追加時): {e}")
        # エラーメッセージにSQLとパラメータを含める (デバッグ用)
        if hasattr(e, 'params') and hasattr(e, 'statement'):
             print(f"SQL: {e.statement}")
             print(f"Params: {e.params}")
        raise HTTPException(status_code=500, detail="コンテンツ基本情報の保存中にエラーが発生しました。")

    # 4. カテゴリの処理
    if content.category:
        db_category = get_category_by_name(db, content.category)
        if not db_category:
             # 存在しないカテゴリが指定された場合のエラーハンドリング
             print(f"警告: カテゴリ '{content.category.value}' が見つかりません。関連付けはスキップされます。")
             # 必要であれば HTTPException を raise する
             # raise HTTPException(status_code=400, detail=f"カテゴリ '{content.category.value}' が見つかりません")
        else:
            # 中間テーブルにレコードを作成
            db_relation = ContentCategoryRelation(
                content_id=db_content.id,
                category_id=db_category.id
            )
            db.add(db_relation)
            try:
                db.flush() # 関連レコードの flush
            except Exception as e:
                db.rollback()
                print(f"データベース flush エラー (カテゴリ関連付け時): {e}")
                raise HTTPException(status_code=500, detail="カテゴリ情報の保存中にエラーが発生しました。")


    # 5. タグの処理
    if content.tags:
        for tag_name in content.tags:
            if tag_name and tag_name.strip(): # 空や空白のみのタグは無視
                db_tag = ContentTag(
                    content_id=db_content.id,
                    tag_name=tag_name.strip() # 前後の空白を削除
                )
                db.add(db_tag)
        try:
            db.flush() # タグ関連レコードの flush
        except Exception as e:
            db.rollback()
            print(f"データベース flush エラー (タグ追加時): {e}")
            raise HTTPException(status_code=500, detail="タグ情報の保存中にエラーが発生しました。")

    # 6. created_by_id, author, difficulty は Content モデルに直接保存しない
    #    必要であればここで監査ログ等への保存処理を行う

    # 7. すべての変更をコミット
    try:
        db.commit()
    except Exception as e:
        db.rollback() # エラーが発生したらロールバック
        print(f"データベースコミットエラー: {e}")
        # commit エラーはより一般的なメッセージにするか、詳細をログに残す
        raise HTTPException(status_code=500, detail="コンテンツの保存中に最終エラーが発生しました。")

    db.refresh(db_content) # リレーションを含めて最新の状態を読み込む
    return db_content

def get_content(db: Session, content_id: UUID) -> Optional[Content]:
    return db.query(Content).filter(Content.id == content_id).first()

def get_contents(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    content_type: Optional[str] = None
) -> List[Content]:
    query = db.query(Content)
    if content_type:
        query = query.filter(Content.content_type == content_type)
    return query.offset(skip).limit(limit).all()

def update_content(
    db: Session,
    content_id: UUID,
    content_update: ContentUpdate
) -> Optional[Content]:
    db_content = get_content(db, content_id)
    if db_content:
        # 更新データから除外するフィールドリスト
        exclude_fields = {'category', 'tags', 'author', 'difficulty', 'content_type'}
        update_data = content_update.model_dump(exclude_unset=True, exclude=exclude_fields)

        # 基本フィールドを更新
        for key, value in update_data.items():
            setattr(db_content, key, value)

        # content_type が更新データに含まれていれば Enum メンバーで上書き
        # Pydantic V2: Check if field was explicitly set using __fields_set__ or check against exclude_unset logic implicitly handled by model_dump
        if content_update.content_type is not None and 'content_type' not in content_update.model_dump(exclude_unset=True, exclude=exclude_fields).keys() :
             # Correction: Check if content_type was provided in the update request *before* excluding it.
             # We access the original model before dump or check the __fields_set__ if available
             # Simpler approach: check if it was provided in the original content_update object
             original_update_dict = content_update.model_dump(exclude_unset=True)
             if 'content_type' in original_update_dict:
                  # DBのEnumラベルに合わせて大文字のnameを利用
                  db_content.content_type = content_update.content_type.name

        # ★★★ duration の値をチェック・変換 (更新時) ★★★
        if 'duration' in update_data and not isinstance(update_data['duration'], (int, type(None))):
            try:
                duration_val = update_data['duration']
                # Check if duration was actually provided before setting it
                if 'duration' in original_update_dict:
                    db_content.duration = int(duration_val) if duration_val is not None and str(duration_val).strip() else None
            except (ValueError, TypeError):
                print(f"警告: 更新時の duration の値 '{duration_val}' を整数に変換できませんでした。None として扱います。")
                # Set to None only if it was part of the update request
                if 'duration' in original_update_dict:
                    db_content.duration = None

        # TODO: category と tags の更新処理をここに追加
        #       - 古い関連を削除し、新しい関連を追加するなど

        try:
            db.commit()
            db.refresh(db_content)
        except Exception as e:
            db.rollback()
            print(f"データベース更新エラー: {e}")
            raise HTTPException(status_code=500, detail="コンテンツ更新中にエラーが発生しました。")
    return db_content

def delete_content(db: Session, content_id: UUID) -> bool:
    db_content = get_content(db, content_id)
    if db_content:
        # 関連レコード (tags, category_relations) の削除も考慮する必要がある
        # Cascade delete が設定されていれば自動で削除される場合もある
        # 手動で削除する場合:
        # db.query(ContentTag).filter(ContentTag.content_id == content_id).delete()
        # db.query(ContentCategoryRelation).filter(ContentCategoryRelation.content_id == content_id).delete()
        db.delete(db_content)
        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"データベース削除エラー: {e}")
            raise HTTPException(status_code=500, detail="コンテンツ削除中にエラーが発生しました。")
    return False 