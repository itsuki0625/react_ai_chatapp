from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, Role, Permission, RolePermission, UserProfile, UserLoginInfo
from app.models.user import UserEmailVerification, UserTwoFactorAuth, UserRole, UserRoleAssignment, UserRoleMetadata
from app.models.user import TokenBlacklist, UserContactInfo

from app.models.school import School, SchoolDetails, SchoolContact
from app.models.university import University, UniversityDetails, UniversityContact, Department, DepartmentDetails
from app.models.admission import AdmissionMethod, AdmissionMethodDetails

from app.models.desired_school import DesiredSchool, DesiredDepartment
from app.models.document import Document, DocumentSubmission
from app.models.schedule import ScheduleEvent, EventCompletion
from app.models.personal_statement import PersonalStatement, PersonalStatementSubmission, Feedback

from app.models.chat import ChatSession, ChatSessionMetaData, ChatMessage, ChatMessageMetaData, ChatAttachment
from app.models.checklist import ChecklistEvaluation
from app.models.subscription import DiscountType

from app.models.base import TimestampMixin
from app.models.enums import DocumentStatus, PersonalStatementStatus, SessionType, SessionStatus, SenderType, MessageType

def insert_demo_data(db: Session):
    """
    第3正規形に基づいたデモデータを挿入する関数
    """
    # 以下に各テーブルのデモデータを追加していきます
    
    # ========= 1. ユーザー関連テーブル =========
    users = create_user_related_data(db)
    
    # ========= 2. 学校・大学関連テーブル =========
    school_data = create_school_university_data(db)
    
    # ========= 3. 志望校関連テーブル =========
    create_desired_school_data(db, users, school_data)
    
    # ========= 4. チャット関連テーブル =========
    create_chat_related_data(db, users)
    
    # ========= 5. サブスクリプション関連テーブル =========
    # サブスクリプションプランテーブルは削除されたため実装しない
    create_subscription_related_data(db)
    
    # ========= 6. コンテンツ関連テーブル =========
    create_content_related_data(db, users)
    
    # ========= 7. 学習進捗関連テーブル =========
    create_study_progress_data(db, users)
    
    # ========= 8. クイズ・テスト関連テーブル =========
    create_quiz_data(db, users)
    
    # ========= 9. フォーラム関連テーブル =========
    create_forum_data(db, users)
    
    # 最終的にコミット
    db.commit()


# 以下、各機能ごとの関数を実装していきます

def create_user_related_data(db: Session):
    # ========= ロールデータ =========
    roles = [
        Role(
            name="管理者",
            description="システム管理者",
            is_active=True
        ),
        Role(
            name="教員",
            description="高校教員",
            is_active=True
        ),
        Role(
            name="生徒",
            description="高校生",
            is_active=True
        ),
        Role(
            name="システム",
            description="システムユーザー",
            is_active=True
        )
    ]
    for role in roles:
        db.add(role)
    db.flush()

    # ========= 権限データ =========
    permissions = [
        Permission(
            name="user_read",
            description="ユーザー情報の閲覧権限"
        ),
        Permission(
            name="user_write",
            description="ユーザー情報の編集権限"
        ),
        Permission(
            name="content_read",
            description="コンテンツの閲覧権限"
        ),
        Permission(
            name="content_write",
            description="コンテンツの編集権限"
        ),
        Permission(
            name="admin_access",
            description="管理者画面へのアクセス権限"
        )
    ]
    for permission in permissions:
        db.add(permission)
    db.flush()

    # ========= ロール権限の関連付け =========
    # 管理者のロール権限
    admin_permissions = [
        RolePermission(
            role_id=roles[0].id,  # 管理者ロール
            permission_id=permissions[0].id,  # user_read
            is_granted=True
        ),
        RolePermission(
            role_id=roles[0].id,
            permission_id=permissions[1].id,  # user_write
            is_granted=True
        ),
        RolePermission(
            role_id=roles[0].id,
            permission_id=permissions[2].id,  # content_read
            is_granted=True
        ),
        RolePermission(
            role_id=roles[0].id,
            permission_id=permissions[3].id,  # content_write
            is_granted=True
        ),
        RolePermission(
            role_id=roles[0].id,
            permission_id=permissions[4].id,  # admin_access
            is_granted=True
        )
    ]
    for rp in admin_permissions:
        db.add(rp)
    
    # 教員のロール権限
    teacher_permissions = [
        RolePermission(
            role_id=roles[1].id,  # 教員ロール
            permission_id=permissions[0].id,  # user_read
            is_granted=True
        ),
        RolePermission(
            role_id=roles[1].id,
            permission_id=permissions[2].id,  # content_read
            is_granted=True
        ),
        RolePermission(
            role_id=roles[1].id,
            permission_id=permissions[3].id,  # content_write
            is_granted=True
        )
    ]
    for rp in teacher_permissions:
        db.add(rp)
    
    # 生徒のロール権限
    student_permissions = [
        RolePermission(
            role_id=roles[2].id,  # 生徒ロール
            permission_id=permissions[2].id,  # content_read
            is_granted=True
        )
    ]
    for rp in student_permissions:
        db.add(rp)
    db.flush()

    # ========= ユーザーデータ =========
    users = [
        User(
            id=uuid.uuid4(),
            email="admin@demo-univ.ac.jp",
            hashed_password=get_password_hash("admin123"),  # password: "admin123"
            full_name="管理者 テスト",
            is_active=True
        ),
        User(
            id=uuid.uuid4(),
            email="teacher@demo-high.ed.jp",
            hashed_password=get_password_hash("teacher123"),  # password: "teacher123"
            full_name="教員 テスト",
            is_active=True
        ),
        User(
            id=uuid.uuid4(),
            email="student@example.com",
            hashed_password=get_password_hash("student123"),  # password: "student123"
            full_name="生徒 テスト",
            is_active=True
        ),
        User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password=get_password_hash("test123"),  # パスワードをハッシュ化
            full_name="テストユーザー",
            is_active=True
        ),
        User(
            id=uuid.uuid4(),
            email="ai-system@example.com",
            hashed_password=get_password_hash("aiSystem@123"),
            full_name="AIシステム",
            is_active=True
        )
    ]
    for user in users:
        db.add(user)
    db.flush()

    # ========= ユーザーロール関連付け =========
    user_roles = [
        UserRole(
            id=uuid.uuid4(),
            user_id=users[0].id,
            role_id=roles[0].id,  # 管理者ロール
            is_primary=True
        ),
        UserRole(
            id=uuid.uuid4(),
            user_id=users[1].id,
            role_id=roles[1].id,  # 教員ロール
            is_primary=True
        ),
        UserRole(
            id=uuid.uuid4(),
            user_id=users[2].id,
            role_id=roles[2].id,  # 生徒ロール
            is_primary=True
        ),
        UserRole(
            id=uuid.uuid4(),
            user_id=users[3].id,
        role_id=roles[2].id,  # 生徒ロール
            is_primary=True
        ),
        UserRole(
            id=uuid.uuid4(),
            user_id=users[4].id,
            role_id=roles[3].id,  # システムロール
            is_primary=True
        )
    ]
    for ur in user_roles:
        db.add(ur)
    db.flush()
    
    # ========= ユーザーロール割り当て =========
    for i, ur in enumerate(user_roles):
        assignment = UserRoleAssignment(
            id=uuid.uuid4(),
            user_role_id=ur.id,
            assigned_at=datetime.utcnow(),
            assigned_by=users[0].id if i > 0 else None  # 管理者が割り当てたとする（自分以外）
        )
        db.add(assignment)
    db.flush()
    
    # ========= ユーザープロフィール =========
    profiles = [
        UserProfile(
            id=uuid.uuid4(),
            user_id=users[0].id,
            profile_image_url="https://example.com/profiles/admin.jpg"
        ),
        UserProfile(
            id=uuid.uuid4(),
            user_id=users[1].id,
            profile_image_url="https://example.com/profiles/teacher.jpg"
        ),
        UserProfile(
            id=uuid.uuid4(),
            user_id=users[2].id,
            grade=3,
            class_number="A",
            student_number="001",
            profile_image_url="https://example.com/profiles/student.jpg"
        ),
        UserProfile(
            id=uuid.uuid4(),
            user_id=users[3].id,
            grade=2,
            class_number="B",
            student_number="015",
            profile_image_url="https://example.com/profiles/test.jpg"
        )
    ]
    for profile in profiles:
        db.add(profile)
    db.flush()
    
    # ========= ユーザーログイン情報 =========
    for i, user in enumerate(users):
        login_info = UserLoginInfo(
            id=uuid.uuid4(),
            user_id=user.id,
            last_login_at=datetime.utcnow() - timedelta(days=i),
            failed_login_attempts=0
        )
        db.add(login_info)
    db.flush()
    
    # ========= ユーザーメール検証 =========
    for i, user in enumerate(users):
        email_verification = UserEmailVerification(
            id=uuid.uuid4(),
            user_id=user.id,
            email_verified=True,  # デモデータなので検証済みとする
            email_verification_token=f"token_{uuid.uuid4()}",
            email_verification_sent_at=datetime.utcnow() - timedelta(days=10)
        )
        db.add(email_verification)
    db.flush()
    
    # ========= ユーザー連絡先情報 =========
    contact_info = [
        UserContactInfo(
            id=uuid.uuid4(),
            user_id=users[0].id,
            contact_type="email",
            contact_value="admin_secondary@example.com",
            is_primary=False,
            verified=True
        ),
        UserContactInfo(
            id=uuid.uuid4(),
            user_id=users[0].id,
            contact_type="phone",
            contact_value="090-1234-5678",
            is_primary=True,
            verified=True
        ),
        UserContactInfo(
            id=uuid.uuid4(),
            user_id=users[1].id,
            contact_type="phone",
            contact_value="090-8765-4321",
            is_primary=True,
            verified=True
        ),
        UserContactInfo(
            id=uuid.uuid4(),
            user_id=users[2].id,
            contact_type="phone",
            contact_value="080-1111-2222",
            is_primary=True,
            verified=False
        )
    ]
    for ci in contact_info:
        db.add(ci)
    db.flush()

    return users

def create_school_university_data(db: Session):
    # ========= 高校データ =========
    demo_school = School(
        id=uuid.uuid4(),
        name="デモ高校",
        school_code="D123456",
        is_active=True
    )
    db.add(demo_school)
    db.flush()
    
    # 高校詳細情報
    school_details = SchoolDetails(
        id=uuid.uuid4(),
        school_id=demo_school.id,
        address="東京都千代田区1-1-1",
        prefecture="東京都",
        city="千代田区",
        zip_code="100-0001",
        principal_name="校長 太郎",
        website_url="https://demo-high.ed.jp"
    )
    db.add(school_details)
    db.flush()
    
    # 高校連絡先
    school_contacts = [
        SchoolContact(
            id=uuid.uuid4(),
            school_id=demo_school.id,
            contact_type="email",
            contact_value="contact@demo-high.ed.jp",
            is_primary=True
        ),
        SchoolContact(
            id=uuid.uuid4(),
            school_id=demo_school.id,
            contact_type="phone",
            contact_value="03-1234-5678",
            is_primary=True
        ),
        SchoolContact(
            id=uuid.uuid4(),
            school_id=demo_school.id,
            contact_type="fax",
            contact_value="03-1234-5679",
            is_primary=True
        )
    ]
    for contact in school_contacts:
        db.add(contact)
    db.flush()
    
    # ========= 大学データ =========
    demo_university = University(
        id=uuid.uuid4(),
        name="デモ大学",
        university_code="U123456",
        is_active=True
    )
    db.add(demo_university)
    db.flush()
    
    # 大学詳細情報
    university_details = UniversityDetails(
        id=uuid.uuid4(),
        university_id=demo_university.id,
        address="東京都文京区2-2-2",
        prefecture="東京都",
        city="文京区",
        zip_code="113-0001",
        president_name="学長 太郎",
        website_url="https://demo-univ.ac.jp"
    )
    db.add(university_details)
    db.flush()
    
    # 大学連絡先
    university_contacts = [
        UniversityContact(
            id=uuid.uuid4(),
            university_id=demo_university.id,
            contact_type="email",
            contact_value="contact@demo-univ.ac.jp",
            is_primary=True
        ),
        UniversityContact(
            id=uuid.uuid4(),
            university_id=demo_university.id,
            contact_type="phone",
            contact_value="03-9876-5432",
            is_primary=True
        ),
        UniversityContact(
            id=uuid.uuid4(),
            university_id=demo_university.id,
            contact_type="fax",
            contact_value="03-9876-5433",
            is_primary=True
        )
    ]
    for contact in university_contacts:
        db.add(contact)
    db.flush()
    
    # ========= 学部・学科データ =========
    departments_data = [
        # 工学部
        {
            "name": "工学部 情報工学科",
            "department_code": "E001",
            "description": "情報工学を専門的に学ぶ学科です"
        },
        {
            "name": "工学部 電気電子工学科",
            "department_code": "E002",
            "description": "電気電子工学を専門的に学ぶ学科です"
        },
        # 理学部
        {
            "name": "理学部 数学科",
            "department_code": "S001",
            "description": "数学を専門的に学ぶ学科です"
        },
        {
            "name": "理学部 物理学科",
            "department_code": "S002",
            "description": "物理学を専門的に学ぶ学科です"
        },
        # 経済学部
        {
            "name": "経済学部 経済学科",
            "department_code": "B001",
            "description": "経済学を専門的に学ぶ学科です"
        },
        {
            "name": "経済学部 経営学科",
            "department_code": "B002",
            "description": "経営学を専門的に学ぶ学科です"
        }
    ]
    
    departments = []
    for dept_data in departments_data:
        dept = Department(
            id=uuid.uuid4(),
            university_id=demo_university.id,
            name=dept_data["name"],
            department_code=dept_data["department_code"],
            is_active=True
        )
        db.add(dept)
        departments.append(dept)
    db.flush()
    
    # 学部・学科詳細情報
    for i, dept in enumerate(departments):
        dept_details = DepartmentDetails(
            id=uuid.uuid4(),
            department_id=dept.id,
            description=departments_data[i]["description"]
        )
        db.add(dept_details)
    db.flush()
    
    # ========= 入試方式データ =========
    admission_methods_data = [
        {
            "name": "一般選抜",
            "description": "共通テストを利用した一般選抜入試"
        },
        {
            "name": "総合型選抜",
            "description": "面接と課題による総合型選抜"
        },
        {
            "name": "学校推薦型選抜",
            "description": "高校からの推薦による選抜"
        }
    ]
    
    admission_methods = []
    for method_data in admission_methods_data:
        method = AdmissionMethod(
            id=uuid.uuid4(),
            name=method_data["name"],
            is_active=True
        )
        db.add(method)
        admission_methods.append(method)
    db.flush()
    
    # 入試方式詳細情報
    for i, method in enumerate(admission_methods):
        method_details = AdmissionMethodDetails(
            id=uuid.uuid4(),
            admission_method_id=method.id,
            description=admission_methods_data[i]["description"]
        )
        db.add(method_details)
    db.flush()
    
    return {
        "school": demo_school,
        "university": demo_university,
        "departments": departments,
        "admission_methods": admission_methods
    }

def create_desired_school_data(db: Session, users, school_data):
    # ユーザー（生徒）
    student = users[2]  # 生徒ユーザー
    
    # 大学と学部・学科
    university = school_data["university"]
    departments = school_data["departments"]
    admission_methods = school_data["admission_methods"]
    
    # ========= 志望校データ =========
    # 第一志望
    desired_school1 = DesiredSchool(
        id=uuid.uuid4(),
        user_id=student.id,
        university_id=university.id,
        preference_order=1  # 第一志望
    )
    db.add(desired_school1)
    
    # 第二志望（別の大学を使うため、ここでは同じ大学とする）
    desired_school2 = DesiredSchool(
        id=uuid.uuid4(),
        user_id=student.id,
        university_id=university.id,
        preference_order=2  # 第二志望
    )
    db.add(desired_school2)
    db.flush()
    
    # ========= 志望学部・学科データ =========
    # 第一志望の学部・学科（工学部情報工学科 - 一般選抜）
    desired_dept1 = DesiredDepartment(
        id=uuid.uuid4(),
        desired_school_id=desired_school1.id,
        department_id=departments[0].id,  # 工学部情報工学科
        admission_method_id=admission_methods[0].id  # 一般選抜
    )
    db.add(desired_dept1)
    
    # 第一志望の別学部・学科（理学部数学科 - 総合型選抜）
    desired_dept2 = DesiredDepartment(
        id=uuid.uuid4(),
        desired_school_id=desired_school1.id,
        department_id=departments[2].id,  # 理学部数学科
        admission_method_id=admission_methods[1].id  # 総合型選抜
    )
    db.add(desired_dept2)
    
    # 第二志望の学部・学科（経済学部経済学科 - 学校推薦型選抜）
    desired_dept3 = DesiredDepartment(
        id=uuid.uuid4(),
        desired_school_id=desired_school2.id,
        department_id=departments[4].id,  # 経済学部経済学科
        admission_method_id=admission_methods[2].id  # 学校推薦型選抜
    )
    db.add(desired_dept3)
    db.flush()
    
    # ========= 提出書類データ =========
    documents = [
        Document(
            id=uuid.uuid4(),
            desired_department_id=desired_dept1.id,
            name="成績証明書",
            status=DocumentStatus.DRAFT,  # pending, submitted, approved, rejected
            deadline=datetime.utcnow() + timedelta(days=30)
        ),
        Document(
            id=uuid.uuid4(),
            desired_department_id=desired_dept1.id,
            name="志願書",
            status=DocumentStatus.DRAFT,
            deadline=datetime.utcnow() + timedelta(days=20)
        ),
        Document(
            id=uuid.uuid4(),
            desired_department_id=desired_dept2.id,
            name="ポートフォリオ",
            status=DocumentStatus.SUBMITTED,
            deadline=datetime.utcnow() + timedelta(days=15)
        ),
        Document(
            id=uuid.uuid4(),
            desired_department_id=desired_dept3.id,
            name="推薦書",
            status=DocumentStatus.DRAFT,
            deadline=datetime.utcnow() + timedelta(days=25)
        )
    ]
    for doc in documents:
        db.add(doc)
    db.flush()
    
    # 提出済み書類
    doc_submission = DocumentSubmission(
        id=uuid.uuid4(),
        document_id=documents[2].id,  # ポートフォリオ
        submitted_at=datetime.utcnow() - timedelta(days=2),
        submitted_by=student.id
    )
    db.add(doc_submission)
    db.flush()
    
    # ========= スケジュールイベント =========
    events = [
        ScheduleEvent(
            id=uuid.uuid4(),
            desired_department_id=desired_dept1.id,
            event_name="出願期間開始",
            event_date=datetime.utcnow() + timedelta(days=10),
            event_type="application"
        ),
        ScheduleEvent(
            id=uuid.uuid4(),
            desired_department_id=desired_dept1.id,
            event_name="出願期間終了",
            event_date=datetime.utcnow() + timedelta(days=20),
            event_type="application"
        ),
        ScheduleEvent(
            id=uuid.uuid4(),
            desired_department_id=desired_dept1.id,
            event_name="試験日",
            event_date=datetime.utcnow() + timedelta(days=45),
            event_type="exam"
        ),
        ScheduleEvent(
            id=uuid.uuid4(),
            desired_department_id=desired_dept2.id,
            event_name="ポートフォリオ提出締切",
            event_date=datetime.utcnow() + timedelta(days=15),
            event_type="submission"
        ),
        ScheduleEvent(
            id=uuid.uuid4(),
            desired_department_id=desired_dept2.id,
            event_name="面接",
            event_date=datetime.utcnow() + timedelta(days=30),
            event_type="interview"
        )
    ]
    for event in events:
        db.add(event)
    db.flush()
    
    # 完了イベント
    event_completion = EventCompletion(
        id=uuid.uuid4(),
        event_id=events[3].id,  # ポートフォリオ提出締切
        completed=True,
        completed_at=datetime.utcnow() - timedelta(days=2),
        completed_by=student.id
    )
    db.add(event_completion)
    db.flush()
    
    # ========= 志望理由書 =========
    statements = [
        PersonalStatement(
            id=uuid.uuid4(),
            user_id=student.id,
            desired_department_id=desired_dept1.id,
            content="私は情報技術に興味があり、AIや機械学習の分野で研究したいと考えています...",
            status=PersonalStatementStatus.DRAFT,  # draft, submitted, reviewed
            submission_deadline=datetime.utcnow() + timedelta(days=20)
        ),
        PersonalStatement(
            id=uuid.uuid4(),
            user_id=student.id,
            desired_department_id=desired_dept2.id,
            content="私は数学が好きで、特に代数学と幾何学に興味があります...",
            status=PersonalStatementStatus.REVIEW,
            submission_deadline=datetime.utcnow() + timedelta(days=15)
        )
    ]
    for stmt in statements:
        db.add(stmt)
    db.flush()
    
    # 提出された志望理由書
    stmt_submission = PersonalStatementSubmission(
        id=uuid.uuid4(),
        personal_statement_id=statements[1].id,
        submitted_at=datetime.utcnow() - timedelta(days=3),
        submitted_by=student.id
    )
    db.add(stmt_submission)
    db.flush()
    
    # フィードバック
    feedback = Feedback(
        id=uuid.uuid4(),
        personal_statement_id=statements[1].id,
        feedback_user_id=users[1].id,  # 教員からのフィードバック
        content="志望理由が明確で良いですが、もう少し具体的なエピソードがあるとより説得力が増します。"
    )
    db.add(feedback)
    db.flush()

def create_chat_related_data(db: Session, users):
    student = users[2]  # 生徒ユーザー
    ai_user = users[4]  # AIシステムユーザー
    
    # ========= チャットセッション =========
    chat_sessions = [
        ChatSession(
            id=uuid.uuid4(),
            user_id=student.id,
            title="大学入試についての相談",
            session_type=SessionType.CONSULTATION,
            status=SessionStatus.ACTIVE,
            last_message_at=datetime.utcnow() - timedelta(hours=2)
        ),
        ChatSession(
            id=uuid.uuid4(),
            user_id=student.id,
            title="志望理由書の添削依頼",
            session_type=SessionType.CONSULTATION,
            status=SessionStatus.ACTIVE,
            last_message_at=datetime.utcnow() - timedelta(days=1)
        ),
        ChatSession(
            id=uuid.uuid4(),
            user_id=student.id,
            title="数学の質問",
            session_type=SessionType.NORMAL,
            status=SessionStatus.CLOSED,
            last_message_at=datetime.utcnow() - timedelta(days=3)
        )
    ]
    for session in chat_sessions:
        db.add(session)
    db.flush()
    
    # ========= チャットセッションメタデータ =========
    session_metadata = [
        ChatSessionMetaData(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            key="target_university",
            value="デモ大学"
        ),
        ChatSessionMetaData(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            key="admission_method",
            value="総合型選抜"
        ),
        ChatSessionMetaData(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            key="department",
            value="工学部情報工学科"
        )
    ]
    for meta in session_metadata:
        db.add(meta)
    db.flush()
    
    # ========= チャットメッセージ =========
    # 第1セッションのメッセージ
    messages_session1 = [
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="デモ大学の総合型選抜について教えてください。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="デモ大学の総合型選抜では、書類審査と面接が行われます。書類には志望理由書とポートフォリオの提出が必要です。面接は約20分間で、あなたの学習意欲や将来の目標について質問されます。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="ポートフォリオには何を入れればいいですか？",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="ポートフォリオには、あなたのこれまでの活動や成果物をまとめます。例えば、研究プロジェクト、課外活動、受賞歴、資格などです。特に情報工学科を志望する場合は、プログラミングの経験やIT関連の活動を強調するとよいでしょう。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="ありがとうございます。面接対策はどうすればいいですか？",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=2)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[0].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="面接対策としては以下の準備をおすすめします：\n1. 志望理由を明確に説明できるようにする\n2. 自分の強みや特技を具体的なエピソードと共に準備する\n3. 大学の特色や学部の研究内容について調べておく\n4. 想定質問に対する回答を練習する\n5. 質問も数個用意しておく\n\n模擬面接を行うことも効果的です。面接直前にはリラックスして自信を持って臨みましょう。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(hours=2)
        )
    ]
    
    # 第2セッションのメッセージ
    messages_session2 = [
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="志望理由書を添削してもらえませんか？",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="はい、喜んで添削します。志望理由書をアップロードしてください。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="志望理由書_工学部情報工学科.pdf",
            message_type=MessageType.FILE,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="志望理由書を拝見しました。全体的に良く書けていますが、いくつか改善点があります：\n\n1. 冒頭部分：もう少し印象的な導入ができるとよいでしょう\n2. 2段落目：具体的なエピソードをもう少し詳しく書くと説得力が増します\n3. 最終段落：大学で学びたいことをより具体的に記述するとよいでしょう\n\n修正案を作成しました。ご確認ください。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="志望理由書_修正案.pdf",
            message_type=MessageType.FILE,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="ありがとうございます。修正案を参考に書き直してみます。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=1, hours=1)
        )
    ]
    
    # 第3セッションのメッセージ
    messages_session3 = [
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="数学の微分方程式について質問があります。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=6)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="微分方程式についてどのような質問ですか？",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=6)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="dy/dx + Py = Q の形の1階線形微分方程式の解き方がわかりません。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="1階線形微分方程式 dy/dx + Py = Q の解法を説明します。\n\nこれは積分因子法で解くことができます。\n\n1. まず積分因子 μ = exp(∫P dx) を見つけます\n2. 両辺に μ を掛けると、左辺が d(μy)/dx の形になります\n3. すなわち d(μy)/dx = μQ となります\n4. 両辺を積分して μy = ∫μQ dx + C\n5. 最後に y について解きます: y = (∫μQ dx + C) / μ\n\n具体例を挙げると分かりやすいかもしれません。例題を解いてみましょうか？",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=5)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="はい、例題をお願いします。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=ai_user.id,  # AIシステムユーザー
            sender_type=SenderType.AI,
            content="例題: dy/dx + 2xy = x を解いてみましょう。\n\nこの場合、P(x) = 2x, Q(x) = x です。\n\n1. 積分因子 μ = exp(∫2x dx) = exp(x²)\n2. 両辺に μ を掛ける: exp(x²) dy/dx + 2x·exp(x²)y = x·exp(x²)\n3. 左辺は d(exp(x²)y)/dx の形\n4. よって d(exp(x²)y)/dx = x·exp(x²)\n5. 両辺を積分: exp(x²)y = ∫x·exp(x²) dx\n\n∫x·exp(x²) dx は置換積分で解けます。u = x² とすると du = 2x dx なので、x dx = du/2\n∫x·exp(x²) dx = ∫exp(u)·du/2 = (1/2)exp(u) + C = (1/2)exp(x²) + C\n\n6. よって exp(x²)y = (1/2)exp(x²) + C\n7. y について解くと: y = 1/2 + C·exp(-x²)\n\nこれが求める一般解です。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=4)
        ),
        ChatMessage(
            id=uuid.uuid4(),
            session_id=chat_sessions[2].id,
            sender_id=student.id,
            sender_type=SenderType.USER,
            content="わかりました！ありがとうございます。",
            message_type=MessageType.TEXT,
            is_read=True,
            read_at=datetime.utcnow() - timedelta(days=3, hours=3)
        )
    ]
    
    # すべてのメッセージを追加
    all_messages = messages_session1 + messages_session2 + messages_session3
    for msg in all_messages:
        db.add(msg)
    db.flush()
    
    # ========= チャット添付ファイル =========
    # 第2セッションのファイル添付（学生からのアップロード）
    attachment1 = ChatAttachment(
        id=uuid.uuid4(),
        message_id=messages_session2[2].id,  # 学生がアップロードしたメッセージ
        file_url="https://storage.example.com/files/ps_original.pdf",
        file_type="application/pdf",
        file_size=256000,  # 250KB
        file_name="志望理由書_工学部情報工学科.pdf"
    )
    db.add(attachment1)
    
    # 第2セッションのファイル添付（AIの修正案）
    attachment2 = ChatAttachment(
        id=uuid.uuid4(),
        message_id=messages_session2[4].id,  # AIが返信したファイル
        file_url="https://storage.example.com/files/ps_revised.pdf",
        file_type="application/pdf",
        file_size=280000,  # 275KB
        file_name="志望理由書_修正案.pdf"
    )
    db.add(attachment2)
    db.flush()
    
    # ========= チェックリスト評価 =========
    checklists = [
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="志望理由の明確さ",
            is_completed=True,
            score=4,  # 5段階で4
            evaluator_id=None,  # AIによる評価
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="具体的なエピソード",
            is_completed=True,
            score=3,  # 5段階で3
            evaluator_id=None,  # AIによる評価
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="文章構成",
            is_completed=True,
            score=4,  # 5段階で4
            evaluator_id=None,  # AIによる評価
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="誤字脱字",
            is_completed=True,
            score=5,  # 5段階で5
            evaluator_id=None,  # AIによる評価
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        )
    ]
    for checklist in checklists:
        db.add(checklist)
    db.flush()

def create_content_related_data(db: Session, users):
    # コンテンツ関連データの作成
    # ここにコンテンツ関連のデータを追加するコードを書く
    pass

def create_study_progress_data(db: Session, users):
    # 学習進捗関連データの作成
    # ここに学習進捗関連のデータを追加するコードを書く
    pass

def create_quiz_data(db: Session, users):
    # クイズ・テスト関連データの作成
    # ここにクイズ・テスト関連のデータを追加するコードを書く
    pass

def create_forum_data(db: Session, users):
    # フォーラム関連データの作成
    # ここにフォーラム関連のデータを追加するコードを書く
    pass

def create_subscription_related_data(db: Session):
    """
    割引タイプなどのサブスクリプション関連データを挿入します。
    """
    # ========= 割引タイプデータ =========
    print("Seeding discount types...")
    try:
        # 既存のデータをチェック
        existing_percentage = db.query(DiscountType).filter(DiscountType.name == 'percentage').first()
        existing_fixed = db.query(DiscountType).filter(DiscountType.name == 'fixed').first()
        # --- 追加チェック ---
        existing_none = db.query(DiscountType).filter(DiscountType.name == 'none').first()
        existing_trial_fixed = db.query(DiscountType).filter(DiscountType.name == 'trial_fixed').first()
        existing_trial_percentage = db.query(DiscountType).filter(DiscountType.name == 'trial_percentage').first()
        # --- ここまで ---

        added = False
        if not existing_percentage:
            percentage_type = DiscountType(
                id=uuid.uuid4(), # UUIDを生成
                name='percentage',
                description='割引率 (%)'
            )
            db.add(percentage_type)
            print("Added 'percentage' discount type.")
            added = True

        if not existing_fixed:
            fixed_type = DiscountType(
                id=uuid.uuid4(), # UUIDを生成
                name='fixed',
                description='固定割引額 (円)'
            )
            db.add(fixed_type)
            print("Added 'fixed' discount type.")
            added = True
            
        # --- 追加のタイプを追加 --- 
        if not existing_none:
            none_type = DiscountType(
                id=uuid.uuid4(),
                name='none',
                description='割引なし'
            )
            db.add(none_type)
            print("Added 'none' discount type.")
            added = True
            
        if not existing_trial_fixed:
            trial_fixed_type = DiscountType(
                id=uuid.uuid4(),
                name='trial_fixed',
                description='トライアル固定価格'
            )
            db.add(trial_fixed_type)
            print("Added 'trial_fixed' discount type.")
            added = True
            
        if not existing_trial_percentage:
            trial_percentage_type = DiscountType(
                id=uuid.uuid4(),
                name='trial_percentage',
                description='トライアル割引率'
            )
            db.add(trial_percentage_type)
            print("Added 'trial_percentage' discount type.")
            added = True
        # --- ここまで --- 

        if added:
            # ここでは flush のみ行い、コミットは insert_demo_data の最後で行う
            db.flush()
            print("Discount types flushed.")
        else:
            # メッセージを更新
            print("All required discount types already exist.") 

    except Exception as e:
        print(f"An error occurred during discount type seeding: {e}")
        # ロールバックは不要（コミット前のため） 