import uuid
import sys
import os
from sqlalchemy.orm import Session
import logging

# --- パス設定 --- 
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- ここまで --- 

from app.database.database import SessionLocal, engine # engine もインポート
from app.models.user import Permission, Base # Permission と Base をインポート

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 追加したい権限のリスト (名前: 説明)
PERMISSIONS_TO_ADD = {
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
    
    # --- 追加: Role Management --- 
    'role_read': 'ロール情報を閲覧する',
    'role_create': '新しいロールを作成する',
    'role_update': '既存のロール情報を更新する',
    'role_delete': 'ロールを削除する',
    'role_permission_assign': 'ロールに対して権限を割り当てる/解除する',
    # --- 追加: Permission Management (if needed) --- 
    'permission_read': '権限情報を閲覧する',
    'permission_create': '新しい権限を作成する',
    'permission_update': '既存の権限情報を更新する',
    'permission_delete': '権限を削除する',
    
    # --- 追加: Admin Access --- # 既存のチェック (get_current_superuser) を置き換えるため
    'admin_access': '管理者機能へのアクセス全般',

    # --- 追加: Stripe Product Management ---
    'stripe_product_read': 'Stripe 商品情報を閲覧する',
    'stripe_product_write': 'Stripe 商品情報を作成・更新・アーカイブする',
    # --- 追加: Stripe Price Management ---
    'stripe_price_read': 'Stripe 価格情報を閲覧する',
    'stripe_price_write': 'Stripe 価格情報を作成・更新・アーカイブする',
    # --- 追加: Campaign Code Management ---
    'campaign_code_read': 'キャンペーンコード情報を閲覧する',
    'campaign_code_write': 'キャンペーンコードを作成・削除する',
    # --- 追加: Discount Type Management ---
    'discount_type_read': '割引タイプ情報を閲覧する',
    'discount_type_write': '割引タイプを作成・更新・削除する',

    # --- 追加: Study Plan Management ---
    'study_plan_read': '学習計画を閲覧する',
    'study_plan_write': '学習計画を作成・更新・削除する',

    # --- 追加: Communication Management ---
    'communication_read': '会話やメッセージを閲覧する',
    'communication_write': '会話を開始したりメッセージを送信する',

    # --- 追加: Application Management ---
    'application_read': '出願情報を閲覧する',
    'application_write': '出願情報を作成・更新・削除する',
}

def seed_permissions():
    """
    定義された権限をデータベースに挿入（存在しない場合のみ）
    """
    # テーブルが存在しない場合に作成 (開発環境用)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Ensured tables exist (or created).")
    except Exception as e:
        logger.warning(f"テーブル作成中にエラーが発生しました（無視します）: {e}")

    db: Session = SessionLocal()
    try:
        added_count = 0
        
        for name, description in PERMISSIONS_TO_ADD.items():
            exists = db.query(Permission).filter(Permission.name == name).first()
            if not exists:
                new_permission = Permission(
                    id=uuid.uuid4(),
                    name=name,
                    description=description
                )
                db.add(new_permission)
                logger.info(f"Added permission: '{name}'")
                added_count += 1
            else:
                logger.info(f"Permission '{name}' already exists.")

        if added_count > 0:
            db.commit()
            logger.info(f"{added_count} new permission(s) committed.")
        else:
            logger.info("No new permissions needed to be added.")

    except Exception as e:
        logger.error(f"権限挿入中にエラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Seeding permissions...")
    seed_permissions()
    logger.info("Permission seeding complete.") 