from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.models.content import Content, ContentCategory, ContentCategoryRelation, ContentTag
from app.schemas.content import ContentCreate, ContentUpdate, ContentCategoryInfo
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import selectinload

async def create_content(db: AsyncSession, content: ContentCreate) -> Content:
    # 1. モデルに渡す基本データを取得
    content_data = content.model_dump(exclude={'category_id', 'tags', 'created_by_id', 'author', 'difficulty', 'content_type', 'provider', 'provider_item_id'})

    # ★★★ duration の値をチェック・変換 ★★★
    if 'duration' in content_data and not isinstance(content_data['duration'], (int, type(None))):
        try:
            duration_val = content_data['duration']
            content_data['duration'] = int(duration_val) if duration_val is not None and str(duration_val).strip() else None
        except (ValueError, TypeError):
            print(f"警告: duration の値 '{content_data['duration']}' を整数に変換できませんでした。None として扱います。")
            content_data['duration'] = None

    # 2. Content インスタンスを作成
    db_content = Content(
        **content_data,
        content_type=content.content_type.name,
        created_by_id=content.created_by_id,
        provider=content.provider,
        provider_item_id=content.provider_item_id
    )

    # 3. DBに追加してIDを割り当て
    db.add(db_content)
    try:
      await db.flush()
    except Exception as e:
        await db.rollback()
        print(f"データベース flush エラー (Content 追加時): {e}")
        if hasattr(e, 'params') and hasattr(e, 'statement'):
             print(f"SQL: {e.statement}")
             print(f"Params: {e.params}")
        raise HTTPException(status_code=500, detail="コンテンツ基本情報の保存中にエラーが発生しました。")

    # 4. カテゴリの処理 (★ category_id を使用するように変更)
    if content.category_id:
        db_relation = ContentCategoryRelation(
            content_id=db_content.id,
            category_id=content.category_id # Use category_id directly
        )
        db.add(db_relation)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            print(f"データベース flush エラー (カテゴリ関連付け時): {e}")
            raise HTTPException(status_code=500, detail="カテゴリ情報の保存中にエラーが発生しました。")

    # 5. タグの処理
    if content.tags:
        for tag_name in content.tags:
            if tag_name and tag_name.strip():
                db_tag = ContentTag(
                    content_id=db_content.id,
                    tag_name=tag_name.strip()
                )
                db.add(db_tag)
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            print(f"データベース flush エラー (タグ追加時): {e}")
            raise HTTPException(status_code=500, detail="タグ情報の保存中にエラーが発生しました。")

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"データベースコミットエラー: {e}")
        raise HTTPException(status_code=500, detail="コンテンツの保存中に最終エラーが発生しました。")

    await db.refresh(db_content) 

    return db_content

async def get_content(db: AsyncSession, content_id: UUID) -> Optional[Content]:
    # result = await db.execute(select(Content).filter(Content.id == content_id))
    # Eager load category_relations and its nested category, and tags
    result = await db.execute(
        select(Content)
        .options(
            selectinload(Content.category_relations).selectinload(ContentCategoryRelation.category),
            selectinload(Content.tags)
        )
        .filter(Content.id == content_id)
    )
    db_content = result.scalars().first()
    if db_content: # ★ 古い category Enum のセットアップロジックを削除
        # Pydanticモデルへの変換のために category 属性をセット
        if db_content.category_relations and db_content.category_relations[0].category:
            try:
                # ContentCategoryInfo.from_orm を使用
                db_content.category_info = ContentCategoryInfo.from_orm(db_content.category_relations[0].category)
            except Exception as e:
                # 変換エラーのログ出力など
                print(f"Error converting category to ContentCategoryInfo: {e}")
                db_content.category_info = None # エラー時は None にフォールバック
        else:
            # category_relations がない場合や、関連categoryがない場合はデフォルト値を設定
            db_content.category_info = None 
    return db_content

async def get_contents(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    content_type: Optional[str] = None
) -> List[Content]:
    query = (
        select(Content)
        .options(
            selectinload(Content.category_relations).selectinload(ContentCategoryRelation.category),
            selectinload(Content.tags)
        )
    )
    if content_type:
        query = query.filter(Content.content_type == content_type)
    
    result = await db.execute(query.order_by(Content.created_at.desc()).offset(skip).limit(limit)) # created_at でソートする例
    all_contents = result.scalars().all()
    
    # ★ 古い category Enum のセットアップロジックをループ内から削除
    # for db_content_item in all_contents:
    #     if db_content_item.category_relations and db_content_item.category_relations[0].category:
    #         try:
    #             db_content_item.category = ContentCategoryEnum(db_content_item.category_relations[0].category.name)
    #         except ValueError:
    #             print(f"警告: DBのカテゴリ名 '{db_content_item.category_relations[0].category.name}' を ContentCategoryEnumに変換できませんでした。")
    #             db_content_item.category = ContentCategoryEnum.OTHER
    #     else:
    #         db_content_item.category = ContentCategoryEnum.OTHER
            
    return all_contents

async def update_content(
    db: AsyncSession,
    content_id: UUID,
    content_update: ContentUpdate
) -> Optional[Content]:
    db_content = await db.get(Content, content_id)
    if db_content:
        # 更新データから除外するフィールドリストに provider と provider_item_id を追加 (これらは個別処理するため)
        exclude_fields = {'category_id', 'tags', 'author', 'difficulty', 'content_type', 'provider', 'provider_item_id'}
        update_data = content_update.model_dump(exclude_unset=True, exclude=exclude_fields)

        # 基本フィールドを更新
        for key, value in update_data.items():
            setattr(db_content, key, value)

        # content_type の更新
        if content_update.content_type is not None and 'content_type' in content_update.model_fields_set:
            db_content.content_type = content_update.content_type.name

        # duration の更新
        if 'duration' in content_update.model_fields_set and 'duration' in update_data:
            duration_val = update_data['duration']
            try:
                db_content.duration = int(duration_val) if duration_val is not None and str(duration_val).strip() else None
            except (ValueError, TypeError):
                print(f"警告: 更新時の duration の値 '{duration_val}' を整数に変換できませんでした。None として扱います。")
                db_content.duration = None
        elif 'duration' in content_update.model_fields_set and update_data.get('duration') is None:
            # 明示的に null が渡された場合
            db_content.duration = None

        # ★ provider と provider_item_id の更新処理を追加
        if 'provider' in content_update.model_fields_set:
            db_content.provider = content_update.provider
        if 'provider_item_id' in content_update.model_fields_set:
            db_content.provider_item_id = content_update.provider_item_id

        # カテゴリの更新処理
        # 1. 既存のカテゴリ関連を削除
        await db.execute(delete(ContentCategoryRelation).where(ContentCategoryRelation.content_id == db_content.id))
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            print(f"データベース flush エラー (既存カテゴリ関連削除時): {e}")
            raise HTTPException(status_code=500, detail="既存カテゴリ関連の削除中にエラーが発生しました。")

        # 2. 新しいカテゴリIDが提供されていれば、新しい関連を作成
        if 'category_id' in content_update.model_fields_set and content_update.category_id is not None:
            new_relation = ContentCategoryRelation(
                content_id=db_content.id,
                category_id=content_update.category_id
            )
            db.add(new_relation)
            try:
                await db.flush()
            except Exception as e:
                await db.rollback()
                print(f"データベース flush エラー (新規カテゴリ関連作成時): {e}")
                raise HTTPException(status_code=500, detail="新規カテゴリ関連の作成中にエラーが発生しました。")
        
        # タグの更新処理
        # 1. 既存のタグを削除
        await db.execute(delete(ContentTag).where(ContentTag.content_id == db_content.id))
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            print(f"データベース flush エラー (既存タグ削除時): {e}")
            raise HTTPException(status_code=500, detail="既存タグの削除中にエラーが発生しました。")

        # 2. 新しいタグが提供されていれば追加
        if 'tags' in content_update.model_fields_set and content_update.tags:
            for tag_name in content_update.tags:
                if tag_name and tag_name.strip():
                    db_tag = ContentTag(content_id=db_content.id, tag_name=tag_name.strip())
                    db.add(db_tag)
            try:
                await db.flush()
            except Exception as e:
                await db.rollback()
                print(f"データベース flush エラー (新規タグ追加時): {e}")
                raise HTTPException(status_code=500, detail="新規タグの追加中にエラーが発生しました。")

        try:
            await db.commit()
            await db.refresh(db_content)
        except Exception as e:
            await db.rollback()
            print(f"データベース更新コミットエラー: {e}")
            raise HTTPException(status_code=500, detail="コンテンツ更新中に最終エラーが発生しました。")
    return db_content

async def delete_content(db: AsyncSession, content_id: UUID) -> bool:
    db_content = await get_content(db, content_id)
    if db_content:
        # 関連レコード (tags, category_relations) の削除も考慮する必要がある
        # Cascade delete が設定されていれば自動で削除される場合もある
        # 手動で削除する場合のコメントアウトは残しておいても良い
        # await db.execute(delete(ContentTag).where(ContentTag.content_id == content_id))
        # await db.execute(delete(ContentCategoryRelation).where(ContentCategoryRelation.content_id == content_id))
        
        await db.delete(db_content)
        try:
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            # エラーメッセージにエラー内容を含めるのはデバッグに有用なので残す
            print(f"データベース削除エラー: {e}") 
            raise HTTPException(status_code=500, detail=f"コンテンツ削除中にエラーが発生しました。詳細: {str(e)}")
    return False 

async def get_all_content_categories(db: AsyncSession) -> List[ContentCategory]:
    result = await db.execute(select(ContentCategory).order_by(ContentCategory.display_order, ContentCategory.name))
    return result.scalars().all() 