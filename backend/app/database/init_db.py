from sqlalchemy.orm import Session
from app.database.database import engine, SessionLocal
from app.models.base import Base
from app.migrations.demo_data import insert_demo_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db() -> None:
    try:
        # データベースセッションの作成
        db = SessionLocal()
        
        # テーブルの作成
        Base.metadata.create_all(bind=engine)
        
        # デモデータの挿入
        insert_demo_data(db)
        
        logger.info("データベースの初期化が完了しました")
        
    except Exception as e:
        logger.error(f"データベースの初期化中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("データベースの初期化を開始します...")
    init_db()