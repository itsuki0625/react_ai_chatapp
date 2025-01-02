from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate
from uuid import UUID

def create_content(db: Session, content: ContentCreate) -> Content:
    db_content = Content(**content.dict())
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
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
        update_data = content_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_content, key, value)
        db.commit()
        db.refresh(db_content)
    return db_content

def delete_content(db: Session, content_id: UUID) -> bool:
    db_content = get_content(db, content_id)
    if db_content:
        db.delete(db_content)
        db.commit()
        return True
    return False 