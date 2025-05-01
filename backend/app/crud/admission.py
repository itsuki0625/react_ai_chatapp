from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from app.models.admission import AdmissionMethod
from app.schemas.admission import AdmissionMethodCreate, AdmissionMethodUpdate # スキーマも必要に応じて作成/インポート

async def get_admission_method(db: AsyncSession, method_id: UUID) -> Optional[AdmissionMethod]:
    """特定の入試方式を取得する"""
    result = await db.execute(
        select(AdmissionMethod).filter(AdmissionMethod.id == method_id)
    )
    return result.scalars().first()

async def get_admission_method_by_name(db: AsyncSession, name: str) -> Optional[AdmissionMethod]:
    """名前で入試方式を取得する"""
    result = await db.execute(
        select(AdmissionMethod).filter(AdmissionMethod.name == name)
    )
    return result.scalars().first()

async def get_all_admission_methods(db: AsyncSession, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[AdmissionMethod]:
    """入試方式一覧を取得する"""
    stmt = select(AdmissionMethod)
    if active_only:
        stmt = stmt.filter(AdmissionMethod.is_active == True)
    stmt = stmt.offset(skip).limit(limit).order_by(AdmissionMethod.name)
    result = await db.execute(stmt)
    return result.scalars().all()

# --- 必要に応じて Create, Update, Delete 関数も追加 ---

# async def create_admission_method(db: AsyncSession, method_in: AdmissionMethodCreate) -> AdmissionMethod:
#     # 実装...

# async def update_admission_method(db: AsyncSession, method_id: UUID, method_in: AdmissionMethodUpdate) -> Optional[AdmissionMethod]:
#     # 実装...

# async def delete_admission_method(db: AsyncSession, method_id: UUID) -> bool:
#     # 実装... 