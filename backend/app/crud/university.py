from sqlalchemy.orm import Session, joinedload
from app.models.university import University, UniversityDetails, Department, DepartmentDetails
from app.schemas.university import (
    UniversityCreate, UniversityUpdate, DepartmentCreate, DepartmentUpdate,
)
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid

from sqlalchemy import select # SQLAlchemy 2.0 スタイル
from sqlalchemy.ext.asyncio import AsyncSession # AsyncSession をインポート
from sqlalchemy.orm import selectinload # selectinload をインポート

# 大学のCRUD操作
async def create_university(db: AsyncSession, university: UniversityCreate) -> University:
    """新しい大学を作成する"""
    university_id = uuid.uuid4()
    db_university = University(
        id=university_id,
        name=university.name,
        university_code=university.university_code,
        is_active=university.is_active
    )
    db.add(db_university)
    
    # 大学詳細レコードがあれば作成
    if university.details:
        details_id = uuid.uuid4()
        db_details = UniversityDetails(
            id=details_id,
            university_id=university_id,
            address=university.details.address,
            prefecture=university.details.prefecture,
            city=university.details.city,
            zip_code=university.details.zip_code,
            president_name=university.details.president_name,
            website_url=university.details.website_url
        )
        db.add(db_details)
    
    await db.commit()
    await db.refresh(db_university)
    return db_university

async def get_university(db: AsyncSession, university_id: UUID) -> Optional[University]:
    """特定の大学を取得する"""
    result = await db.execute(
        select(University)
        .options(joinedload(University.details))
        .filter(University.id == university_id)
    )
    return result.scalars().first()

async def get_university_by_code(db: AsyncSession, university_code: str) -> Optional[University]:
    """大学コードで大学を取得する"""
    result = await db.execute(
        select(University)
        .options(joinedload(University.details))
        .filter(University.university_code == university_code)
    )
    return result.scalars().first()

async def get_universities(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[University]:
    """大学一覧を取得する (Department.details も Eager Loading)"""
    result = await db.execute(
        select(University)
        .options(
            joinedload(University.details),
            selectinload(University.departments).joinedload(Department.details)
        )
        .offset(skip)
        .limit(limit)
        .order_by(University.name) # Optional: Add ordering
    )
    # Use unique() to handle potential duplicates if joins cause them
    return result.scalars().unique().all()

async def search_universities(db: AsyncSession, query: str, limit: int = 20) -> List[University]:
    """大学を検索する (Department.details も Eager Loading)"""
    search_pattern = f"%{query}%"
    result = await db.execute(
        select(University)
        .options(
             joinedload(University.details),
             selectinload(University.departments).joinedload(Department.details)
         )
        .filter(University.name.ilike(search_pattern))
        .limit(limit)
        .order_by(University.name) # Optional: Add ordering
    )
    return result.scalars().unique().all()

async def update_university(db: AsyncSession, university_id: UUID, university_data: UniversityUpdate) -> Optional[University]:
    """大学情報を更新する"""
    result = await db.execute(
        select(University).options(joinedload(University.details)).filter(University.id == university_id)
    )
    db_university = result.scalars().first()

    if not db_university:
        return None
    
    update_data = university_data.model_dump(exclude_unset=True)

    # Update university fields
    if "name" in update_data:
        db_university.name = update_data["name"]
    if "university_code" in update_data:
        db_university.university_code = update_data["university_code"]
    if "is_active" in update_data:
        db_university.is_active = update_data["is_active"]
    
    # Update details if provided
    if "details" in update_data and update_data["details"] is not None:
        details_update_data = update_data["details"]
        # Fetch existing details or create new one
        # Note: We already loaded details, so we might be able to use db_university.details
        db_details = db_university.details
        if not db_details:
             db_details = UniversityDetails(id=uuid.uuid4(), university_id=university_id)
             db.add(db_details)
             db_university.details = db_details # Associate if newly created

        # Apply updates to details
        if "address" in details_update_data:
            db_details.address = details_update_data["address"]
        if "prefecture" in details_update_data:
            db_details.prefecture = details_update_data["prefecture"]
        if "city" in details_update_data:
            db_details.city = details_update_data["city"]
        if "zip_code" in details_update_data:
            db_details.zip_code = details_update_data["zip_code"]
        if "president_name" in details_update_data:
            db_details.president_name = details_update_data["president_name"]
        if "website_url" in details_update_data:
            db_details.website_url = details_update_data["website_url"]
    
    db.add(db_university) # Add university again to ensure it's marked dirty if needed
    await db.commit()
    await db.refresh(db_university)
    # Refresh the relationship explicitly if needed after commit
    # await db.refresh(db_university, attribute_names=['details', 'departments'])
    return db_university

async def delete_university(db: AsyncSession, university_id: UUID) -> bool:
    """大学を削除する"""
    result = await db.execute(select(University).filter(University.id == university_id))
    db_university = result.scalars().first()
    if not db_university:
        return False
    
    # Consider handling related entities (departments, etc.) before deleting
    await db.delete(db_university)
    await db.commit()
    return True

# 学部・学科のCRUD操作
async def create_department(db: AsyncSession, department: DepartmentCreate) -> Department:
    """新しい学部・学科を作成する"""
    # Check university existence
    univ_result = await db.execute(select(University).filter(University.id == department.university_id))
    db_university = univ_result.scalars().first()
    if not db_university:
        raise ValueError(f"University with ID {department.university_id} not found")
    
    department_id = uuid.uuid4()
    db_department = Department(
        id=department_id,
        university_id=department.university_id,
        name=department.name,
        department_code=department.department_code,
        is_active=department.is_active
    )
    db.add(db_department)
    
    # 学部詳細レコードがあれば作成
    if department.details:
        details_id = uuid.uuid4()
        db_details = DepartmentDetails(
            id=details_id,
            department_id=department_id,
            description=department.details.description
        )
        db.add(db_details)
    
    await db.commit()
    await db.refresh(db_department)
    return db_department

async def get_department(db: AsyncSession, department_id: UUID) -> Optional[Department]:
    """特定の学部・学科を取得する"""
    result = await db.execute(
        select(Department)
        .options(
            joinedload(Department.details),
            joinedload(Department.university).joinedload(University.details) # Eager load university and its details too
        )
        .filter(Department.id == department_id)
    )
    return result.scalars().first()

async def get_university_departments(db: AsyncSession, university_id: UUID) -> List[Department]:
    """特定の大学の学部・学科一覧を取得する"""
    result = await db.execute(
        select(Department)
        .options(
             joinedload(Department.details)
             # No need to load university again if only departments are needed
         )
        .filter(Department.university_id == university_id)
        .order_by(Department.name) # Optional: Add ordering
    )
    return result.scalars().all()

async def update_department(db: AsyncSession, department_id: UUID, department_data: DepartmentUpdate) -> Optional[Department]:
    """学部・学科情報を更新する"""
    result = await db.execute(
        select(Department).options(joinedload(Department.details)).filter(Department.id == department_id)
    )
    db_department = result.scalars().first()
    if not db_department:
        return None
    
    update_data = department_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        db_department.name = update_data["name"]
    if "department_code" in update_data:
        db_department.department_code = update_data["department_code"]
    if "is_active" in update_data:
        db_department.is_active = update_data["is_active"]

    if "details" in update_data and update_data["details"] is not None:
        details_update_data = update_data["details"]
        # Fetch or create details
        db_details = db_department.details # Use already loaded details if available
        if not db_details:
            db_details = DepartmentDetails(id=uuid.uuid4(), department_id=department_id)
            db.add(db_details)
            db_department.details = db_details
        if "description" in details_update_data:
            db_details.description = details_update_data["description"]

    db.add(db_department)
    await db.commit()
    await db.refresh(db_department)
    # await db.refresh(db_department, attribute_names=['details'])
    return db_department

async def delete_department(db: AsyncSession, department_id: UUID) -> bool:
    """学部・学科を削除する"""
    result = await db.execute(select(Department).filter(Department.id == department_id))
    db_department = result.scalars().first()
    if not db_department:
        return False
    
    await db.delete(db_department)
    await db.commit()
    return True

async def get_recommended_universities(db: AsyncSession, user_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
    """ユーザーの特性に基づいた推奨大学一覧を取得する"""
    # 実際の実装では、ユーザーのプロフィール、興味、志望校などに基づいてレコメンデーションをする
    # ここではシンプルな例を示す
    
    # ランダムに大学を取得
    from sqlalchemy.sql.expression import func
    universities = await db.execute(
        select(University)
        .order_by(func.random())
        .limit(limit)
    )
    
    result = []
    for university in universities.scalars().all():
        result.append({
            "id": str(university.id),
            "name": university.name,
            "match_score": round(50 + 50 * university.id.int % 100 / 100, 2),  # ダミースコア
            "reasons": [
                "あなたの興味と一致する学部があります",
                "あなたの学力レベルに適しています",
                "進路希望に合致する専攻があります"
            ]
        })
    
    return result 