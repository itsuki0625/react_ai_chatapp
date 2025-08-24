#!/usr/bin/env python3
"""
学校テナント機能用の増分データ更新スクリプト
既存のデータを保持しつつ、新しいロール、権限、ユーザーを追加する
"""

import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, Role, Permission, RolePermission, UserRole, UserRoleAssignment
from app.models.school import School
from app.models.teacher_student import TeacherStudentAssignment, SchoolSettings, SchoolAdminSettings
from app.models.enums import UserStatus, AssignmentType

logger = logging.getLogger(__name__)

def update_tenant_data():
    """学校テナント機能用のデータを既存データベースに追加"""
    db = SessionLocal()
    try:
        print("🏫 学校テナント機能用データの更新を開始します...")
        
        # 1. 学校管理者ロールを追加
        school_admin_role = add_school_admin_role(db)
        
        # 2. 新しい権限を追加
        add_tenant_permissions(db)
        
        # 3. 学校管理者と教員に新しい権限を付与
        assign_tenant_permissions(db, school_admin_role)
        
        # 4. 学校設定を追加
        add_school_settings(db)
        
        # 5. テストユーザーを追加
        add_tenant_users(db, school_admin_role)
        
        # 6. 先生・生徒の担当関係を追加
        add_teacher_student_assignments(db)
        
        db.commit()
        print("✅ 学校テナント機能用データの更新が完了しました！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {e}")
        logger.error(f"データ更新エラー: {e}", exc_info=True)
        raise
    finally:
        db.close()

def add_school_admin_role(db: Session) -> Role:
    """学校管理者ロールを追加"""
    print("📝 学校管理者ロールを追加中...")
    
    # 既存チェック
    existing_role = db.query(Role).filter(Role.name == "学校管理者").first()
    if existing_role:
        print("   ℹ️  学校管理者ロールは既に存在します")
        return existing_role
    
    # 新しいロールを作成
    school_admin_role = Role(
        id=uuid.uuid4(),
        name="学校管理者",
        description="学校レベル管理者",
        is_active=True
    )
    db.add(school_admin_role)
    db.flush()
    print("   ✅ 学校管理者ロールを追加しました")
    return school_admin_role

def add_tenant_permissions(db: Session):
    """テナント機能用の権限を追加"""
    print("🔐 テナント機能用権限を追加中...")
    
    tenant_permissions = {
        # School Tenant Management (学校テナント管理)
        'school_manage_users': '学校内のユーザーを管理する',
        'school_view_all_students': '学校内の全生徒情報を閲覧する',
        'school_view_all_teachers': '学校内の全先生情報を閲覧する',
        'school_manage_settings': '学校の設定を管理する',
        'school_view_analytics': '学校の統計・分析を閲覧する',
        'school_manage_assignments': '先生と生徒の担当関係を管理する',
        'school_admin_access': '学校管理機能へのアクセス',
        
        # Teacher-Student Management (先生・生徒管理)
        'teacher_view_assigned_students': '担当生徒の情報を閲覧する',
        'teacher_view_student_chat': '担当生徒のチャット履歴を閲覧する',
        'teacher_view_student_statements': '担当生徒の志望理由書を閲覧する',
        'teacher_view_student_schools': '担当生徒の志望校情報を閲覧する',
        'teacher_manage_student_assignments': '生徒の担当関係を管理する',
    }
    
    added_count = 0
    for name, description in tenant_permissions.items():
        existing_perm = db.query(Permission).filter(Permission.name == name).first()
        if not existing_perm:
            perm = Permission(
                id=uuid.uuid4(),
                name=name,
                description=description
            )
            db.add(perm)
            added_count += 1
    
    db.flush()
    print(f"   ✅ {added_count}個の新しい権限を追加しました")

def assign_tenant_permissions(db: Session, school_admin_role: Role):
    """学校管理者と教員にテナント機能権限を付与"""
    print("👤 ロールに権限を付与中...")
    
    # 学校管理者権限
    school_admin_perms = [
        "user_read", "content_read", "content_write",
        "community_read", "community_post_create", "community_post_delete_own",
        "chat_session_read", "chat_message_send",
        "desired_school_manage_own", "desired_school_view_all",
        "statement_review_request", "statement_review_respond", "statement_view_all",
        "study_plan_read", "communication_read", "communication_write",
        "application_read", "application_write",
        "permission_read", "role_read",
        # 学校テナント管理権限
        "school_manage_users", "school_view_all_students", "school_view_all_teachers",
        "school_manage_settings", "school_view_analytics", "school_manage_assignments",
        "school_admin_access",
    ]
    
    # 教員追加権限
    teacher_additional_perms = [
        "teacher_view_assigned_students", "teacher_view_student_chat",
        "teacher_view_student_statements", "teacher_view_student_schools",
    ]
    
    def assign_perms(role_name: str, perm_names: list):
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"   ⚠️  ロール '{role_name}' が見つかりません")
            return
        
        assigned_count = 0
        for perm_name in perm_names:
            perm = db.query(Permission).filter(Permission.name == perm_name).first()
            if not perm:
                continue
            
            # 既存の関連付けをチェック
            existing_rp = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id
            ).first()
            
            if not existing_rp:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                db.add(rp)
                assigned_count += 1
        
        print(f"   ✅ {role_name}に{assigned_count}個の権限を付与しました")
    
    assign_perms("学校管理者", school_admin_perms)
    assign_perms("教員", teacher_additional_perms)
    db.flush()

def add_school_settings(db: Session):
    """学校設定を追加"""
    print("⚙️  学校設定を追加中...")
    
    # デモ学校を取得
    demo_school = db.query(School).filter(School.name == "デモ高校").first()
    if not demo_school:
        print("   ⚠️  デモ学校が見つかりません。スキップします。")
        return
    
    # 学校設定を追加
    existing_settings = db.query(SchoolSettings).filter(
        SchoolSettings.school_id == demo_school.id
    ).first()
    
    if not existing_settings:
        school_settings = SchoolSettings(
            id=uuid.uuid4(),
            school_id=demo_school.id,
            allow_student_chat=True,
            require_statement_approval=True,
            enable_analytics=True,
            enable_teacher_student_assignment=True,
            primary_color="#3B82F6",
            secondary_color="#10B981",
            accent_color="#F59E0B",
            email_notifications_enabled=True,
            push_notifications_enabled=True,
            digest_frequency="weekly"
        )
        db.add(school_settings)
        print("   ✅ 学校設定を追加しました")
    else:
        print("   ℹ️  学校設定は既に存在します")
    
    # 学校管理者設定を追加（学校管理者ユーザーがいる場合のみ）
    school_admin_users = db.query(User).join(UserRole).join(Role).filter(
        User.school_id == demo_school.id,
        Role.name == "学校管理者"
    ).all()
    
    for admin_user in school_admin_users:
        existing_admin_settings = db.query(SchoolAdminSettings).filter(
            SchoolAdminSettings.user_id == admin_user.id,
            SchoolAdminSettings.school_id == demo_school.id
        ).first()
        
        if not existing_admin_settings:
            admin_settings = SchoolAdminSettings(
                id=uuid.uuid4(),
                user_id=admin_user.id,
                school_id=demo_school.id,
                permission_level="full",
                notification_settings='{"email": true, "push": true}',
                dashboard_preferences='{"theme": "light", "layout": "default"}'
            )
            db.add(admin_settings)
            print(f"   ✅ {admin_user.full_name} の学校管理者設定を追加しました")
        else:
            print(f"   ℹ️  {admin_user.full_name} の学校管理者設定は既に存在します")
    
    db.flush()

def add_tenant_users(db: Session, school_admin_role: Role):
    """テナント機能用テストユーザーを追加"""
    print("👥 テストユーザーを追加中...")
    
    # デモ学校を取得
    demo_school = db.query(School).filter(School.name == "デモ高校").first()
    if not demo_school:
        print("   ⚠️  デモ学校が見つかりません。")
        return
    
    # 教員ロール、スタンダードロール、プレミアムロールを取得
    teacher_role = db.query(Role).filter(Role.name == "教員").first()
    standard_role = db.query(Role).filter(Role.name == "スタンダード").first()
    premium_role = db.query(Role).filter(Role.name == "プレミアム").first()
    
    # 追加するユーザー定義
    users_to_add = [
        ("school-admin@demo-high.ed.jp", "schooladmin123", "学校管理者 テスト", school_admin_role),
        ("teacher2@demo-high.ed.jp", "teacher123", "教員2 テスト", teacher_role),
        ("student2@example.com", "student123", "生徒2 テスト", standard_role),
        ("student3@example.com", "student123", "生徒3 テスト", premium_role),
    ]
    
    added_count = 0
    added_users = []
    
    for email, password, full_name, role in users_to_add:
        if not role:
            continue
            
        # 既存ユーザーチェック
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"   ℹ️  ユーザー {email} は既に存在します")
            added_users.append(existing_user)
            continue
        
        # 新しいユーザーを作成
        try:
            user_id = uuid.uuid4()
            user = User(
                id=user_id,
                email=email,
                hashed_password=get_password_hash(password),
                full_name=full_name,
                is_active=True,
                is_verified=True,
                status=UserStatus.ACTIVE,
                school_id=demo_school.id
            )
            db.add(user)
            db.flush()
            
            # UserRoleの作成と割り当て
            user_role = UserRole(
                id=uuid.uuid4(),
                user_id=user_id,
                role_id=role.id,
                is_primary=True
            )
            db.add(user_role)
            db.flush()
            
            assignment = UserRoleAssignment(
                id=uuid.uuid4(),
                user_role_id=user_role.id,
                assigned_at=datetime.utcnow()
            )
            db.add(assignment)
            
            added_users.append(user)
            added_count += 1
            print(f"   ✅ ユーザー {email} を追加しました")
            
        except IntegrityError as e:
            db.rollback()
            print(f"   ❌ ユーザー {email} の追加でエラー: {e}")
            continue
    
    db.flush()
    print(f"   📊 合計 {added_count} 人の新しいユーザーを追加しました")
    return added_users

def add_teacher_student_assignments(db: Session):
    """先生・生徒の担当関係を追加"""
    print("🎓 先生・生徒の担当関係を追加中...")
    
    # 既存の担当関係数を確認
    existing_count = db.query(TeacherStudentAssignment).count()
    if existing_count > 0:
        print(f"   ℹ️  既に {existing_count} 件の担当関係が存在します")
        return
    
    # デモ学校のユーザーを取得
    demo_school = db.query(School).filter(School.name == "デモ高校").first()
    if not demo_school:
        return
    
    # 教員と生徒を取得
    teachers = db.query(User).join(UserRole).join(Role).filter(
        User.school_id == demo_school.id,
        Role.name == "教員"
    ).all()
    
    students = db.query(User).join(UserRole).join(Role).filter(
        User.school_id == demo_school.id,
        Role.name.in_(["フリー", "スタンダード", "プレミアム"])
    ).all()
    
    if len(teachers) < 1 or len(students) < 1:
        print(f"   ⚠️  十分な教員({len(teachers)})または生徒({len(students)})が見つかりません")
        return
    
    # サンプル担当関係を作成
    assignments_data = []
    if len(teachers) >= 1 and len(students) >= 1:
        assignments_data.append((teachers[0], students[0], AssignmentType.PRIMARY, "数学"))
    if len(teachers) >= 1 and len(students) >= 2:
        assignments_data.append((teachers[0], students[1], AssignmentType.PRIMARY, "数学"))
    if len(teachers) >= 2 and len(students) >= 2:
        assignments_data.append((teachers[1], students[1], AssignmentType.SECONDARY, "国語"))
    if len(teachers) >= 2 and len(students) >= 3:
        assignments_data.append((teachers[1], students[2], AssignmentType.PRIMARY, "国語"))
    if len(teachers) >= 1 and len(students) >= 3:
        assignments_data.append((teachers[0], students[2], AssignmentType.SECONDARY, "数学"))
    
    # 割り当て者として管理者ユーザーを取得
    admin_user = db.query(User).join(UserRole).join(Role).filter(
        Role.name == "管理者"
    ).first()
    
    # 管理者が見つからない場合は学校管理者を使用
    if not admin_user:
        admin_user = db.query(User).join(UserRole).join(Role).filter(
            User.school_id == demo_school.id,
            Role.name == "学校管理者"
        ).first()
    
    if not admin_user:
        print("   ⚠️  割り当て者となるユーザーが見つかりません。担当関係の作成をスキップします。")
        return
    
    added_count = 0
    for teacher, student, assignment_type, subject in assignments_data:
        assignment = TeacherStudentAssignment(
            id=uuid.uuid4(),
            teacher_id=teacher.id,
            student_id=student.id,
            school_id=demo_school.id,
            assignment_type=assignment_type,
            subject=subject,
            is_active=True,
            assigned_by=admin_user.id,  # 必須フィールドを設定
            assigned_at=datetime.utcnow()
        )
        db.add(assignment)
        added_count += 1
    
    db.flush()
    print(f"   ✅ {added_count} 件の担当関係を追加しました")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    update_tenant_data()
