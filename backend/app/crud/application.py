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
from sqlalchemy import desc, func, update as sql_update, delete as sql_delete
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_application(
    db: AsyncSession,
    application: ApplicationCreate,
    user_id: UUID
) -> DesiredSchool:
    """新しい志望校を作成 (非同期対応)"""
    # 優先順位が指定されていない場合、現在の最大値+1を設定
    if not application.priority:
        max_order_stmt = select(func.max(DesiredSchool.preference_order)).filter(
            DesiredSchool.user_id == user_id
        )
        max_order_result = await db.execute(max_order_stmt)
        max_order = max_order_result.scalar() or 0
        application.priority = max_order + 1
    
    # まずDesiredSchoolを作成
    db_school = DesiredSchool(
        user_id=user_id,
        university_id=application.university_id,
        preference_order=application.priority
    )
    db.add(db_school)
    await db.flush()

    # 次にDesiredDepartmentを作成
    db_department = DesiredDepartment(
        desired_school_id=db_school.id,
        department_id=application.department_id,
        admission_method_id=application.admission_method_id
    )
    db.add(db_department)
    await db.commit()
    await db.refresh(db_school)
    return db_school

async def get_application(
    db: AsyncSession,
    school_id: str
) -> Optional[DesiredSchool]:
    """特定の志望校を取得 (非同期対応)"""
    stmt = (
        select(DesiredSchool).filter(DesiredSchool.id == school_id)
        .options(
            joinedload(DesiredSchool.university),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_applications(
    db: AsyncSession,
    user_id: UUID
) -> List[DesiredSchool]:
    """ユーザーの志望校一覧を取得 (非同期対応)"""
    stmt = (
        select(DesiredSchool)
        .filter(DesiredSchool.user_id == user_id)
        .options(
            joinedload(DesiredSchool.university),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.department),
            joinedload(DesiredSchool.desired_departments).joinedload(DesiredDepartment.admission_method)
        )
        .order_by(DesiredSchool.preference_order)
    )
    result = await db.execute(stmt)
    return result.unique().scalars().all()

async def update_application(
    db: AsyncSession,
    school: DesiredSchool,
    application_update: ApplicationUpdate
) -> DesiredSchool:
    """志望校を更新 (非同期対応)"""
    # DesiredSchoolの更新
    update_data_school = {}
    if application_update.priority is not None:
        update_data_school['preference_order'] = application_update.priority
    if application_update.university_id is not None:
        update_data_school['university_id'] = application_update.university_id
    
    if update_data_school:
        for key, value in update_data_school.items():
            setattr(school, key, value)

    # DesiredDepartmentの更新
    update_data_dept = {}
    if application_update.department_id is not None:
        update_data_dept['department_id'] = application_update.department_id
    if application_update.admission_method_id is not None:
         update_data_dept['admission_method_id'] = application_update.admission_method_id

    if school.desired_departments and update_data_dept:
        # Assuming one DesiredDepartment per DesiredSchool based on previous logic
        department = school.desired_departments[0]
        for key, value in update_data_dept.items():
             setattr(department, key, value)

    await db.commit()
    await db.refresh(school)
    # Refresh related department if needed
    if school.desired_departments:
         await db.refresh(school.desired_departments[0])
    return school

async def delete_application(
    db: AsyncSession,
    school_id: str
) -> Optional[DesiredSchool]:
    """志望校を削除 (非同期対応)"""
    school = await get_application(db, school_id)
    if school:
        # Consider related objects (DesiredDepartment) if CASCADE is not set
        await db.delete(school)
        await db.commit()
        return school
    return None

async def reorder_applications(
    db: AsyncSession,
    user_id: UUID,
    reorder_data: ReorderApplications
) -> List[DesiredSchool]:
    """志望校の優先順位を更新 (非同期対応)"""
    # 優先順位更新のバリデーション
    applications = await get_applications(db, user_id)
    
    # 全ての志望校がreorder_dataに含まれていることを確認
    app_ids = [str(app.id) for app in applications]
    if set(app_ids) != set(reorder_data.application_order.keys()):
        raise HTTPException(status_code=400, detail="全ての志望校が含まれていません")
    
    # 優先順位を更新 (Execute updates)
    for app_id_str, priority in reorder_data.application_order.items():
        try:
             app_id = UUID(app_id_str)
             stmt = (
                 sql_update(DesiredSchool)
                 .where(DesiredSchool.id == app_id)
                 .where(DesiredSchool.user_id == user_id)
                 .values(preference_order=priority)
             )
             await db.execute(stmt)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid application ID format: {app_id_str}")
        except Exception as e:
             await db.rollback()
             raise HTTPException(status_code=500, detail=f"Error updating priority for {app_id_str}: {e}")

    await db.commit()
    
    # 更新された志望校一覧を返す
    return await get_applications(db, user_id)

# 書類関連のCRUD操作
async def create_document(
    db: AsyncSession,
    document: DocumentCreate,
    department_id: UUID
) -> Document:
    """書類を作成 (非同期対応)"""
    db_document = Document(
        desired_department_id=department_id,
        name=document.name,
        status=document.status,
        deadline=document.deadline
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document

async def get_application_documents(
    db: AsyncSession,
    department_id: UUID
) -> List[Document]:
    """特定の志望学部の書類一覧を取得 (非同期対応)"""
    stmt = select(Document).filter(Document.desired_department_id == department_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_document_by_id(
    db: AsyncSession,
    document_id: str,
    document_update: DocumentUpdate
) -> Optional[Document]:
    """書類を更新 (非同期対応)"""
    try:
        doc_uuid = UUID(document_id)
        stmt_get = select(Document).filter(Document.id == doc_uuid)
        result_get = await db.execute(stmt_get)
        document = result_get.scalars().first()
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid document ID format")

    if not document:
        raise HTTPException(status_code=404, detail="書類が見つかりません")

    update_data = document_update.dict(exclude_unset=True)
    if update_data:
         for key, value in update_data.items():
             setattr(document, key, value)
         await db.commit()
         await db.refresh(document)
    return document

async def delete_document_by_id(
    db: AsyncSession,
    document_id: str
) -> Optional[Document]:
    """書類を削除 (非同期対応)"""
    try:
        doc_uuid = UUID(document_id)
        stmt_get = select(Document).filter(Document.id == doc_uuid)
        result_get = await db.execute(stmt_get)
        document = result_get.scalars().first()
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid document ID format")

    if document:
        await db.delete(document)
        await db.commit()
        return document
    return None

async def submit_document(
    db: AsyncSession,
    document_id: UUID,
    user_id: UUID
) -> Optional[DocumentSubmission]:
    """書類を提出済みにする (非同期対応)"""
    stmt_get = select(Document).filter(Document.id == document_id)
    result_get = await db.execute(stmt_get)
    document = result_get.scalars().first()

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
    await db.commit()
    await db.refresh(submission)
    await db.refresh(document)
    return submission

# スケジュール関連のCRUD操作
async def create_schedule(
    db: AsyncSession,
    schedule: ScheduleCreate,
    department_id: UUID
) -> ScheduleEvent:
    """スケジュールイベントを作成 (非同期対応)"""
    db_schedule = ScheduleEvent(
        desired_department_id=department_id,
        event_name=schedule.event_name,
        event_date=schedule.date,
        event_type=schedule.type
    )
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule

async def get_application_schedules(
    db: AsyncSession,
    department_id: UUID
) -> List[ScheduleEvent]:
    """特定の志望学部のスケジュール一覧を取得 (非同期対応)"""
    stmt = select(ScheduleEvent).filter(
        ScheduleEvent.desired_department_id == department_id
    ).order_by(ScheduleEvent.event_date)
    result = await db.execute(stmt)
    return result.scalars().all()

async def update_schedule_by_id(
    db: AsyncSession,
    schedule_id: str,
    schedule_update: ScheduleUpdate
) -> Optional[ScheduleEvent]:
    """スケジュールを更新 (非同期対応)"""
    try:
        sched_uuid = UUID(schedule_id)
        stmt_get = select(ScheduleEvent).filter(ScheduleEvent.id == sched_uuid)
        result_get = await db.execute(stmt_get)
        schedule = result_get.scalars().first()
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid schedule ID format")

    if not schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    update_data = schedule_update.dict(exclude_unset=True)
    if update_data:
        if 'date' in update_data:
             update_data['event_date'] = update_data.pop('date')
        if 'type' in update_data:
             update_data['event_type'] = update_data.pop('type')

        for key, value in update_data.items():
            setattr(schedule, key, value)
        await db.commit()
        await db.refresh(schedule)
    return schedule

async def delete_schedule_by_id(
    db: AsyncSession,
    schedule_id: str
) -> Optional[ScheduleEvent]:
    """スケジュールを削除 (非同期対応)"""
    try:
        sched_uuid = UUID(schedule_id)
        stmt_get = select(ScheduleEvent).filter(ScheduleEvent.id == sched_uuid)
        result_get = await db.execute(stmt_get)
        schedule = result_get.scalars().first()
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid schedule ID format")

    if schedule:
        await db.delete(schedule)
        await db.commit()
        return schedule
    return None

async def complete_event(
    db: AsyncSession,
    event_id: UUID,
    user_id: UUID,
    completed: bool = True
) -> Optional[EventCompletion]:
    """イベントを完了済みにする (非同期対応)"""
    stmt_get_event = select(ScheduleEvent).filter(ScheduleEvent.id == event_id)
    result_get_event = await db.execute(stmt_get_event)
    event = result_get_event.scalars().first()

    if not event:
        raise HTTPException(status_code=404, detail="イベントが見つかりません")
    
    # 既存の完了記録を取得または新規作成
    stmt_get_completion = select(EventCompletion).filter(EventCompletion.event_id == event_id)
    result_get_completion = await db.execute(stmt_get_completion)
    completion = result_get_completion.scalars().first()

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
    
    await db.commit()
    await db.refresh(completion)
    return completion

# 締め切り情報の取得
async def get_upcoming_deadlines(
    db: AsyncSession,
    user_id: UUID,
    days: int = 30
) -> List[Dict[str, Any]]:
    """近づく提出期限の一覧を取得する (非同期対応)"""
    now = datetime.utcnow()
    deadline_date = now + timedelta(days=days)
    
    # 書類の提出期限取得
    doc_stmt = (
        select(Document, DesiredDepartment, DesiredSchool, University, Department)
        .join(DesiredDepartment, DesiredDepartment.id == Document.desired_department_id)
        .join(DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id)
        .join(University, University.id == DesiredSchool.university_id)
        .join(Department, Department.id == DesiredDepartment.department_id)
        .filter(
            DesiredSchool.user_id == user_id,
            Document.deadline.between(now, deadline_date),
            Document.status != "APPROVED"
        )
        .order_by(Document.deadline)
    )
    doc_result = await db.execute(doc_stmt)
    documents = doc_result.all()
    
    # イベントの予定取得
    event_stmt = (
         select(ScheduleEvent, DesiredDepartment, DesiredSchool, University, Department)
        .join(DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id)
        .join(DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id)
        .join(University, University.id == DesiredSchool.university_id)
        .join(Department, Department.id == DesiredDepartment.department_id)
        .outerjoin(EventCompletion, EventCompletion.event_id == ScheduleEvent.id)
        .filter(
            DesiredSchool.user_id == user_id,
            ScheduleEvent.event_date.between(now, deadline_date),
            (EventCompletion.completed == False) | (EventCompletion.id == None)
        )
        .order_by(ScheduleEvent.event_date)
    )
    event_result = await db.execute(event_stmt)
    events = event_result.all()
    
    # 結果を整形
    result_list = []
    
    for doc, dept, school, university, department in documents:
         result_list.append({
             "type": "document",
             "id": str(doc.id),
             "name": doc.name,
             "deadline": doc.deadline.isoformat(),
             "university_name": university.name,
             "department_name": department.name,
             "days_remaining": (doc.deadline.replace(tzinfo=None) - now).days,
             "status": doc.status
         })
    
    for event, dept, school, university, department in events:
         result_list.append({
             "type": "event",
             "id": str(event.id),
             "name": event.event_name,
             "deadline": event.event_date.isoformat(),
             "university_name": university.name,
             "department_name": department.name,
             "days_remaining": (event.event_date.replace(tzinfo=None) - now).days,
             "event_type": event.event_type
         })
    
    # 日付順にソート
    result_list.sort(key=lambda x: x["days_remaining"])
    
    return result_list

async def get_application_statistics(
    db: AsyncSession,
    user_id: UUID
) -> Dict[str, Any]:
    """志望校関連の統計情報を取得する (非同期対応)"""
    # 志望校数
    schools_count_stmt = select(func.count(DesiredSchool.id)).filter(
        DesiredSchool.user_id == user_id
    )
    schools_count_res = await db.execute(schools_count_stmt)
    schools_count = schools_count_res.scalar_one()

    # 志望学部・学科数
    departments_count_stmt = select(func.count(DesiredDepartment.id)).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    )
    departments_count_res = await db.execute(departments_count_stmt)
    departments_count = departments_count_res.scalar_one()

    # 書類数と状態別のカウント
    docs_stmt = select(Document).join(
        DesiredDepartment, DesiredDepartment.id == Document.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    )
    docs_res = await db.execute(docs_stmt)
    documents = docs_res.scalars().all()

    documents_count = len(documents)
    document_statuses = {}
    for doc in documents:
        status = str(doc.status)
        document_statuses[status] = document_statuses.get(status, 0) + 1

    # イベント数と種類別のカウント
    events_stmt = select(ScheduleEvent).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id
    )
    events_res = await db.execute(events_stmt)
    events = events_res.scalars().all()

    events_count = len(events)
    event_types = {}
    for event in events:
        event_type = str(event.event_type)
        event_types[event_type] = event_types.get(event_type, 0) + 1

    # 締め切りが近い書類/イベント数
    now = datetime.utcnow()
    deadline_date = now + timedelta(days=7)

    upcoming_docs_stmt = select(func.count(Document.id)).join(
        DesiredDepartment, DesiredDepartment.id == Document.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).filter(
        DesiredSchool.user_id == user_id,
        Document.deadline.between(now, deadline_date)
    )
    upcoming_docs_res = await db.execute(upcoming_docs_stmt)
    upcoming_documents = upcoming_docs_res.scalar_one()

    upcoming_events_stmt = select(func.count(ScheduleEvent.id)).join(
        DesiredDepartment, DesiredDepartment.id == ScheduleEvent.desired_department_id
    ).join(
        DesiredSchool, DesiredSchool.id == DesiredDepartment.desired_school_id
    ).outerjoin(
        EventCompletion, EventCompletion.event_id == ScheduleEvent.id
    ).filter(
        DesiredSchool.user_id == user_id,
        ScheduleEvent.event_date.between(now, deadline_date),
        (EventCompletion.completed == False) | (EventCompletion.id == None)
    )
    upcoming_events_res = await db.execute(upcoming_events_stmt)
    upcoming_events = upcoming_events_res.scalar_one()

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
