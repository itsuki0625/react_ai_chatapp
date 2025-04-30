from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.models.university import Department # Departmentモデルをインポート

def get_department(db: Session, *, department_id: UUID) -> Optional[Department]:
    """指定されたIDの学部を取得する"""
    return db.query(Department).filter(Department.id == department_id).first()

# 必要に応じて他のCRUD操作 (create, update, delete, get_multiなど) を追加 