from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationDetailResponse,
    DocumentCreate,
    DocumentResponse,
    ScheduleCreate,
    ScheduleResponse,
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
)

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
            
        department = school.desired_departments[0]
        documents = get_application_documents(db, department.id)
        schedules = get_application_schedules(db, department.id)
        
        app_response = ApplicationDetailResponse(
            id=school.id,
            user_id=school.user_id,
            university_id=school.university_id,
            department_id=department.department_id,
            admission_method_id=department.admission_method_id,
            priority=school.preference_order,
            created_at=school.created_at,
            updated_at=school.updated_at,
            university_name=school.university.name,
            department_name=department.department.name,
            admission_method_name=department.admission_method.name,
            notes=None,
            documents=[DocumentResponse(**doc.__dict__) for doc in documents],
            schedules=[ScheduleResponse(**schedule.__dict__) for schedule in schedules],
            desired_departments=[{
                "id": department.id,
                "department_id": department.department_id,
                "department_name": department.department.name
            }]
        )
        result.append(app_response)
    
    return result

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
        
    department = school.desired_departments[0]
    documents = get_application_documents(db, department.id)
    schedules = get_application_schedules(db, department.id)
    
    return ApplicationDetailResponse(
        id=school.id,
        user_id=school.user_id,
        university_id=school.university_id,
        department_id=department.department_id,
        admission_method_id=department.admission_method_id,
        priority=school.preference_order,
        created_at=school.created_at,
        updated_at=school.updated_at,
        university_name=school.university.name,
        department_name=department.department.name,
        admission_method_name=department.admission_method.name,
        notes=None,
        documents=[DocumentResponse(**doc.__dict__) for doc in documents],
        schedules=[ScheduleResponse(**schedule.__dict__) for schedule in schedules]
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
        
    return create_schedule(
        db=db, 
        schedule=schedule, 
        department_id=school.desired_departments[0].id
    )
