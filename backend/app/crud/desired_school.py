from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional

from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.schemas.desired_school import DesiredSchoolCreate, DesiredSchoolUpdate, DesiredDepartmentCreate
from app.core.exceptions import NotFoundError, ConflictError, DatabaseError


# --- DesiredSchool CRUD --- #

def create_desired_school(db: Session, *, user_id: UUID, obj_in: DesiredSchoolCreate) -> DesiredSchool:
    """指定されたユーザーIDと志望校情報で新しいDesiredSchoolを作成し、関連するDesiredDepartmentも作成する"""
    db_desired_school = DesiredSchool(
        user_id=user_id,
        university_id=obj_in.university_id,
        preference_order=obj_in.preference_order
    )
    db.add(db_desired_school)

    try:
        # まずDesiredSchoolをコミットしてIDを確定させる
        db.flush() # flush() はコミットせずDBに変更を送りIDなどを取得する

        created_departments = []
        for dept_in in obj_in.desired_departments:
            db_dept = DesiredDepartment(
                desired_school_id=db_desired_school.id, # 確定したIDを使用
                department_id=dept_in.department_id,
                admission_method_id=dept_in.admission_method_id
            )
            created_departments.append(db_dept)
        
        if created_departments:
            db.add_all(created_departments)
        
        db.commit() # 全ての変更をコミット
        db.refresh(db_desired_school) # 関連情報を含めてリフレッシュ
        # 必要なら関連部門もリフレッシュ
        for dept in created_departments:
             db.refresh(dept)
        return db_desired_school
    except IntegrityError as e:
        db.rollback()
        # 制約違反の詳細に応じてエラーメッセージを調整
        if "uq_user_university_preference" in str(e.orig): # 例: ユニーク制約名
            raise ConflictError(f"ユーザーID {user_id} は既に大学ID {obj_in.university_id} を登録済みか、同じ志望順位 {obj_in.preference_order} が存在します。")
        elif "fk_" in str(e.orig): # 外部キー制約違反
             raise NotFoundError(f"関連データ（大学、学部、入試方式など）が見つかりません。詳細: {e.orig}")
        else:
             raise DatabaseError(f"志望校の作成中にデータベースエラーが発生しました: {e}")
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"志望校の作成中に予期せぬエラーが発生しました: {e}")

def get_desired_school(db: Session, *, desired_school_id: UUID) -> Optional[DesiredSchool]:
    """指定されたIDのDesiredSchoolを関連するDesiredDepartmentと共に取得する"""
    return (
        db.query(DesiredSchool)
        .options(joinedload(DesiredSchool.desired_departments))
        .filter(DesiredSchool.id == desired_school_id)
        .first()
    )

def get_desired_schools_by_user(db: Session, *, user_id: UUID, skip: int = 0, limit: int = 100) -> List[DesiredSchool]:
    """指定されたユーザーIDのDesiredSchoolリストを関連するDesiredDepartmentと共に取得する"""
    return (
        db.query(DesiredSchool)
        .options(joinedload(DesiredSchool.desired_departments))
        .filter(DesiredSchool.user_id == user_id)
        .order_by(DesiredSchool.preference_order) # 志望順位でソート
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_desired_school(db: Session, *, db_obj: DesiredSchool, obj_in: DesiredSchoolUpdate) -> DesiredSchool:
    """既存のDesiredSchoolオブジェクトを更新する。DesiredDepartmentの更新は別途実装が必要"""
    update_data = obj_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    # TODO: DesiredDepartmentリストの更新ロジックを追加する場合
    # if obj_in.desired_departments is not None:
        # 既存のdepartmentsを削除して新しいもので置き換える、など
        # pass

    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        db.rollback()
        # ユニーク制約違反などのハンドリング
        raise ConflictError(f"更新により制約違反が発生しました。詳細: {e.orig}")
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"志望校の更新中にエラーが発生しました: {e}")

def delete_desired_school(db: Session, *, desired_school_id: UUID) -> DesiredSchool:
    """指定されたIDのDesiredSchoolと関連するDesiredDepartmentを削除する"""
    db_obj = get_desired_school(db, desired_school_id=desired_school_id) # 関連ロード済み
    if not db_obj:
        raise NotFoundError(f"ID {desired_school_id} の志望校が見つかりません。")

    try:
        # 関連する DesiredDepartment を先に削除 (CASCADE設定がない場合)
        # for dept in db_obj.desired_departments:
        #     db.delete(dept)
        # db.flush() # DesiredDepartmentの削除を反映
        
        # DesiredSchool を削除
        db.delete(db_obj)
        db.commit()
        # 削除されたオブジェクトを返す（IDなどはまだアクセス可能）
        return db_obj
    except IntegrityError as e:
        db.rollback()
        raise DatabaseError(f"志望校の削除中に他のデータとの整合性エラーが発生しました: {e.orig}")
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"志望校の削除中にエラーが発生しました: {e}")

# --- DesiredDepartment CRUD (必要に応じて追加) --- #
# 例: 特定の学部だけを追加・削除する関数など 