#!/usr/bin/env python3
"""
デモデータの存在確認スクリプト
データベース内のデモデータが正しく挿入されているかを確認する
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.database import get_db
from app.models.school import School, SchoolDetails
from app.models.user import User, Role
from app.models.teacher_student import TeacherStudentAssignment, SchoolSettings
from sqlalchemy.orm import joinedload

def main():
    """デモデータの確認メイン関数"""
    print("=" * 60)
    print("🔍 デモデータ確認スクリプト")
    print("=" * 60)
    
    # データベース接続
    try:
        db = next(get_db())
        print("✅ データベース接続成功")
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return
    
    try:
        # 1. 学校データの確認
        print("\n📍 学校データの確認")
        schools = db.query(School).options(
            joinedload(School.details),
            joinedload(School.settings)
        ).all()
        print(f"   学校数: {len(schools)}")
        
        if schools:
            for school in schools:
                print(f"   - {school.name} (コード: {school.school_code}, アクティブ: {school.is_active})")
                if school.details:
                    print(f"     住所: {school.details.prefecture} {school.details.city}")
                if school.settings:
                    print(f"     設定: チャット={school.settings.allow_student_chat}, 分析={school.settings.enable_analytics}")
        else:
            print("   ⚠️  学校データが見つかりません")
        
        # 2. ユーザーデータの確認
        print("\n👤 ユーザーデータの確認")
        users = db.query(User).options(joinedload(User.roles)).all()
        print(f"   ユーザー数: {len(users)}")
        
        if users:
            for user in users:
                roles = [role.role.name for role in user.roles] if user.roles else []
                school_name = "システム" if not user.school_id else "学校所属"
                print(f"   - {user.full_name} ({user.email}) - ロール: {', '.join(roles)} - {school_name}")
        else:
            print("   ⚠️  ユーザーデータが見つかりません")
        
        # 3. ロールの確認
        print("\n🔐 ロールデータの確認")
        roles = db.query(Role).all()
        print(f"   ロール数: {len(roles)}")
        
        if roles:
            for role in roles:
                print(f"   - {role.name}: {role.description}")
        else:
            print("   ⚠️  ロールデータが見つかりません")
        
        # 4. 担当関係の確認
        print("\n👥 担当関係データの確認")
        assignments = db.query(TeacherStudentAssignment).options(
            joinedload(TeacherStudentAssignment.teacher),
            joinedload(TeacherStudentAssignment.student)
        ).all()
        print(f"   担当関係数: {len(assignments)}")
        
        if assignments:
            for assignment in assignments:
                teacher_name = assignment.teacher.full_name if assignment.teacher else "不明"
                student_name = assignment.student.full_name if assignment.student else "不明"
                print(f"   - {teacher_name} → {student_name} ({assignment.assignment_type.value if assignment.assignment_type else '不明'}) - 科目: {assignment.subject}")
        else:
            print("   ⚠️  担当関係データが見つかりません")
        
        # 5. システム管理者の確認
        print("\n🔧 システム管理者の確認")
        admin_users = db.query(User).join(User.roles).join(Role).filter(
            Role.name == "管理者"
        ).all()
        print(f"   管理者数: {len(admin_users)}")
        
        if admin_users:
            for admin in admin_users:
                print(f"   - {admin.full_name} ({admin.email})")
        else:
            print("   ⚠️  システム管理者が見つかりません")
            
        print("\n" + "=" * 60)
        print("✅ デモデータ確認完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ データ確認中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
