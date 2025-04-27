# backend/app/migrations/seed_extra_discount_types.py
import uuid
import sys
import os
from sqlalchemy.orm import Session
import logging # ロギングを追加

# --- パス設定を追加 --- 
# スクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトルートのパスを取得 (migrations -> app -> backend -> project_root)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
# Pythonの検索パスにプロジェクトルートを追加
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- ここまで --- 

from app.database.database import SessionLocal, engine # engine もインポート
from app.models.subscription import DiscountType, Base # Base もインポート

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_additional_discount_types():
    """
    追加の割引タイプのみをデータベースに挿入（存在しない場合のみ）
    """
    # テーブルが存在しない場合に作成 (開発環境用)
    # 念のため実行するが、既存DBがある場合は通常不要
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"テーブル作成中にエラーが発生しました（無視します）: {e}")

    db: Session = SessionLocal()
    try:
        # 追加したい割引タイプをすべてチェック
        types_to_add = {
            'percentage': '割引率 (%)',
            'fixed': '固定割引額 (円)',
            'none': '割引なし',
            'trial_fixed': 'トライアル固定価格',
            'trial_percentage': 'トライアル割引率'
        }
        
        added_count = 0
        
        for name, description in types_to_add.items():
            exists = db.query(DiscountType).filter(DiscountType.name == name).first()
            if not exists:
                new_type = DiscountType(
                    id=uuid.uuid4(),
                    name=name,
                    description=description
                )
                db.add(new_type)
                logger.info(f"Added '{name}' discount type.")
                added_count += 1
            else:
                logger.info(f"Discount type '{name}' already exists.")

        if added_count > 0:
            db.commit()
            logger.info(f"{added_count} new discount type(s) committed.")
        else:
            logger.info("No new discount types needed to be added.")

    except Exception as e:
        logger.error(f"追加の割引タイプ挿入中にエラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Seeding additional discount types...")
    seed_additional_discount_types()
    logger.info("Additional discount type seeding complete.") 