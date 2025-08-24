"""
本番環境用権限・ロール管理システム
バージョン管理された権限定義と安全な適用機能
"""

from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Depends, status

from app.models.user import Role, Permission, RolePermission, User, UserRole
from app.database.database import SessionLocal

logger = logging.getLogger(__name__)


class PermissionVersion(Enum):
    """権限バージョン管理"""
    V1_INITIAL = "v1.0.0"  # 初期権限
    V1_1_SCHOOL_TENANT = "v1.1.0"  # 学校テナント機能
    V1_2_ADVANCED_FEATURES = "v1.2.0"  # 将来の機能拡張用


@dataclass
class PermissionDefinition:
    """権限定義"""
    name: str
    description: str
    version: PermissionVersion


@dataclass
class RoleDefinition:
    """ロール定義"""
    name: str
    description: str
    permissions: List[str]
    version: PermissionVersion


class PermissionRegistry:
    """権限・ロールレジストリ"""
    
    # 全権限定義
    PERMISSIONS: Dict[str, PermissionDefinition] = {
        # === V1.0.0 初期権限 ===
        'community_read': PermissionDefinition(
            'community_read', 'コミュニティ投稿を閲覧する', PermissionVersion.V1_INITIAL
        ),
        'community_post_create': PermissionDefinition(
            'community_post_create', 'コミュニティ投稿を作成する', PermissionVersion.V1_INITIAL
        ),
        'chat_session_read': PermissionDefinition(
            'chat_session_read', 'チャットセッションを閲覧する', PermissionVersion.V1_INITIAL
        ),
        'chat_message_send': PermissionDefinition(
            'chat_message_send', 'チャットメッセージを送信する', PermissionVersion.V1_INITIAL
        ),
        'statement_manage_own': PermissionDefinition(
            'statement_manage_own', '自分の志望理由書を管理する', PermissionVersion.V1_INITIAL
        ),
        'statement_review_respond': PermissionDefinition(
            'statement_review_respond', '志望理由書のレビューを行う', PermissionVersion.V1_INITIAL
        ),
        'admin_access': PermissionDefinition(
            'admin_access', '管理者機能へのアクセス全般', PermissionVersion.V1_INITIAL
        ),
        'user_read': PermissionDefinition(
            'user_read', 'ユーザー情報を閲覧する', PermissionVersion.V1_INITIAL
        ),
        'content_read': PermissionDefinition(
            'content_read', 'コンテンツを閲覧する', PermissionVersion.V1_INITIAL
        ),
        'content_write': PermissionDefinition(
            'content_write', 'コンテンツを作成・編集する', PermissionVersion.V1_INITIAL
        ),
        
        # === V1.1.0 学校テナント機能 ===
        'school_manage_users': PermissionDefinition(
            'school_manage_users', '学校内のユーザーを管理する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_view_all_students': PermissionDefinition(
            'school_view_all_students', '学校内の全生徒情報を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_view_all_teachers': PermissionDefinition(
            'school_view_all_teachers', '学校内の全先生情報を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_manage_settings': PermissionDefinition(
            'school_manage_settings', '学校の設定を管理する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_view_analytics': PermissionDefinition(
            'school_view_analytics', '学校の統計・分析を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_manage_assignments': PermissionDefinition(
            'school_manage_assignments', '先生と生徒の担当関係を管理する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'school_admin_access': PermissionDefinition(
            'school_admin_access', '学校管理機能へのアクセス', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'teacher_view_assigned_students': PermissionDefinition(
            'teacher_view_assigned_students', '担当生徒の情報を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'teacher_view_student_chat': PermissionDefinition(
            'teacher_view_student_chat', '担当生徒のチャット履歴を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'teacher_view_student_statements': PermissionDefinition(
            'teacher_view_student_statements', '担当生徒の志望理由書を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        'teacher_view_student_schools': PermissionDefinition(
            'teacher_view_student_schools', '担当生徒の志望校情報を閲覧する', PermissionVersion.V1_1_SCHOOL_TENANT
        ),
    }
    
    # 全ロール定義
    ROLES: Dict[str, RoleDefinition] = {
        '管理者': RoleDefinition(
            '管理者', 'システム管理者', 
            list(PERMISSIONS.keys()), # 全権限
            PermissionVersion.V1_INITIAL
        ),
        '学校管理者': RoleDefinition(
            '学校管理者', '学校レベル管理者',
            [
                'user_read', 'content_read', 'content_write',
                'community_read', 'community_post_create',
                'chat_session_read', 'chat_message_send',
                'statement_manage_own', 'statement_review_respond',
                'school_manage_users', 'school_view_all_students', 'school_view_all_teachers',
                'school_manage_settings', 'school_view_analytics', 'school_manage_assignments',
                'school_admin_access',
            ],
            PermissionVersion.V1_1_SCHOOL_TENANT
        ),
        '教員': RoleDefinition(
            '教員', '高校教員',
            [
                'user_read', 'content_read', 'content_write',
                'community_read', 'community_post_create',
                'chat_session_read', 'chat_message_send',
                'statement_manage_own', 'statement_review_respond',
                'teacher_view_assigned_students', 'teacher_view_student_chat',
                'teacher_view_student_statements', 'teacher_view_student_schools',
            ],
            PermissionVersion.V1_1_SCHOOL_TENANT
        ),
    }
    
    @classmethod
    def get_permissions_by_version(cls, version: PermissionVersion) -> Dict[str, PermissionDefinition]:
        """指定バージョンの権限を取得"""
        return {k: v for k, v in cls.PERMISSIONS.items() if v.version == version}
    
    @classmethod
    def get_roles_by_version(cls, version: PermissionVersion) -> Dict[str, RoleDefinition]:
        """指定バージョンのロールを取得"""
        return {k: v for k, v in cls.ROLES.items() if v.version == version}


class PermissionChecker:
    """権限チェック機能"""
    
    @staticmethod
    def get_user_permissions(db: Session, user: User) -> Set[str]:
        """ユーザーの権限一覧を取得"""
        try:
            # ユーザーのロールを取得
            user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
            
            permissions = set()
            for user_role in user_roles:
                # ロールの権限を取得
                role_permissions = db.query(RolePermission).filter(
                    RolePermission.role_id == user_role.role_id
                ).all()
                
                for role_perm in role_permissions:
                    permission = db.query(Permission).filter(
                        Permission.id == role_perm.permission_id
                    ).first()
                    if permission:
                        permissions.add(permission.name)
            
            return permissions
            
        except Exception as e:
            logger.error(f"権限取得エラー: {e}")
            return set()
    
    @staticmethod
    def check_permissions(db: Session, user: User, required_permissions: List[str]) -> bool:
        """ユーザーが必要な権限を持っているかチェック"""
        try:
            user_permissions = PermissionChecker.get_user_permissions(db, user)
            
            # システム管理者は全権限を持つ
            if 'admin_access' in user_permissions:
                return True
            
            # 必要な権限をすべて持っているかチェック
            return all(perm in user_permissions for perm in required_permissions)
            
        except Exception as e:
            logger.error(f"権限チェックエラー: {e}")
            return False


def require_permissions(required_permissions: List[str]):
    """
    APIエンドポイント用の権限チェックデコレーター
    
    使用例:
    @router.get("/admin-only")
    @require_permissions(["admin_access"])
    async def admin_endpoint():
        return {"message": "管理者専用"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # FastAPIの依存関係からDBセッションとユーザーを取得
            db = None
            current_user = None
            
            # 引数からDBセッションとユーザーを取得
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, User):
                    current_user = value
            
            if not db or not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="権限チェックに必要な情報が不足しています"
                )
            
            # 権限チェック実行
            if not PermissionChecker.check_permissions(db, current_user, required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="この機能を利用する権限がありません"
                )
            
            # 権限チェックを通過した場合、元の関数を実行
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class PermissionMigrator:
    """権限・ロールマイグレーター"""
    
    def __init__(self, db: Session):
        self.db = db
        self.registry = PermissionRegistry()
    
    def get_current_version(self) -> Optional[PermissionVersion]:
        """現在適用されている権限バージョンを取得"""
        # 学校テナント権限があるかチェック
        school_permission = self.db.query(Permission).filter(
            Permission.name == 'school_admin_access'
        ).first()
        
        if school_permission:
            return PermissionVersion.V1_1_SCHOOL_TENANT
        
        # 基本権限があるかチェック  
        admin_permission = self.db.query(Permission).filter(
            Permission.name == 'admin_access'
        ).first()
        
        if admin_permission:
            return PermissionVersion.V1_INITIAL
        
        return None
    
    def apply_permissions(self, version: PermissionVersion, dry_run: bool = False) -> Dict[str, any]:
        """指定バージョンの権限を適用"""
        logger.info(f"権限適用開始: {version.value} (dry_run={dry_run})")
        
        permissions_to_add = self.registry.get_permissions_by_version(version)
        result = {
            'version': version.value,
            'permissions_added': 0,
            'permissions_skipped': 0,
            'errors': []
        }
        
        for perm_name, perm_def in permissions_to_add.items():
            try:
                existing_perm = self.db.query(Permission).filter(
                    Permission.name == perm_name
                ).first()
                
                if existing_perm:
                    result['permissions_skipped'] += 1
                    logger.info(f"権限 '{perm_name}' は既に存在します")
                    continue
                
                if not dry_run:
                    new_perm = Permission(
                        name=perm_def.name,
                        description=perm_def.description
                    )
                    self.db.add(new_perm)
                    self.db.flush()
                
                result['permissions_added'] += 1
                logger.info(f"権限 '{perm_name}' を追加しました")
                
            except Exception as e:
                error_msg = f"権限 '{perm_name}' の追加でエラー: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
        
        if not dry_run:
            try:
                self.db.commit()
                logger.info("権限の適用を完了しました")
            except Exception as e:
                self.db.rollback()
                error_msg = f"コミットエラー: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
                raise
        
        return result
    
    def apply_roles(self, version: PermissionVersion, dry_run: bool = False) -> Dict[str, any]:
        """指定バージョンのロールを適用"""
        logger.info(f"ロール適用開始: {version.value} (dry_run={dry_run})")
        
        roles_to_add = self.registry.get_roles_by_version(version)
        result = {
            'version': version.value,
            'roles_added': 0,
            'roles_updated': 0,
            'permissions_assigned': 0,
            'errors': []
        }
        
        for role_name, role_def in roles_to_add.items():
            try:
                existing_role = self.db.query(Role).filter(
                    Role.name == role_name
                ).first()
                
                if not existing_role:
                    if not dry_run:
                        new_role = Role(
                            name=role_def.name,
                            description=role_def.description,
                            is_active=True
                        )
                        self.db.add(new_role)
                        self.db.flush()
                        existing_role = new_role
                    
                    result['roles_added'] += 1
                    logger.info(f"ロール '{role_name}' を追加しました")
                else:
                    result['roles_updated'] += 1
                    logger.info(f"ロール '{role_name}' は既に存在します")
                
                # 権限の割り当て
                if not dry_run and existing_role:
                    assigned_perms = self._assign_role_permissions(existing_role, role_def.permissions)
                    result['permissions_assigned'] += assigned_perms
                
            except Exception as e:
                error_msg = f"ロール '{role_name}' の処理でエラー: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
        
        if not dry_run:
            try:
                self.db.commit()
                logger.info("ロールの適用を完了しました")
            except Exception as e:
                self.db.rollback()
                error_msg = f"コミットエラー: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
                raise
        
        return result
    
    def _assign_role_permissions(self, role: Role, permission_names: List[str]) -> int:
        """ロールに権限を割り当て"""
        assigned_count = 0
        
        for perm_name in permission_names:
            permission = self.db.query(Permission).filter(
                Permission.name == perm_name
            ).first()
            
            if not permission:
                logger.warning(f"権限 '{perm_name}' が見つかりません")
                continue
            
            # 既存の関連付けをチェック
            existing_rp = self.db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            ).first()
            
            if not existing_rp:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id
                )
                self.db.add(role_perm)
                assigned_count += 1
        
        return assigned_count
    
    def migrate_to_version(self, target_version: PermissionVersion, dry_run: bool = False) -> Dict[str, any]:
        """指定バージョンまでマイグレートする"""
        current_version = self.get_current_version()
        logger.info(f"マイグレーション開始: {current_version} -> {target_version.value}")
        
        result = {
            'current_version': current_version.value if current_version else None,
            'target_version': target_version.value,
            'migrations': [],
            'success': True
        }
        
        try:
            # バージョン順に適用
            versions_to_apply = []
            
            if not current_version:
                versions_to_apply = [PermissionVersion.V1_INITIAL]
            
            if target_version == PermissionVersion.V1_1_SCHOOL_TENANT:
                if current_version != PermissionVersion.V1_1_SCHOOL_TENANT:
                    versions_to_apply.append(PermissionVersion.V1_1_SCHOOL_TENANT)
            
            for version in versions_to_apply:
                logger.info(f"バージョン {version.value} を適用中...")
                
                # 権限を適用
                perm_result = self.apply_permissions(version, dry_run)
                result['migrations'].append(f"権限: {perm_result}")
                
                # ロールを適用
                role_result = self.apply_roles(version, dry_run)
                result['migrations'].append(f"ロール: {role_result}")
                
                logger.info(f"バージョン {version.value} の適用完了")
        
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            logger.error(f"マイグレーションエラー: {e}")
            raise
        
        return result


def migrate_permissions_to_latest(dry_run: bool = True) -> Dict[str, any]:
    """最新バージョンまで権限をマイグレート"""
    db = SessionLocal()
    try:
        migrator = PermissionMigrator(db)
        return migrator.migrate_to_version(PermissionVersion.V1_1_SCHOOL_TENANT, dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    
    print("=== DRY RUN ===")
    dry_result = migrate_permissions_to_latest(dry_run=True)
    print(f"Dry run結果: {dry_result}")
    
    # 実際の適用はコメントアウト
    # print("\n=== ACTUAL MIGRATION ===")
    # actual_result = migrate_permissions_to_latest(dry_run=False)
    # print(f"実際の適用結果: {actual_result}")