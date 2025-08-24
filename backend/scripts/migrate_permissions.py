#!/usr/bin/env python3
"""
本番環境用権限・ロールマイグレーションCLI
安全な権限適用とロールバック機能を提供
"""

import argparse
import logging
import json
import sys
from datetime import datetime
from pathlib import Path

from app.core.permissions import PermissionMigrator, PermissionVersion, migrate_permissions_to_latest
from app.database.database import SessionLocal


def setup_logging(verbose: bool = False):
    """ログ設定"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('permission_migration.log')
        ]
    )


def check_environment():
    """環境チェック"""
    print("🔍 環境チェック中...")
    
    # データベース接続チェック
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ データベース接続: OK")
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return False
    
    # 既存データチェック
    try:
        db = SessionLocal()
        migrator = PermissionMigrator(db)
        current_version = migrator.get_current_version()
        
        if current_version:
            print(f"📋 現在のバージョン: {current_version.value}")
        else:
            print("📋 現在のバージョン: 未適用")
        
        db.close()
        print("✅ 権限システムチェック: OK")
        return True
    except Exception as e:
        print(f"❌ 権限システムチェックエラー: {e}")
        return False


def backup_current_permissions():
    """現在の権限設定をバックアップ"""
    print("💾 現在の権限設定をバックアップ中...")
    
    try:
        db = SessionLocal()
        
        # 現在の権限とロールを取得
        from app.models.user import Role, Permission, RolePermission
        
        roles = db.query(Role).all()
        permissions = db.query(Permission).all()
        role_permissions = db.query(RolePermission).all()
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'roles': [
                {
                    'id': str(role.id),
                    'name': role.name,
                    'description': role.description,
                    'is_active': role.is_active
                }
                for role in roles
            ],
            'permissions': [
                {
                    'id': str(perm.id),
                    'name': perm.name,
                    'description': perm.description
                }
                for perm in permissions
            ],
            'role_permissions': [
                {
                    'role_id': str(rp.role_id),
                    'permission_id': str(rp.permission_id)
                }
                for rp in role_permissions
            ]
        }
        
        # バックアップファイルを保存
        backup_file = f"permission_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        db.close()
        print(f"✅ バックアップ完了: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"❌ バックアップエラー: {e}")
        return None


def dry_run_migration(target_version: str = None):
    """ドライラン実行"""
    print("🧪 ドライラン実行中...")
    
    try:
        if target_version:
            version = PermissionVersion(target_version)
            db = SessionLocal()
            migrator = PermissionMigrator(db)
            result = migrator.migrate_to_version(version, dry_run=True)
            db.close()
        else:
            result = migrate_permissions_to_latest(dry_run=True)
        
        print("📊 ドライラン結果:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return result
        
    except Exception as e:
        print(f"❌ ドライランエラー: {e}")
        return None


def apply_migration(target_version: str = None, backup_file: str = None):
    """実際のマイグレーション適用"""
    print("🚀 マイグレーション適用中...")
    
    try:
        if target_version:
            version = PermissionVersion(target_version)
            db = SessionLocal()
            migrator = PermissionMigrator(db)
            result = migrator.migrate_to_version(version, dry_run=False)
            db.close()
        else:
            result = migrate_permissions_to_latest(dry_run=False)
        
        if result['success']:
            print("✅ マイグレーション完了!")
            print("📊 適用結果:")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
            
            # 適用ログを保存
            log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            migration_log = {
                'timestamp': datetime.now().isoformat(),
                'backup_file': backup_file,
                'result': result
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(migration_log, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📝 マイグレーションログ保存: {log_file}")
        else:
            print(f"❌ マイグレーションエラー: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ マイグレーション適用エラー: {e}")
        return False


def interactive_migration():
    """インタラクティブモード"""
    print("🎯 インタラクティブマイグレーション")
    print("=" * 50)
    
    # 環境チェック
    if not check_environment():
        print("❌ 環境チェックに失敗しました。処理を中止します。")
        return
    
    # 現在の状況を表示
    print("\n📋 現在の権限バージョン確認...")
    try:
        db = SessionLocal()
        migrator = PermissionMigrator(db)
        current_version = migrator.get_current_version()
        db.close()
        
        if current_version:
            print(f"現在のバージョン: {current_version.value}")
        else:
            print("現在のバージョン: 未適用")
    except Exception as e:
        print(f"バージョン確認エラー: {e}")
        return
    
    # ターゲットバージョンを選択
    print("\n🎯 適用したいバージョンを選択してください:")
    versions = list(PermissionVersion)
    for i, version in enumerate(versions, 1):
        print(f"{i}. {version.value}")
    
    try:
        choice = input("選択 (番号): ")
        target_version = versions[int(choice) - 1]
    except (ValueError, IndexError):
        print("無効な選択です。")
        return
    
    # ドライラン実行
    print(f"\n🧪 {target_version.value} のドライランを実行します...")
    dry_result = dry_run_migration(target_version.value)
    
    if not dry_result or not dry_result.get('success', True):
        print("❌ ドライランでエラーが発生しました。処理を中止します。")
        return
    
    # 実行確認
    print("\n⚠️  実際のマイグレーションを実行しますか?")
    print("この操作はデータベースを変更します。")
    confirm = input("続行しますか? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("処理をキャンセルしました。")
        return
    
    # バックアップ作成
    backup_file = backup_current_permissions()
    if not backup_file:
        print("❌ バックアップに失敗しました。処理を中止します。")
        return
    
    # 実際のマイグレーション実行
    success = apply_migration(target_version.value, backup_file)
    
    if success:
        print("\n🎉 マイグレーションが正常に完了しました!")
        print(f"💾 バックアップファイル: {backup_file}")
        print("📝 ログファイルも確認してください。")
    else:
        print(f"\n❌ マイグレーションに失敗しました。")
        print(f"💾 バックアップファイル: {backup_file}")
        print("📝 ログファイルでエラー詳細を確認してください。")


def main():
    parser = argparse.ArgumentParser(description="権限・ロールマイグレーションツール")
    parser.add_argument('--version', help="適用するバージョン (例: v1.1.0)")
    parser.add_argument('--dry-run', action='store_true', help="ドライラン実行")
    parser.add_argument('--interactive', action='store_true', help="インタラクティブモード")
    parser.add_argument('--check-env', action='store_true', help="環境チェックのみ")
    parser.add_argument('--backup', action='store_true', help="現在の設定をバックアップのみ")
    parser.add_argument('--verbose', action='store_true', help="詳細ログ")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.interactive:
        interactive_migration()
    elif args.check_env:
        check_environment()
    elif args.backup:
        backup_current_permissions()
    elif args.dry_run:
        dry_run_migration(args.version)
    else:
        # 通常のマイグレーション実行
        if not check_environment():
            sys.exit(1)
        
        backup_file = backup_current_permissions()
        if not backup_file:
            sys.exit(1)
        
        success = apply_migration(args.version, backup_file)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
