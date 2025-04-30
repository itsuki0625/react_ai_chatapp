from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.models.admission import AdmissionMethod # AdmissionMethodモデルをインポート

def get_admission_method(db: Session, *, admission_method_id: UUID) -> Optional[AdmissionMethod]:
    """指定されたIDの入試方式を取得する"""
    return db.query(AdmissionMethod).filter(AdmissionMethod.id == admission_method_id).first()

# 必要に応じて他のCRUD操作 (create, update, delete, get_multiなど) を追加 