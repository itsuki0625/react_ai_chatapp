from datetime import datetime
from app.models.user import User, Role
from app.models.university import University, Department
from app.models.school import School
from app.models.admission import AdmissionMethod
from sqlalchemy.orm import Session
from app.core.security import get_password_hash

def insert_demo_data(db: Session):
    # ロールデータ
    roles = [
        Role(
            name="管理者",
            description="システム管理者",
            permissions="admin"
        ),
        Role(
            name="教員",
            description="高校教員",
            permissions="teacher"
        ),
        Role(
            name="生徒",
            description="高校生",
            permissions="student"
        )
    ]
    for role in roles:
        db.add(role)
    db.flush()

    # 高校データ
    demo_school = School(
        name="デモ高校",
        school_code="D123456",
        prefecture="東京都",
        city="千代田区",
        zip_code="100-0001",
        contact_email="contact@demo-high.ed.jp",
        contact_phone="03-1234-5678",
        principal_name="校長 太郎",
        website_url="https://demo-high.ed.jp",
        is_active=True
    )
    db.add(demo_school)
    db.flush()

    # 大学データ
    demo_university = University(
        name="デモ大学",
        university_code="U123456",
        prefecture="東京都",
        city="文京区",
        zip_code="113-0001",
        contact_email="contact@demo-univ.ac.jp",
        contact_phone="03-9876-5432",
        president_name="学長 太郎",
        website_url="https://demo-univ.ac.jp",
        is_active=True
    )
    db.add(demo_university)
    db.flush()

    # 学部・学科データ
    departments = [
        # 工学部
        Department(
            university_id=demo_university.id,
            name="工学部 情報工学科",
            department_code="E001",
            description="情報工学を専門的に学ぶ学科です",
            is_active=True
        ),
        Department(
            university_id=demo_university.id,
            name="工学部 電気電子工学科",
            department_code="E002",
            description="電気電子工学を専門的に学ぶ学科です",
            is_active=True
        ),
        # 理学部
        Department(
            university_id=demo_university.id,
            name="理学部 数学科",
            department_code="S001",
            description="数学を専門的に学ぶ学科です",
            is_active=True
        ),
        Department(
            university_id=demo_university.id,
            name="理学部 物理学科",
            department_code="S002",
            description="物理学を専門的に学ぶ学科です",
            is_active=True
        ),
        # 経済学部
        Department(
            university_id=demo_university.id,
            name="経済学部 経済学科",
            department_code="B001",
            description="経済学を専門的に学ぶ学科です",
            is_active=True
        ),
        Department(
            university_id=demo_university.id,
            name="経済学部 経営学科",
            department_code="B002",
            description="経営学を専門的に学ぶ学科です",
            is_active=True
        )
    ]
    for department in departments:
        db.add(department)
    db.flush()

    # 入試方式データ
    admission_methods = [
        AdmissionMethod(
            name="一般選抜",
            description="共通テストを利用した一般選抜入試",
            is_active=True
        ),
        AdmissionMethod(
            name="総合型選抜",
            description="面接と課題による総合型選抜",
            is_active=True
        ),
        AdmissionMethod(
            name="学校推薦型選抜",
            description="高校からの推薦による選抜",
            is_active=True
        )
    ]
    for method in admission_methods:
        db.add(method)
    db.flush()

    # ユーザーデー��
    users = [
        User(
            email="admin@demo-univ.ac.jp",
            hashed_password=get_password_hash("admin123"),  # password: "admin123"
            full_name="管理者 テスト",
            role_id=roles[0].id,  # 管理者ロール
            school_id=demo_school.id,
            is_active=True
        ),
        User(
            email="teacher@demo-high.ed.jp",
            hashed_password=get_password_hash("teacher123"),  # password: "teacher123"
            full_name="教員 テスト",
            role_id=roles[1].id,  # 教員ロール
            school_id=demo_school.id,
            is_active=True
        ),
        User(
            email="student@example.com",
            hashed_password=get_password_hash("student123"),  # password: "student123"
            full_name="生徒 テスト",
            role_id=roles[2].id,  # 生徒ロール
            school_id=demo_school.id,
            grade=3,
            class_number="A",
            student_number="001",
            is_active=True
        )
    ]
    for user in users:
        db.add(user)
    db.flush()

    # テストユーザーの作成
    test_user = User(
        email="test@example.com",
        hashed_password=get_password_hash("test123"),  # パスワードをハッシュ化
        full_name="テストユーザー",
        role_id=roles[2].id,  # 生徒ロール
        is_active=True
    )
    db.add(test_user)
    db.commit() 