from sqlalchemy.orm import Session, joinedload
from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.models.document import Document
from app.models.schedule import ScheduleEvent
from app.schemas.application import (
    ApplicationCreate, 
    ApplicationUpdate,
    DocumentCreate,
    ScheduleCreate
)
from uuid import UUID
from typing import List, Optional

def create_application(
    db: Session,
    application: ApplicationCreate,
    user_id: UUID
) -> DesiredSchool:
    """新しい志望校を作成"""
    # まずDesiredSchoolを作成
    db_school = DesiredSchool(
        user_id=user_id,
        university_id=application.university_id,
        preference_order=application.priority
    )
    db.add(db_school)
    db.flush()

    # 次にDesiredDepartmentを作成
    db_department = DesiredDepartment(
        desired_school_id=db_school.id,
        department_id=application.department_id,
        admission_method_id=application.admission_method_id
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_school)
    return db_school

def get_application(
    db: Session,
    school_id: str
) -> Optional[DesiredSchool]:
    """特定の志望校を取得"""
    return db.query(DesiredSchool).filter(
        DesiredSchool.id == school_id
    ).first()

def get_applications(
    db: Session,
    user_id: UUID
) -> List[DesiredSchool]:
    """ユーザーの志望校一覧を取得"""
    return db.query(DesiredSchool).filter(
        DesiredSchool.user_id == user_id
    ).order_by(DesiredSchool.preference_order).all()

def update_application(
    db: Session,
    school: DesiredSchool,
    application_update: ApplicationUpdate
) -> DesiredSchool:
    """志望校を更新"""
    # DesiredSchoolの更新
    school.preference_order = application_update.priority
    
    # DesiredDepartmentの更新
    if school.desired_departments:
        department = school.desired_departments[0]
        department.department_id = application_update.department_id
        department.admission_method_id = application_update.admission_method_id
    
    db.commit()
    db.refresh(school)
    return school

def delete_application(
    db: Session,
    school_id: str
) -> None:
    """志望校を削除"""
    school = db.query(DesiredSchool).filter(DesiredSchool.id == school_id).first()
    if school:
        db.delete(school)
        db.commit()

# 書類関連のCRUD操作
def create_document(
    db: Session,
    document: DocumentCreate,
    department_id: UUID
) -> Document:
    db_document = Document(
        desired_department_id=department_id,
        name=document.name,
        status=document.status,
        deadline=document.deadline
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_application_documents(
    db: Session,
    department_id: UUID
) -> List[Document]:
    return db.query(Document).filter(
        Document.desired_department_id == department_id
    ).all()

# スケジュール関連のCRUD操作
def create_schedule(
    db: Session,
    schedule: ScheduleCreate,
    department_id: UUID
) -> ScheduleEvent:
    db_schedule = ScheduleEvent(
        desired_department_id=department_id,
        event_name=schedule.event_name,
        date=schedule.date,
        type=schedule.event_type
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def get_application_schedules(
    db: Session,
    department_id: UUID
) -> List[ScheduleEvent]:
    return db.query(ScheduleEvent).filter(
        ScheduleEvent.desired_department_id == department_id
    ).all()
