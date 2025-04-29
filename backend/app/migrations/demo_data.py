import logging
import uuid
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

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

from app.models.chat import ChatSession, ChatMessage, ChatAttachment
from app.models.checklist import ChecklistEvaluation
from app.models.subscription import DiscountType, CampaignCode, SubscriptionPlan

from app.models.base import TimestampMixin, Base
from app.models.enums import DocumentStatus, PersonalStatementStatus, SessionType, SessionStatus, MessageSender, ChatType
from app.models.enums import UserStatus

logger = logging.getLogger(__name__)

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
    roles_data = {
        "管理者": Role(id=uuid.uuid4(), name="管理者", description="システム管理者", is_active=True),
        "教員": Role(id=uuid.uuid4(), name="教員", description="高校教員", is_active=True),
        "フリー": Role(id=uuid.uuid4(), name="フリー", description="無料プランユーザー", is_active=True),
        "スタンダード": Role(id=uuid.uuid4(), name="スタンダード", description="標準プランユーザー", is_active=True),
        "プレミアム": Role(id=uuid.uuid4(), name="プレミアム", description="上位プランユーザー", is_active=True),
        "システム": Role(id=uuid.uuid4(), name="システム", description="システムユーザー", is_active=True)
    }
    for role in roles_data.values(): db.add(role)
    db.flush()
    # ★修正: DBからロールを再取得して、IDが確定したオブジェクトを使用する
    roles = {r.name: r for r in db.query(Role).all()}

    # ========= 権限データ =========
    # ★修正: 権限定義をこのファイル内に移動
    # PERMISSIONS_TO_ADD に相当するデータをここで定義
    all_permissions_data = {
        # Community
        'community_read': 'コミュニティ投稿を閲覧する',
        'community_post_create': 'コミュニティ投稿を作成する',
        'community_post_delete_own': '自分のコミュニティ投稿を削除する',
        'community_post_delete_any': '（管理者向け）任意のコミュニティ投稿を削除する',
        'community_category_manage': '（管理者向け）コミュニティカテゴリを管理する',
        # Chat
        'chat_session_read': 'チャットセッションを閲覧する',
        'chat_message_send': 'チャットメッセージを送信する',
        # Desired School
        'desired_school_manage_own': '自分の志望校リストを管理する',
        'desired_school_view_all': '（管理者向け）全ユーザーの志望校リストを閲覧する',
        # Statement
        'statement_manage_own': '自分の志望理由書を管理する',
        'statement_review_request': '志望理由書のレビューを依頼する',
        'statement_review_respond': '（教員/管理者向け）志望理由書のレビューを行う',
        'statement_view_all': '（管理者向け）全ユーザーの志望理由書を閲覧する',
        # Role Management
        'role_read': 'ロール情報を閲覧する',
        'role_create': '新しいロールを作成する',
        'role_update': '既存のロール情報を更新する',
        'role_delete': 'ロールを削除する',
        'role_permission_assign': 'ロールに対して権限を割り当てる/解除する',
        # Permission Management
        'permission_read': '権限情報を閲覧する',
        'permission_create': '新しい権限を作成する',
        'permission_update': '既存の権限情報を更新する',
        'permission_delete': '権限を削除する',
        # Admin Access
        'admin_access': '管理者機能へのアクセス全般',
        # Stripe Product Management
        'stripe_product_read': 'Stripe 商品情報を閲覧する',
        'stripe_product_write': 'Stripe 商品情報を作成・更新・アーカイブする',
        # Stripe Price Management
        'stripe_price_read': 'Stripe 価格情報を閲覧する',
        'stripe_price_write': 'Stripe 価格情報を作成・更新・アーカイブする',
        # Campaign Code Management
        'campaign_code_read': 'キャンペーンコード情報を閲覧する',
        'campaign_code_write': 'キャンペーンコードを作成・削除する',
        # Discount Type Management
        'discount_type_read': '割引タイプ情報を閲覧する',
        'discount_type_write': '割引タイプを作成・更新・削除する',
        # Study Plan Management
        'study_plan_read': '学習計画を閲覧する',
        'study_plan_write': '学習計画を作成・更新・削除する',
        # Communication Management
        'communication_read': '会話やメッセージを閲覧する',
        'communication_write': '会話を開始したりメッセージを送信する',
        # Application Management
        'application_read': '出願情報を閲覧する',
        'application_write': '出願情報を作成・更新・削除する',
        # ★注意: ここに teacher_perms や free_perms で使われている権限が全て含まれているか確認が必要
        # 例: 'user_read', 'content_read', 'subscription_read_own' などが含まれていない可能性
        # 必要に応じて、これらの権限も上記 all_permissions_data に追加する
         'user_read': 'ユーザー情報を閲覧する', # 例: 追加が必要な場合
         'content_read': 'コンテンツを閲覧する', # 例: 追加が必要な場合
         'content_write': 'コンテンツを作成・編集する', # 例: 追加が必要な場合
         'subscription_read_own': '自身のサブスクリプション情報を閲覧する', # 例: 追加が必要な場合
         'payment_history_read_own': '自身の支払い履歴を閲覧する', # 例: 追加が必要な場合
         'invoice_read_own': '自身の請求書情報を閲覧する', # 例: 追加が必要な場合
         'learning_path_read': '学習パスを閲覧する', # 例: 追加が必要な場合
         'quiz_attempt': 'クイズに挑戦する', # 例: 追加が必要な場合
         'forum_read': 'フォーラムを閲覧する', # 例: 追加が必要な場合
         'forum_post': 'フォーラムに投稿する', # 例: 追加が必要な場合
         'subscription_manage_own': '自身のサブスクリプションを管理する', # 例: 追加が必要な場合

    }

    # 権限をデータベースに追加
    permissions = {}
    for name, description in all_permissions_data.items():
        perm = db.query(Permission).filter(Permission.name == name).first()
        if not perm:
            perm = Permission(id=uuid.uuid4(), name=name, description=description)
            db.add(perm)
        permissions[name] = perm
    db.flush() # Flush after adding all permissions

    # ★修正: DBから権限を再取得して、IDが確定したオブジェクトを使用する
    permissions = {p.name: p for p in db.query(Permission).all()}

    # ========= ロールと権限の関連付け =========
    def add_perm(role_name, perm_name):
        role = roles.get(role_name) # Get role from dictionary
        perm = permissions.get(perm_name)
        if not role or not perm:
            # ★重要: 警告が出続ける場合、ここの perm_name が all_permissions_data に存在するか再確認
            print(f"警告: ロール '{role_name}' または権限 '{perm_name}' が見つかりません。スキップします。")
            return
        # 既存の関連付けをチェック
        existing_rp = db.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == perm.id
        ).first()
        if not existing_rp:
            rp = RolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)

    # 管理者への権限付与 (すべての権限を付与)
    all_permission_names = list(permissions.keys())
    for perm_name in all_permission_names:
        add_perm("管理者", perm_name)

    # 教員への権限付与 (リストで指定)
    # ★注意: このリスト内の権限名が上記の all_permissions_data に存在するか確認
    teacher_perms = [
        "user_read", "content_read", "content_write",
        "community_read", "community_post_create", "community_post_delete_own",
        "chat_session_read", "chat_message_send",
        "desired_school_manage_own",
        "statement_review_request", "statement_review_respond",
        "study_plan_read",
        "communication_read", "communication_write",
        "application_read", "application_write",
        "permission_read", # Read permissions
        "role_read",       # Read roles
    ]
    for perm_name in teacher_perms:
        add_perm("教員", perm_name)

    # --- 新しいロールへの権限割り当て --- 
    # フリープランの権限
    # ★注意: このリスト内の権限名が上記の all_permissions_data に存在するか確認
    free_perms = [
        "content_read",
        "community_read",
        "chat_session_read",
        "chat_message_send",
        "subscription_read_own",
        "payment_history_read_own",
        "invoice_read_own",
        "learning_path_read",
        "quiz_attempt",
        "forum_read",
    ]
    for perm_name in free_perms:
        add_perm("フリー", perm_name)

    # スタンダードプランの権限 (フリー + 追加権限)
    # ★注意: このリスト内の権限名が上記の all_permissions_data に存在するか確認
    standard_perms = free_perms + [
        "community_post_create",
        "community_post_delete_own",
        "study_plan_read",
        "study_plan_write",
        "communication_read",
        "communication_write",
        "forum_post",
        "subscription_manage_own",
    ]
    for perm_name in standard_perms:
        add_perm("スタンダード", perm_name)

    # プレミアムプランの権限 (スタンダード + 追加権限)
    # ★注意: このリスト内の権限名が上記の all_permissions_data に存在するか確認
    premium_perms = standard_perms + [
        "desired_school_manage_own",
        "statement_review_request",
        "application_read",
        "application_write",
    ]
    for perm_name in premium_perms:
        add_perm("プレミアム", perm_name)
    # --- ここまで --- 

    # システムロールへの権限付与 (必要に応じて)
    # system_perms = [ ... ]
    # for perm_name in system_perms: add_perm("システム", perm_name)

    db.flush() # RolePermission の変更を反映

    # ========= ユーザーデータ =========
    users_data = [
        ("admin@demo-univ.ac.jp", get_password_hash("admin123"), "管理者 テスト", roles["管理者"]),
        ("teacher@demo-high.ed.jp", get_password_hash("teacher123"), "教員 テスト", roles["教員"]),
        ("student@example.com", get_password_hash("student123"), "フリーユーザー テスト", roles["フリー"]),
        ("test@example.com", get_password_hash("test123"), "テストユーザー", roles["フリー"]),
        ("ai-system@example.com", get_password_hash("aiSystem@123"), "AIシステム", roles["システム"]),
    ]
    users = []
    for email, pwd, name, role_obj in users_data:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=email,
            hashed_password=pwd,
            full_name=name,
            is_active=True,
            is_verified=True, # Demo data: assume verified
            status=UserStatus.ACTIVE # Set status to ACTIVE
        )
        users.append(user)
        db.add(user)
        db.flush()

        # UserRole の作成と割り当て
        user_role = UserRole(id=uuid.uuid4(), user_id=user_id, role_id=role_obj.id, is_primary=True)
        db.add(user_role)
        db.flush()

        assignment = UserRoleAssignment(id=uuid.uuid4(), user_role_id=user_role.id, assigned_at=datetime.utcnow())
        db.add(assignment)
    db.flush()

    # ========= ユーザープロフィールなど (既存のロジックを維持) =========
    # ... (User Profile, Login Info, Email Verification, Contact Info logic) ...

    return users # Return the list of created user objects

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
            status=SessionStatus.ACTIVE,
            last_message_at=datetime.utcnow() - timedelta(hours=2)
        ),
        ChatSession(
            id=uuid.uuid4(),
            user_id=student.id,
            title="志望理由書の添削依頼",
            status=SessionStatus.ACTIVE,
            last_message_at=datetime.utcnow() - timedelta(days=1)
        ),
        ChatSession(
            id=uuid.uuid4(),
            user_id=student.id,
            title="数学の質問",
            status=SessionStatus.CLOSED,
            last_message_at=datetime.utcnow() - timedelta(days=3)
        )
    ]
    for session in chat_sessions:
        db.add(session)
    db.flush()
    
    # ========= チャットメッセージ =========
    # 第1セッションのメッセージ
    messages_session1 = [
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="デモ大学の総合型選抜について教えてください。"
        ),
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="デモ大学の総合型選抜では、書類審査と面接が行われます。書類には志望理由書とポートフォリオの提出が必要です。面接は約20分間で、あなたの学習意欲や将来の目標について質問されます。"
        ),
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="ポートフォリオには何を入れればいいですか？"
        ),
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="ポートフォリオには、あなたのこれまでの活動や成果物をまとめます。例えば、研究プロジェクト、課外活動、受賞歴、資格などです。特に情報工学科を志望する場合は、プログラミングの経験やIT関連の活動を強調するとよいでしょう。"
        ),
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="ありがとうございます。面接対策はどうすればいいですか？"
        ),
        ChatMessage(
            session_id=chat_sessions[0].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="面接対策としては以下の準備をおすすめします：\\n1. 志望理由を明確に説明できるようにする\\n2. 自分の強みや特技を具体的なエピソードと共に準備する\\n3. 大学の特色や学部の研究内容について調べておく\\n4. 想定質問に対する回答を練習する\\n5. 質問も数個用意しておく\\n\\n模擬面接を行うことも効果的です。面接直前にはリラックスして自信を持って臨みましょう。"
        )
    ]
    
    # 第2セッションのメッセージ
    messages_session2 = [
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="志望理由書を添削してもらえませんか？"
        ),
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="はい、喜んで添削します。志望理由書をアップロードしてください。"
        ),
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="志望理由書_工学部情報工学科.pdf"
        ),
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="志望理由書を拝見しました。全体的に良く書けていますが、いくつか改善点があります：\\n\\n1. 冒頭部分：もう少し印象的な導入ができるとよいでしょう\\n2. 2段落目：具体的なエピソードをもう少し詳しく書くと説得力が増します\\n3. 最終段落：大学で学びたいことをより具体的に記述するとよいでしょう\\n\\n修正案を作成しました。ご確認ください。"
        ),
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="志望理由書_修正案.pdf"
        ),
        ChatMessage(
            session_id=chat_sessions[1].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="ありがとうございます。修正案を参考に書き直してみます。"
        )
    ]
    
    # 第3セッションのメッセージ
    messages_session3 = [
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="数学の微分方程式について質問があります。"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="微分方程式についてどのような質問ですか？"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="dy/dx + Py = Q の形の1階線形微分方程式の解き方がわかりません。"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="1階線形微分方程式 dy/dx + Py = Q の解法を説明します。\\n\\nこれは積分因子法で解くことができます。\\n\\n1. まず積分因子 μ = exp(∫P dx) を見つけます\\n2. 両辺に μ を掛けると、左辺が d(μy)/dx の形になります\\n3. すなわち d(μy)/dx = μQ となります\\n4. 両辺を積分して μy = ∫μQ dx + C\\n5. 最後に y について解きます: y = (∫μQ dx + C) / μ\\n\\n具体例を挙げると分かりやすいかもしれません。例題を解いてみましょうか？"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="はい、例題をお願いします。"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=ai_user.id,
            sender=MessageSender.AI,
            content="例題: dy/dx + 2xy = x を解いてみましょう。\\n\\nこの場合、P(x) = 2x, Q(x) = x です。\\n\\n1. 積分因子 μ = exp(∫2x dx) = exp(x²)\\n2. 両辺に μ を掛ける: exp(x²) dy/dx + 2x·exp(x²)y = x·exp(x²)\\n3. 左辺は d(exp(x²)y)/dx の形\\n4. よって d(exp(x²)y)/dx = x·exp(x²)\\n5. 両辺を積分: exp(x²)y = ∫x·exp(x²) dx\\n\\n∫x·exp(x²) dx は置換積分で解けます。u = x² とすると du = 2x dx なので、x dx = du/2\\n∫x·exp(x²) dx = ∫exp(u)·du/2 = (1/2)exp(u) + C = (1/2)exp(x²) + C\\n\\n6. よって exp(x²)y = (1/2)exp(x²) + C\\n7. y について解くと: y = 1/2 + C·exp(-x²)\\n\\nこれが求める一般解です。"
        ),
        ChatMessage(
            session_id=chat_sessions[2].id,
            user_id=student.id,
            sender=MessageSender.USER,
            content="わかりました！ありがとうございます。"
        )
    ]
    
    # すべてのメッセージを追加
    all_messages = messages_session1 + messages_session2 + messages_session3
    message_id_map = {} # 添付ファイル用にメッセージIDを保存
    for i, msg in enumerate(all_messages):
        db.add(msg)
        db.flush() # IDを取得するためにflush
        message_id_map[f"msg_{i}"] = msg.id # 例: msg_0, msg_1, ...

    # ========= チャット添付ファイル =========
    # ChatAttachment は message_id を Integer として期待している (モデル定義より)
    # message_id_map から取得したIDを使用

    # 第2セッションのファイル添付（学生からのアップロード - 対応するメッセージIDを取得）
    student_upload_msg_index = len(messages_session1) + 2 # messages_session2 の3番目
    student_upload_msg_id = message_id_map.get(f"msg_{student_upload_msg_index}")

    # 第2セッションのファイル添付（AIの修正案 - 対応するメッセージIDを取得）
    ai_upload_msg_index = len(messages_session1) + 4 # messages_session2 の5番目
    ai_upload_msg_id = message_id_map.get(f"msg_{ai_upload_msg_index}")

    if student_upload_msg_id:
        attachment1 = ChatAttachment(
            id=uuid.uuid4(),
            message_id=student_upload_msg_id, # ChatMessage.id (Integer)
            file_url="https://storage.example.com/files/ps_original.pdf",
            file_type="application/pdf",
            file_size=256000,
            file_name="志望理由書_工学部情報工学科.pdf"
        )
        db.add(attachment1)
    else:
        print(f"警告: 添付ファイル1のメッセージIDが見つかりません (Index: {student_upload_msg_index})")


    if ai_upload_msg_id:
        attachment2 = ChatAttachment(
            id=uuid.uuid4(),
            message_id=ai_upload_msg_id, # ChatMessage.id (Integer)
            file_url="https://storage.example.com/files/ps_revised.pdf",
            file_type="application/pdf",
            file_size=280000,
            file_name="志望理由書_修正案.pdf"
        )
        db.add(attachment2)
    else:
        print(f"警告: 添付ファイル2のメッセージIDが見つかりません (Index: {ai_upload_msg_index})")

    db.flush()

    # ========= チェックリスト評価 =========
    checklists = [
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="志望理由の明確さ",
            is_completed=True,
            score=4,
            evaluator_id=None,
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="具体的なエピソード",
            is_completed=True,
            score=3,
            evaluator_id=None,
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="文章構成",
            is_completed=True,
            score=4,
            evaluator_id=None,
            evaluated_at=datetime.utcnow() - timedelta(days=1, hours=4)
        ),
        ChecklistEvaluation(
            id=uuid.uuid4(),
            session_id=chat_sessions[1].id,
            checklist_item="誤字脱字",
            is_completed=True,
            score=5,
            evaluator_id=None,
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
    割引タイプやキャンペーンコードなどのサブスクリプション関連データを挿入します。
    """
    # ========= 割引タイプデータ =========
    print("Seeding discount types...")
    discount_types = {}
    try:
        # 既存のデータをチェックし、なければ追加、辞書に格納
        def get_or_create_discount_type(name, description):
            dt = db.query(DiscountType).filter(DiscountType.name == name).first()
            if not dt:
                dt = DiscountType(id=uuid.uuid4(), name=name, description=description)
                db.add(dt)
                db.flush() # IDを確定させる
                print(f"Added '{name}' discount type.")
            discount_types[name] = dt # 辞書に格納

        get_or_create_discount_type('percentage', '割引率 (%)')
        get_or_create_discount_type('fixed', '固定割引額 (円)')
        get_or_create_discount_type('none', '割引なし')
        get_or_create_discount_type('trial_fixed', 'トライアル固定価格')
        get_or_create_discount_type('trial_percentage', 'トライアル割引率')

        print("Discount types seeding complete.")

    except Exception as e:
        print(f"An error occurred during discount type seeding: {e}")
        db.rollback() # エラー時はロールバック
        return # キャンペーンコード作成に進まない

    # ========= キャンペーンコードデータ (自動作成を無効化) =========
    # print("Seeding campaign codes...")
    # try:
    #     campaign_codes_data = [
    #         {
    #             "code": "WELCOME10",
    #             "description": "新規登録者向け10%割引",
    #             "discount_type_name": "percentage",
    #             "discount_value": 10.0,
    #             "max_uses": 1000,
    #             "valid_until": datetime.utcnow() + timedelta(days=365)
    #         },
    #         {
    #             "code": "SPRING500",
    #             "description": "春のキャンペーン500円引き",
    #             "discount_type_name": "fixed",
    #             "discount_value": 500.0,
    #             "max_uses": 500,
    #             "valid_until": datetime.utcnow() + timedelta(days=90)
    #         },
    #         {
    #             "code": "EXPIREDCODE",
    #             "description": "期限切れテストコード",
    #             "discount_type_name": "percentage",
    #             "discount_value": 5.0,
    #             "max_uses": 10,
    #             "valid_until": datetime.utcnow() - timedelta(days=1) # 期限切れ
    #         },
    #         {
    #             "code": "USEDUPCODE",
    #             "description": "使用上限テストコード",
    #             "discount_type_name": "fixed",
    #             "discount_value": 100.0,
    #             "max_uses": 0, # 使用上限0
    #             "valid_until": datetime.utcnow() + timedelta(days=30)
    #         }
    #     ]
    #
    #     added_codes = False
    #     for data in campaign_codes_data:
    #         # 既存チェック
    #         existing_code = db.query(CampaignCode).filter(CampaignCode.code == data["code"]).first()
    #         if not existing_code:
    #             discount_type = discount_types.get(data["discount_type_name"])
    #             if not discount_type:
    #                 print(f"Warning: Discount type '{data['discount_type_name']}' not found for campaign code '{data['code']}'. Skipping.")
    #                 continue
    #
    #             # モデル定義に合わせて修正が必要 (例: redemption_count が存在しない)
    #             # new_code = CampaignCode(
    #             #     id=uuid.uuid4(),
    #             #     code=data["code"],
    #             #     description=data["description"],
    #             #     discount_type_id=discount_type.id,
    #             #     discount_value=data["discount_value"],
    #             #     max_uses=data["max_uses"],
    #             #     # redemption_count=0, # モデルに存在しない場合コメントアウト
    #             #     used_count=0, # モデルに合わせて修正 (もし used_count があれば)
    #             #     is_active=True,
    #             #     valid_until=data["valid_until"]
    #             # )
    #             # db.add(new_code)
    #             # print(f"Added campaign code: {data['code']}")
    #             added_codes = True
    #
    #     if added_codes:
    #         db.flush()
    #         print("Campaign codes flushed.")
    #     else:
    #         print("All required campaign codes already exist.")
    #
    # except Exception as e:
    #     print(f"An error occurred during campaign code seeding: {e}")
    #     db.rollback() # エラー時はロールバック 