from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional, Tuple

from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.models.university import University, Department
from app.schemas.desired_school import DesiredSchoolCreate, DesiredSchoolUpdate, DesiredDepartmentCreate
from app.core.exceptions import NotFoundError, ConflictError, DatabaseError


# --- DesiredSchool CRUD --- #

async def create_desired_school(db: AsyncSession, *, user_id: UUID, obj_in: DesiredSchoolCreate) -> DesiredSchool:
    """指定されたユーザーIDと志望校情報で新しいDesiredSchoolを作成し、関連するDesiredDepartmentも作成する"""
    db_desired_school = DesiredSchool(
        user_id=user_id,
        university_id=obj_in.university_id,
        preference_order=obj_in.preference_order
    )
    db.add(db_desired_school)

    try:
        await db.flush()

        created_departments = []
        for dept_in in obj_in.desired_departments:
            db_dept = DesiredDepartment(
                desired_school_id=db_desired_school.id,
                department_id=dept_in.department_id,
                admission_method_id=dept_in.admission_method_id
            )
            created_departments.append(db_dept)
        
        if created_departments:
            db.add_all(created_departments)
        
        await db.commit()
        # Refresh は個々のオブジェクトに対して行うよりも、
        # 関連を含めて再取得する方が確実
        # await db.refresh(db_desired_school)
        # for dept in created_departments:
        #      await db.refresh(dept)
             
        # ★★★ 修正: 作成後に get_desired_school を呼び出して関連データをロード ★★★
        created_school_complete = await get_desired_school(db, desired_school_id=db_desired_school.id)
        if not created_school_complete:
             # 通常ここには到達しないはずだが念のため
             raise DatabaseError("作成した志望校データの再読み込みに失敗しました。")
        return created_school_complete
        # ★★★ 修正ここまで ★★★

    except IntegrityError as e:
        await db.rollback()
        # 制約違反の詳細に応じてエラーメッセージを調整
        if "uq_user_university_preference" in str(e.orig): # 例: ユニーク制約名
            raise ConflictError(f"ユーザーID {user_id} は既に大学ID {obj_in.university_id} を登録済みか、同じ志望順位 {obj_in.preference_order} が存在します。")
        elif "fk_" in str(e.orig): # 外部キー制約違反
             raise NotFoundError(f"関連データ（大学、学部、入試方式など）が見つかりません。詳細: {e.orig}")
        else:
             raise DatabaseError(f"志望校の作成中にデータベースエラーが発生しました: {e}")
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"志望校の作成中に予期せぬエラーが発生しました: {e}")

async def get_desired_school(db: AsyncSession, *, desired_school_id: UUID) -> Optional[DesiredSchool]:
    """指定されたIDのDesiredSchoolを関連するDesiredDepartmentと共に取得する"""
    result = await db.execute(
        select(DesiredSchool)
        .options(
            joinedload(DesiredSchool.university),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
        )
        .filter(DesiredSchool.id == desired_school_id)
    )
    return result.scalars().first()

async def get_desired_schools_by_user(db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100) -> List[DesiredSchool]:
    """指定されたユーザーIDのDesiredSchoolリストを関連するDesiredDepartmentと共に取得する"""
    result = await db.execute(
        select(DesiredSchool)
        .options(
            joinedload(DesiredSchool.university),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
        )
        .filter(DesiredSchool.user_id == user_id)
        .order_by(DesiredSchool.preference_order)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# ★★★ get_desired_schools_by_user_with_count 関数を追加 ★★★
# (desired_schools.py エンドポイントで使用されているため)
from sqlalchemy import func, select

async def get_desired_schools_by_user_with_count(db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100) -> Tuple[List[DesiredSchool], int]:
    """指定されたユーザーIDのDesiredSchoolリストと総数を取得する"""
    # Count query
    count_stmt = select(func.count()).select_from(DesiredSchool).filter(DesiredSchool.user_id == user_id)
    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar_one()

    # Data query
    stmt = (
        select(DesiredSchool)
        .options(
            joinedload(DesiredSchool.university),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
        )
        .filter(DesiredSchool.user_id == user_id)
        .order_by(DesiredSchool.preference_order)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    # Use unique() to avoid duplicates if joins cause them
    schools = result.scalars().unique().all()
    return schools, total_count

async def update_desired_school(db: AsyncSession, *, db_obj: DesiredSchool, obj_in: DesiredSchoolUpdate) -> DesiredSchool:
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
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        # ユニーク制約違反などのハンドリング
        raise ConflictError(f"更新により制約違反が発生しました。詳細: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"志望校の更新中にエラーが発生しました: {e}")

async def delete_desired_school(db: AsyncSession, *, desired_school_id: UUID) -> DesiredSchool:
    """指定されたIDのDesiredSchoolと関連するDesiredDepartmentを削除する"""
    db_obj = await get_desired_school(db, desired_school_id=desired_school_id)
    if not db_obj:
        raise NotFoundError(f"ID {desired_school_id} の志望校が見つかりません。")

    try:
        # 関連する DesiredDepartment を先に削除 (CASCADE設定がない場合)
        # for dept in db_obj.desired_departments:
        #     await db.delete(dept)
        # await db.flush() # DesiredDepartmentの削除を反映
        
        # DesiredSchool を削除
        await db.delete(db_obj)
        await db.commit()
        # 削除されたオブジェクトを返す（IDなどはまだアクセス可能）
        return db_obj
    except IntegrityError as e:
        await db.rollback()
        raise DatabaseError(f"志望校の削除中に他のデータとの整合性エラーが発生しました: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"志望校の削除中にエラーが発生しました: {e}")

# --- DesiredDepartment CRUD (必要に応じて追加) --- #
# 例: 特定の学部だけを追加・削除する関数など 