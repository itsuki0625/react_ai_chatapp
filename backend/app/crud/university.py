from sqlalchemy.orm import Session, joinedload
from app.models.university import University, UniversityDetails, Department, DepartmentDetails
from app.models.university import AdmissionMethod, AdmissionMethodDetails
from app.schemas.university import (
    UniversityCreate, UniversityUpdate, DepartmentCreate, DepartmentUpdate,
    AdmissionMethodCreate, AdmissionMethodUpdate
)
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid

# 大学のCRUD操作
def create_university(db: Session, university: UniversityCreate) -> University:
    """新しい大学を作成する"""
    # 大学レコードを作成
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
    
    db.commit()
    db.refresh(db_university)
    return db_university

def get_university(db: Session, university_id: UUID) -> Optional[University]:
    """特定の大学を取得する"""
    return db.query(University).filter(University.id == university_id).options(
        joinedload(University.details)
    ).first()

def get_university_by_code(db: Session, university_code: str) -> Optional[University]:
    """大学コードで大学を取得する"""
    return db.query(University).filter(University.university_code == university_code).options(
        joinedload(University.details)
    ).first()

def get_universities(db: Session, skip: int = 0, limit: int = 100) -> List[University]:
    """大学一覧を取得する"""
    return db.query(University).offset(skip).limit(limit).options(
        joinedload(University.details)
    ).all()

def search_universities(db: Session, query: str, limit: int = 20) -> List[University]:
    """大学を検索する"""
    search_pattern = f"%{query}%"
    return db.query(University).filter(
        University.name.ilike(search_pattern)
    ).options(
        joinedload(University.details)
    ).limit(limit).all()

def update_university(db: Session, university_id: UUID, university_data: UniversityUpdate) -> Optional[University]:
    """大学情報を更新する"""
    db_university = db.query(University).filter(University.id == university_id).first()
    if not db_university:
        return None
    
    # 基本情報を更新
    if university_data.name is not None:
        db_university.name = university_data.name
    if university_data.university_code is not None:
        db_university.university_code = university_data.university_code
    if university_data.is_active is not None:
        db_university.is_active = university_data.is_active
    
    # 詳細情報を更新（存在する場合）
    if university_data.details:
        db_details = db.query(UniversityDetails).filter(
            UniversityDetails.university_id == university_id
        ).first()
        
        # 詳細がない場合は作成
        if not db_details:
            db_details = UniversityDetails(
                id=uuid.uuid4(),
                university_id=university_id
            )
            db.add(db_details)
        
        # 詳細を更新
        if university_data.details.address is not None:
            db_details.address = university_data.details.address
        if university_data.details.prefecture is not None:
            db_details.prefecture = university_data.details.prefecture
        if university_data.details.city is not None:
            db_details.city = university_data.details.city
        if university_data.details.zip_code is not None:
            db_details.zip_code = university_data.details.zip_code
        if university_data.details.president_name is not None:
            db_details.president_name = university_data.details.president_name
        if university_data.details.website_url is not None:
            db_details.website_url = university_data.details.website_url
    
    db.commit()
    db.refresh(db_university)
    return db_university

def delete_university(db: Session, university_id: UUID) -> bool:
    """大学を削除する"""
    db_university = db.query(University).filter(University.id == university_id).first()
    if not db_university:
        return False
    
    db.delete(db_university)
    db.commit()
    return True

# 学部・学科のCRUD操作
def create_department(db: Session, department: DepartmentCreate) -> Department:
    """新しい学部・学科を作成する"""
    # 大学の存在確認
    db_university = db.query(University).filter(University.id == department.university_id).first()
    if not db_university:
        raise ValueError(f"University with ID {department.university_id} not found")
    
    # 学部レコードを作成
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
    
    db.commit()
    db.refresh(db_department)
    return db_department

def get_department(db: Session, department_id: UUID) -> Optional[Department]:
    """特定の学部・学科を取得する"""
    return db.query(Department).filter(Department.id == department_id).options(
        joinedload(Department.details),
        joinedload(Department.university)
    ).first()

def get_university_departments(db: Session, university_id: UUID) -> List[Department]:
    """特定の大学の学部・学科一覧を取得する"""
    return db.query(Department).filter(Department.university_id == university_id).options(
        joinedload(Department.details)
    ).all()

def update_department(db: Session, department_id: UUID, department_data: DepartmentUpdate) -> Optional[Department]:
    """学部・学科情報を更新する"""
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        return None
    
    # 基本情報を更新
    if department_data.name is not None:
        db_department.name = department_data.name
    if department_data.department_code is not None:
        db_department.department_code = department_data.department_code
    if department_data.is_active is not None:
        db_department.is_active = department_data.is_active
    
    # 詳細情報を更新（存在する場合）
    if department_data.details:
        db_details = db.query(DepartmentDetails).filter(
            DepartmentDetails.department_id == department_id
        ).first()
        
        # 詳細がない場合は作成
        if not db_details:
            db_details = DepartmentDetails(
                id=uuid.uuid4(),
                department_id=department_id
            )
            db.add(db_details)
        
        # 詳細を更新
        if department_data.details.description is not None:
            db_details.description = department_data.details.description
    
    db.commit()
    db.refresh(db_department)
    return db_department

def delete_department(db: Session, department_id: UUID) -> bool:
    """学部・学科を削除する"""
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        return False
    
    db.delete(db_department)
    db.commit()
    return True

# 入試方式のCRUD操作
def create_admission_method(db: Session, admission_method: AdmissionMethodCreate) -> AdmissionMethod:
    """新しい入試方式を作成する"""
    # 入試方式レコードを作成
    method_id = uuid.uuid4()
    db_method = AdmissionMethod(
        id=method_id,
        name=admission_method.name,
        is_active=admission_method.is_active
    )
    db.add(db_method)
    
    # 入試方式詳細レコードがあれば作成
    if admission_method.details:
        details_id = uuid.uuid4()
        db_details = AdmissionMethodDetails(
            id=details_id,
            admission_method_id=method_id,
            description=admission_method.details.description
        )
        db.add(db_details)
    
    db.commit()
    db.refresh(db_method)
    return db_method

def get_admission_method(db: Session, method_id: UUID) -> Optional[AdmissionMethod]:
    """特定の入試方式を取得する"""
    return db.query(AdmissionMethod).filter(AdmissionMethod.id == method_id).options(
        joinedload(AdmissionMethod.details)
    ).first()

def get_admission_methods(db: Session) -> List[AdmissionMethod]:
    """入試方式一覧を取得する"""
    return db.query(AdmissionMethod).filter(AdmissionMethod.is_active == True).options(
        joinedload(AdmissionMethod.details)
    ).all()

def update_admission_method(db: Session, method_id: UUID, method_data: AdmissionMethodUpdate) -> Optional[AdmissionMethod]:
    """入試方式情報を更新する"""
    db_method = db.query(AdmissionMethod).filter(AdmissionMethod.id == method_id).first()
    if not db_method:
        return None
    
    # 基本情報を更新
    if method_data.name is not None:
        db_method.name = method_data.name
    if method_data.is_active is not None:
        db_method.is_active = method_data.is_active
    
    # 詳細情報を更新（存在する場合）
    if method_data.details:
        db_details = db.query(AdmissionMethodDetails).filter(
            AdmissionMethodDetails.admission_method_id == method_id
        ).first()
        
        # 詳細がない場合は作成
        if not db_details:
            db_details = AdmissionMethodDetails(
                id=uuid.uuid4(),
                admission_method_id=method_id
            )
            db.add(db_details)
        
        # 詳細を更新
        if method_data.details.description is not None:
            db_details.description = method_data.details.description
    
    db.commit()
    db.refresh(db_method)
    return db_method

def delete_admission_method(db: Session, method_id: UUID) -> bool:
    """入試方式を削除する"""
    db_method = db.query(AdmissionMethod).filter(AdmissionMethod.id == method_id).first()
    if not db_method:
        return False
    
    db.delete(db_method)
    db.commit()
    return True

def get_university_admission_methods(db: Session, university_id: UUID) -> List[Dict[str, Any]]:
    """特定の大学で利用可能な入試方式一覧を取得する"""
    # 実装例：特定の大学と入試方式の関連を取得
    # 実際のデータモデルに合わせて適切に実装する必要があります
    from app.models.university import UniversityAdmissionMethod
    
    university_methods = db.query(
        UniversityAdmissionMethod, AdmissionMethod
    ).join(
        AdmissionMethod, AdmissionMethod.id == UniversityAdmissionMethod.admission_method_id
    ).filter(
        UniversityAdmissionMethod.university_id == university_id,
        AdmissionMethod.is_active == True
    ).all()
    
    result = []
    for rel, method in university_methods:
        result.append({
            "id": str(method.id),
            "name": method.name,
            "description": method.details.description if method.details else None
        })
    
    return result

def get_recommended_universities(db: Session, user_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
    """ユーザーの特性に基づいた推奨大学一覧を取得する"""
    # 実際の実装では、ユーザーのプロフィール、興味、志望校などに基づいてレコメンデーションをする
    # ここではシンプルな例を示す
    
    # ランダムに大学を取得
    from sqlalchemy.sql.expression import func
    universities = db.query(University).order_by(func.random()).limit(limit).all()
    
    result = []
    for university in universities:
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