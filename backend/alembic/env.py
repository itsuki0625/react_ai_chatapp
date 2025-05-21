import os # 環境変数を読み込むために追加
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine # create_engine をインポート (offline モードで使う可能性)

from alembic import context

# アプリケーションのBaseとモデルをインポート
# パスはプロジェクト構成に合わせて調整してください
from app.models.base import Base
# 以下のインポートはBase.metadataが全てのモデルを認識していれば不要な場合もありますが、
# 明示的にインポートしておく方が安全です。
from app.models.user import User, UserRole, Role, Permission, RolePermission, UserLoginInfo, PasswordResetToken, TokenBlacklist
from app.models.chat import ChatSession, ChatMessage, ChatAttachment, ChatMessageMetadata
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.system import AuditLog # 修正: audit -> system
from app.models.checklist import ChecklistItem, ChecklistEvaluation # 追加: Checklist関連モデル

# 通知関連モデルのインポートを追加
from app.models.notification_setting import NotificationSetting
from app.models.push_subscription import PushSubscription
from app.models.in_app_notification import InAppNotification

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# alembic.ini から DATABASE_URL を読み込む設定
# config.set_main_option('sqlalchemy.url', os.environ.get('DATABASE_URL'))
# または、環境変数から直接読み込む
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    # alembic.ini の設定を使用する場合 (コメントアウトを解除)
    # ini_url = config.get_main_option("sqlalchemy.url")
    # if not ini_url:
    #     raise ValueError("DATABASE_URL environment variable or sqlalchemy.url in alembic.ini must be set")
    pass # iniファイルの設定にフォールバック（iniファイルにURLが設定されている前提）


# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # ★ Base.metadata を設定

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # ★ configからURLを取得するように修正
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("Database URL not found in alembic.ini or environment variables.")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # ★ configからURLを取得するように修正
    # connectable = engine_from_config(...) の代わりにURLを直接使うか、
    # engine_from_config が config.get_main_option("sqlalchemy.url") を使えるようにする
    configuration = config.get_section(config.config_ini_section, {})
    # 環境変数や set_main_option で設定した URL が使われるように
    configuration['sqlalchemy.url'] = config.get_main_option("sqlalchemy.url")
    if not configuration['sqlalchemy.url']:
        raise ValueError("Database URL not found in alembic.ini or environment variables.")

    connectable = engine_from_config(
        configuration, # 修正: configセクション全体を渡す
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
