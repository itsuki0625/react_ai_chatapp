from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.orm import Session
from alembic import context
import os
import sys
from app.models import Base
from app.core.config import settings
from app.migrations.demo_data import insert_demo_data

# Alembicの設定ファイルのディレクトリをPYTHONPATHに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# このファイルはalembic.iniから読み込まれます
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータのターゲットを設定
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

        # デモデータの挿入（環境変数で制御）
        if os.getenv('INSERT_DEMO_DATA', '').lower() == 'true':
            db = Session(bind=connection)
            try:
                insert_demo_data(db)
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 