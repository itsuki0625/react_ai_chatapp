from sqlalchemy.orm import Session, joinedload
from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.models.document import Document, DocumentSubmission
from app.models.schedule import ScheduleEvent, EventCompletion
from app.models.university import University, Department
from app.models.admission import AdmissionMethod
from app.schemas.application import (
    ApplicationCreate, 
    ApplicationUpdate,
    DocumentCreate,
    ScheduleCreate,
    DocumentUpdate,
    ScheduleUpdate,
    ReorderApplications
)
from sqlalchemy import desc, func
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime, timedelta

def create_application(
    db: Session,
    application: ApplicationCreate,
    user_id: UUID
) -> DesiredSchool:
    """新しい志望校を作成"""
    # 優先順位が指定されていない場合、現在の最大値+1を設定
    if not application.priority:
        max_order = db.query(func.max(DesiredSchool.preference_order)).filter(
            DesiredSchool.user_id == user_id
        ).scalar() or 0
        application.priority = max_order + 1
    
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
    ).options(
        joinedload(DesiredSchool.university),
        joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
        joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
    ).first()

def get_applications(
    db: Session,
    user_id: UUID
) -> List[DesiredSchool]:
    """ユーザーの志望校一覧を取得"""
    return db.query(DesiredSchool).filter(
        DesiredSchool.user_id == user_id
    ).options(
        joinedload(DesiredSchool.university),
        joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
        joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
    ).order_by(DesiredSchool.preference_order).all()

def update_application(
    db: Session,
    school: DesiredSchool,
    application_update: ApplicationUpdate
) -> DesiredSchool:
    """志望校を更新"""
    # DesiredSchoolの更新
    if application_update.priority is not None:
        school.preference_order = application_update.priority
    
    if application_update.university_id is not None:
        school.university_id = application_update.university_id
    
    # DesiredDepartmentの更新
    if school.desired_departments and (application_update.department_id is not None or application_update.admission_method_id is not None):
        department = school.desired_departments[0]
        if application_update.department_id is not None:
            department.department_id = application_update.department_id
        if application_update.admission_method_id is not None:
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

def reorder_applications(
    db: Session,
    user_id: UUID,
    reorder_data: ReorderApplications
) -> List[DesiredSchool]:
    """志望校の優先順位を更新"""
    # 優先順位更新のバリデーション
    applications = get_applications(db, user_id)
    
    # 全ての志望校がreorder_dataに含まれていることを確認
    app_ids = [str(app.id) for app in applications]
    if set(app_ids) != set(reorder_data.application_order.keys()):
        raise HTTPException(status_code=400, detail="全ての志望校が含まれていません")
    
    # 優先順位を更新
    for app_id, priority in reorder_data.application_order.items():
        db.query(DesiredSchool).filter(
            DesiredSchool.id == app_id,
            DesiredSchool.user_id == user_id  # セキュリティのため、ユーザー所有のアプリケーションのみ更新
        ).update({"preference_order": priority})
    
    db.commit()
    
    # 更新された志望校一覧を返す
    return get_applications(db, user_id)

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

def update_document_by_id(
    db: Session,
    document_id: str,
    document_update: DocumentUpdate
) -> Document:
    """書類を更新"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="書類が見つかりません")

    for key, value in document_update.dict(exclude_unset=True).items():
        setattr(document, key, value)

    db.commit()
    db.refresh(document)
    return document

def delete_document_by_id(
    db: Session,
    document_id: str
) -> None:
    """書類を削除"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document:
        db.delete(document)
        db.commit()

def submit_document(
    db: Session,
    document_id: UUID,
    user_id: UUID
) -> DocumentSubmission:
    """書類を提出済みにする"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="書類が見つかりません")
    
    # 書類のステータスを更新
    document.status = "SUBMITTED"
    
    # 提出記録を作成
    submission = DocumentSubmission(
        document_id=document_id,
        submitted_at=datetime.utcnow(),
        submitted_by=user_id
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

# スケジュール関連のCRUD操作
def create_schedule(
    db: Session,
    schedule: ScheduleCreate,
    department_id: UUID
) -> ScheduleEvent:
    db_schedule = ScheduleEvent(
        desired_department_id=department_id,
        event_name=schedule.event_name,
        event_date=schedule.date,
        event_type=schedule.type
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
    ).order_by(ScheduleEvent.event_date).all()

def update_schedule_by_id(
    db: Session,
    schedule_id: str,
    schedule_update: ScheduleUpdate
) -> ScheduleEvent:
    """スケジュールを更新"""
    schedule = db.query(ScheduleEvent).filter(ScheduleEvent.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    for key, value in schedule_update.dict(exclude_unset=True).items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)
    return schedule

def delete_schedule_by_id(
    db: Session,
    schedule_id: str
) -> None:
    """スケジュールを削除"""
    schedule = db.query(ScheduleEvent).filter(ScheduleEvent.id == schedule_id).first()
    if schedule:
        db.delete(schedule)
        db.commit()

def complete_event(
    db: Session,
    event_id: UUID,
    user_id: UUID,
    completed: bool = True
) -> EventCompletion:
    """イベントを完了済みにする"""
    event = db.query(ScheduleEvent).filter(ScheduleEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 既存の完了記録を取得または新規作成
    completion = db.query(EventCompletion).filter(EventCompletion.event_id == event_id).first()
    if not completion:
        completion = EventCompletion(
            event_id=event_id,
            completed=completed,
            completed_by=user_id if completed else None,
            completed_at=datetime.utcnow() if completed else None
        )
        db.add(completion)
    else:
        completion.completed = completed
        completion.completed_by = user_id if completed else None
        completion.completed_at = datetime.utcnow() if completed else None
    
    db.commit()
    db.refresh(completion)
    return completion

# 締め切り情報の取得
def get_upcoming_deadlines(
    db: Session,
    user_id: UUID,
    days: int = 30
) -> List[Dict[str, Any]]:
    """近づく提出期限の一覧を取得する"""
    now = datetime.utcnow()
    deadline_date = now + timedelta(days=days)
    
    # 書類の提出期限取得
    documents = db.query(
        Document, DesiredDepartment, DesiredSchool, University, Department
    ).join(
        DesiredDepartment, DesiredDepartment.id == Document.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).join(
        University, University.id == DesiredSchool.university_id
    ).join(
        Department, Department.id == DesiredDepartment.department_id
    ).filter(
        DesiredSchool.user_id == user_id,
        Document.deadline.between(now, deadline_date),
        Document.status != "APPROVED"  # 承認済みの書類は除外
    ).order_by(
        Document.deadline
    ).all()
    
    # イベントの予定取得
    events = db.query(
        ScheduleEvent, DesiredDepartment, DesiredSchool, University, Department
    ).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).join(
        University, University.id == DesiredSchool.university_id
    ).join(
        Department, Department.id == DesiredDepartment.department_id
    ).outerjoin(
        EventCompletion, EventCompletion.event_id == ScheduleEvent.id
    ).filter(
        DesiredSchool.user_id == user_id,
        ScheduleEvent.event_date.between(now, deadline_date),
        (EventCompletion.completed == False) | (EventCompletion.id == None)  # 完了していないイベント
    ).order_by(
        ScheduleEvent.event_date
    ).all()
    
    # 結果を整形
    result = []
    
    for doc, dept, school, university, department in documents:
        result.append({
            "type": "document",
            "id": str(doc.id),
            "name": doc.name,
            "deadline": doc.deadline.isoformat(),
            "university_name": university.name,
            "department_name": department.name,
            "days_remaining": (doc.deadline - now).days,
            "status": doc.status
        })
    
    for event, dept, school, university, department in events:
        result.append({
            "type": "event",
            "id": str(event.id),
            "name": event.event_name,
            "deadline": event.event_date.isoformat(),
            "university_name": university.name,
            "department_name": department.name,
            "days_remaining": (event.event_date - now).days,
            "event_type": event.event_type
        })
    
    # 日付順にソート
    result.sort(key=lambda x: x["days_remaining"])
    
    return result

def get_application_statistics(
    db: Session,
    user_id: UUID
) -> Dict[str, Any]:
    """志望校関連の統計情報を取得する"""
    # 志望校数
    schools_count = db.query(func.count(DesiredSchool.id)).filter(
        DesiredSchool.user_id == user_id
    ).scalar()
    
    # 志望学部・学科数
    departments_count = db.query(func.count(DesiredDepartment.id)).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    ).scalar()
    
    # 書類数と状態別のカウント
    documents = db.query(Document).join(
        DesiredDepartment, DesiredDepartment.id == Document.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    ).all()
    
    documents_count = len(documents)
    document_statuses = {}
    for doc in documents:
        status = str(doc.status)
        if status in document_statuses:
            document_statuses[status] += 1
        else:
            document_statuses[status] = 1
    
    # イベント数と種類別のカウント
    events = db.query(ScheduleEvent).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    ).all()
    
    events_count = len(events)
    event_types = {}
    for event in events:
        event_type = str(event.event_type)
        if event_type in event_types:
            event_types[event_type] += 1
        else:
            event_types[event_type] = 1
    
    # 締め切りが近い書類/イベント数
    now = datetime.utcnow()
    deadline_date = now + timedelta(days=7)
    
    upcoming_documents = db.query(func.count(Document.id)).join(
        DesiredDepartment, DesiredDepartment.id == Document.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id,
        Document.deadline.between(now, deadline_date)
    ).scalar()
    
    upcoming_events = db.query(func.count(ScheduleEvent.id)).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).outerjoin(
        EventCompletion, EventCompletion.event_id == ScheduleEvent.id
    ).filter(
        DesiredSchool.user_id == user_id,
        ScheduleEvent.event_date.between(now, deadline_date),
        (EventCompletion.completed == False) | (EventCompletion.id == None)
    ).scalar()
    
    return {
        "schools_count": schools_count,
        "departments_count": departments_count,
        "documents_count": documents_count,
        "document_statuses": document_statuses,
        "events_count": events_count,
        "event_types": event_types,
        "upcoming_documents": upcoming_documents,
        "upcoming_events": upcoming_events,
        "total_upcoming_deadlines": upcoming_documents + upcoming_events
    }
