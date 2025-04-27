from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.document import Document
from app.models.schedule import ScheduleEvent
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationDetailResponse,
    DocumentCreate,
    DocumentResponse,
    ScheduleCreate,
    ScheduleResponse,
    DocumentUpdate,
    ScheduleUpdate,
    ReorderApplications,
)
from app.crud.application import (
    create_application,
    get_applications,
    get_application,
    update_application,
    delete_application,
    create_document,
    create_schedule,
    get_application_documents,
    get_application_schedules,
    update_document_by_id,
    update_schedule_by_id,
    delete_document_by_id,
    delete_schedule_by_id,
    reorder_applications,
)
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/", response_model=ApplicationResponse)
async def create_new_application(
    application: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新しい志望校を登録"""
    school = create_application(db=db, application=application, user_id=current_user.id)
    
    # レスポンスデータの作成
    return ApplicationResponse(
        id=school.id,
        user_id=school.user_id,
        university_id=school.university_id,
        department_id=school.desired_departments[0].department_id,
        admission_method_id=school.desired_departments[0].admission_method_id,
        priority=school.preference_order,
        created_at=school.created_at,
        updated_at=school.updated_at,
        university_name=school.university.name,
        department_name=school.desired_departments[0].department.name,
        admission_method_name=school.desired_departments[0].admission_method.name,
        notes=None
    )

@router.get("/", response_model=List[ApplicationDetailResponse])
async def get_user_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーの志望校一覧を取得"""
    schools = get_applications(db=db, user_id=current_user.id)
    result = []
    
    for school in schools:
        if not school.desired_departments:
            continue
            
        department_info = school.desired_departments[0] 
        documents = get_application_documents(db, department_info.id)
        schedules = get_application_schedules(db, department_info.id)
        
        app_response = ApplicationDetailResponse(
            id=school.id,
            user_id=school.user_id,
            university_id=school.university_id,
            department_id=department_info.department_id,
            admission_method_id=department_info.admission_method_id,
            priority=school.preference_order,
            created_at=school.created_at,
            updated_at=school.updated_at,
            university_name=school.university.name,
            department_name=department_info.department.name,
            admission_method_name=department_info.admission_method.name,
            notes=None,
            documents=[
                DocumentResponse(
                    id=doc.id,
                    name=doc.name,
                    status=doc.status,
                    deadline=doc.deadline,
                    notes=getattr(doc, 'notes', None),
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    desired_department_id=doc.desired_department_id
                ) for doc in documents
            ],
            schedules=[
                ScheduleResponse(
                    id=schedule.id,
                    event_name=schedule.event_name,
                    date=schedule.event_date,
                    type=schedule.event_type,
                    location=getattr(schedule, 'location', None),
                    description=getattr(schedule, 'description', None),
                    created_at=schedule.created_at,
                    updated_at=schedule.updated_at,
                    desired_department_id=schedule.desired_department_id
                ) for schedule in schedules
            ],
            department_details=[{
                "id": department_info.id,
                "department_id": department_info.department_id,
                "department_name": department_info.department.name,
                "faculty_name": "不明"
            }]
        )
        result.append(app_response)
    
    return result

@router.put("/reorder")
async def reorder_user_applications(
    reorder_data: ReorderApplications,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    志望校の優先順位を更新する
    """
    try:
        # reorder_applicationsのCRUD関数を使用して一括更新
        updated_schools = reorder_applications(
            db=db, 
            user_id=current_user.id, 
            reorder_data=reorder_data
        )
        
        # レスポンスを整形
        result = []
        for school in updated_schools:
            if not school.desired_departments:
                continue
                
            department = school.desired_departments[0]
            
            app_response = {
                "id": school.id,
                "user_id": school.user_id,
                "university_id": school.university_id,
                "department_id": department.department_id,
                "admission_method_id": department.admission_method_id,
                "priority": school.preference_order,
                "created_at": school.created_at,
                "updated_at": school.updated_at,
                "university_name": school.university.name,
                "department_name": department.department.name,
                "admission_method_name": department.admission_method.name
            }
            result.append(app_response)
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"優先順位の更新中にエラーが発生しました: {str(e)}"
        )

@router.get("/statistics")
async def get_application_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    志望校関連の統計情報を取得
    """
    try:
        # ユーザーの志望校を取得
        schools = get_applications(db=db, user_id=current_user.id)
        
        if not schools:
            return {
                "total_applications": 0,
                "admission_methods": [],
                "document_completion": 0,
                "upcoming_deadlines": 0,
                "universities_by_region": [],
                "departments_by_field": []
            }
        
        # 基本統計
        total_applications = len(schools)
        
        # 入試方式別の志望校数
        admission_methods = {}
        
        # 地域別の大学数
        universities_by_region = {}
        
        # 分野別の学部数
        departments_by_field = {}
        
        # 書類の完成度
        total_documents = 0
        completed_documents = 0
        
        # 直近の締め切り
        upcoming_deadlines = 0
        now = datetime.now()
        
        for school in schools:
            # 学部情報がない場合はスキップ
            if not school.desired_departments:
                continue
                
            department = school.desired_departments[0]
            
            # 入試方式
            method_name = department.admission_method.name
            if method_name in admission_methods:
                admission_methods[method_name] += 1
            else:
                admission_methods[method_name] = 1
            
            # 地域（大学の所在地属性を仮定）
            region = getattr(school.university, 'region', '不明')
            if region in universities_by_region:
                universities_by_region[region] += 1
            else:
                universities_by_region[region] = 1
            
            # 分野（学部の分野属性を仮定）
            field = getattr(department.department, 'field', '不明')
            if field in departments_by_field:
                departments_by_field[field] += 1
            else:
                departments_by_field[field] = 1
            
            # 書類と締め切り
            documents = get_application_documents(db, department.id)
            schedules = get_application_schedules(db, department.id)
            
            # 書類の完成度
            for doc in documents:
                total_documents += 1
                if doc.status == "完了":
                    completed_documents += 1
            
            # 直近の締め切り
            for schedule in schedules:
                if hasattr(schedule, 'due_date') and schedule.due_date:
                    due_date = schedule.due_date
                    # 30日以内の締め切りをカウント
                    if due_date > now and (due_date - now).days <= 30:
                        upcoming_deadlines += 1
        
        # 書類完成率の計算
        document_completion = 0
        if total_documents > 0:
            document_completion = round((completed_documents / total_documents) * 100)
        
        # 入試方式データの整形
        admission_methods_list = [
            {"name": name, "count": count}
            for name, count in admission_methods.items()
        ]
        
        # 地域データの整形
        region_list = [
            {"name": name, "count": count}
            for name, count in universities_by_region.items()
        ]
        
        # 分野データの整形
        field_list = [
            {"name": name, "count": count}
            for name, count in departments_by_field.items()
        ]
        
        return {
            "total_applications": total_applications,
            "admission_methods": admission_methods_list,
            "document_completion": document_completion,
            "upcoming_deadlines": upcoming_deadlines,
            "universities_by_region": region_list,
            "departments_by_field": field_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"統計情報の取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/deadlines")
async def get_upcoming_deadlines(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    近づく提出期限の一覧を取得
    デフォルトでは30日以内の期限を返す
    """
    try:
        # ユーザーの志望校を取得
        schools = get_applications(db=db, user_id=current_user.id)
        
        deadlines = []
        now = datetime.now()
        max_date = now + timedelta(days=days)
        
        for school in schools:
            # 学部情報がない場合はスキップ
            if not school.desired_departments:
                continue
                
            for department in school.desired_departments:
                # 書類の締め切り
                documents = get_application_documents(db, department.id)
                for doc in documents:
                    if hasattr(doc, 'due_date') and doc.due_date:
                        if now <= doc.due_date <= max_date:
                            deadlines.append({
                                "id": str(doc.id),
                                "type": "document",
                                "title": doc.title,
                                "description": doc.description,
                                "due_date": doc.due_date.isoformat(),
                                "status": doc.status,
                                "university_name": school.university.name,
                                "department_name": department.department.name,
                                "days_left": (doc.due_date - now).days
                            })
                
                # スケジュールの締め切り
                schedules = get_application_schedules(db, department.id)
                for schedule in schedules:
                    if hasattr(schedule, 'due_date') and schedule.due_date:
                        if now <= schedule.due_date <= max_date:
                            deadlines.append({
                                "id": str(schedule.id),
                                "type": "schedule",
                                "title": schedule.title,
                                "description": schedule.description,
                                "due_date": schedule.due_date.isoformat(),
                                "status": getattr(schedule, 'status', '予定'),
                                "university_name": school.university.name,
                                "department_name": department.department.name,
                                "days_left": (schedule.due_date - now).days
                            })
        
        # 締め切り日順にソート
        deadlines.sort(key=lambda x: x["due_date"])
        
        return deadlines
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"締め切り情報の取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_single_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """特定の志望校情報を取得"""
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")
    
    if not school.desired_departments:
        raise HTTPException(status_code=404, detail="学部情報が見つかりません")
        
    department_info = school.desired_departments[0]
    documents = get_application_documents(db, department_info.id)
    schedules = get_application_schedules(db, department_info.id)
    
    return ApplicationDetailResponse(
        id=school.id,
        user_id=school.user_id,
        university_id=school.university_id,
        department_id=department_info.department_id,
        admission_method_id=department_info.admission_method_id,
        priority=school.preference_order,
        created_at=school.created_at,
        updated_at=school.updated_at,
        university_name=school.university.name,
        department_name=department_info.department.name,
        admission_method_name=department_info.admission_method.name,
        notes=None,
        documents=[
            DocumentResponse(
                id=doc.id,
                name=doc.name,
                status=doc.status,
                deadline=doc.deadline,
                notes=getattr(doc, 'notes', None),
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                desired_department_id=doc.desired_department_id
            ) for doc in documents
        ],
        schedules=[
            ScheduleResponse(
                id=schedule.id,
                event_name=schedule.event_name,
                date=schedule.event_date,
                type=schedule.event_type,
                location=getattr(schedule, 'location', None),
                description=getattr(schedule, 'description', None),
                created_at=schedule.created_at,
                updated_at=schedule.updated_at,
                desired_department_id=schedule.desired_department_id
            ) for schedule in schedules
        ],
        department_details=[{
            "id": department_info.id,
            "department_id": department_info.department_id,
            "department_name": department_info.department.name,
            "faculty_name": "不明"
        }]
    )

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_existing_application(
    application_id: str,
    application_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """志望校情報を更新"""
    existing_school = get_application(db=db, school_id=application_id)
    if not existing_school or existing_school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")
    
    updated_school = update_application(
        db=db, 
        school=existing_school, 
        application_update=application_update
    )
    
    department = updated_school.desired_departments[0]
    return ApplicationResponse(
        id=updated_school.id,
        user_id=updated_school.user_id,
        university_id=updated_school.university_id,
        department_id=department.department_id,
        admission_method_id=department.admission_method_id,
        priority=updated_school.preference_order,
        created_at=updated_school.created_at,
        updated_at=updated_school.updated_at,
        university_name=updated_school.university.name,
        department_name=department.department.name,
        admission_method_name=department.admission_method.name,
        notes=None
    )

@router.delete("/{application_id}")
async def delete_existing_application(
    application_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """志望校を削除"""
    existing_school = get_application(db=db, school_id=application_id)
    if not existing_school or existing_school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")
    delete_application(db=db, school_id=application_id)
    return {"message": "志望校が削除されました"}

@router.post("/{application_id}/documents", response_model=DocumentResponse)
async def add_document(
    application_id: str,
    document: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """書類を追加"""
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")
    
    if not school.desired_departments:
        raise HTTPException(status_code=404, detail="学部情報が見つかりません")
        
    # documentオブジェクトのdesired_department_idに設定
    document.desired_department_id = school.desired_departments[0].id
    
    return create_document(
        db=db, 
        document=document, 
        department_id=school.desired_departments[0].id
    )

@router.post("/{application_id}/schedules", response_model=ScheduleResponse)
async def add_schedule(
    application_id: str,
    schedule: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """スケジュールを追加"""
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")
    
    if not school.desired_departments:
        raise HTTPException(status_code=404, detail="学部情報が見つかりません")
        
    # scheduleオブジェクトのdesired_department_idに設定
    schedule.desired_department_id = school.desired_departments[0].id
    
    return create_schedule(
        db=db, 
        schedule=schedule, 
        department_id=school.desired_departments[0].id
    )

@router.put("/{application_id}/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    application_id: str,
    document_id: str,
    document: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """書類を更新"""
    # 志望校の存在確認と権限チェック
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")

    # 書類の存在確認
    existing_document = db.query(Document).filter(
        Document.id == document_id,
        Document.desired_department_id == school.desired_departments[0].id
    ).first()
    
    if not existing_document:
        raise HTTPException(status_code=404, detail="書類が見つかりません")

    # 書類の更新
    return update_document_by_id(
        db=db,
        document_id=document_id,
        document_update=document
    )

@router.put("/{application_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    application_id: str,
    schedule_id: str,
    schedule: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """スケジュールを更新"""
    # 志望校の存在確認と権限チェック
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")

    # スケジュールの存在確認
    existing_schedule = db.query(ScheduleEvent).filter(
        ScheduleEvent.id == schedule_id,
        ScheduleEvent.desired_department_id == school.desired_departments[0].id
    ).first()
    
    if not existing_schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    # スケジュールの更新
    return update_schedule_by_id(
        db=db,
        schedule_id=schedule_id,
        schedule_update=schedule
    )

@router.delete("/{application_id}/documents/{document_id}")
async def delete_document(
    application_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """書類を削除"""
    # 志望校の存在確認と権限チェック
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")

    # 書類の存在確認
    existing_document = db.query(Document).filter(
        Document.id == document_id,
        Document.desired_department_id == school.desired_departments[0].id
    ).first()
    
    if not existing_document:
        raise HTTPException(status_code=404, detail="書類が見つかりません")

    # 書類の削除
    delete_document_by_id(db=db, document_id=document_id)
    return {"message": "書類が削除されました"}

@router.delete("/{application_id}/schedules/{schedule_id}")
async def delete_schedule(
    application_id: str,
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """スケジュールを削除"""
    # 志望校の存在確認と権限チェック
    school = get_application(db=db, school_id=application_id)
    if not school or school.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="志望校が見つかりません")

    # スケジュールの存在確認
    existing_schedule = db.query(ScheduleEvent).filter(
        ScheduleEvent.id == schedule_id,
        ScheduleEvent.desired_department_id == school.desired_departments[0].id
    ).first()
    
    if not existing_schedule:
        raise HTTPException(status_code=404, detail="スケジュールが見つかりません")

    # スケジュールの削除
    delete_schedule_by_id(db=db, schedule_id=schedule_id)
    return {"message": "スケジュールが削除されました"}
