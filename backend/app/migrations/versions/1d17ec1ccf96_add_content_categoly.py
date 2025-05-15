"""add-content-categoly

Revision ID: 1d17ec1ccf96
Revises: 102fc87ec254
Create Date: 2025-05-15 14:08:44.996383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '1d17ec1ccf96'
down_revision: Union[str, None] = '102fc87ec254'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# カテゴリーの初期データ
initial_categories = [
    {"id": uuid.uuid4(), "name": "self_analysis", "description": "自己分析", "display_order": 1, "is_active": True},
    {"id": uuid.uuid4(), "name": "admissions", "description": "入試情報", "display_order": 2, "is_active": True},
    {"id": uuid.uuid4(), "name": "academic", "description": "学術・教養", "display_order": 3, "is_active": True},
    {"id": uuid.uuid4(), "name": "university_info", "description": "大学情報", "display_order": 4, "is_active": True},
    {"id": uuid.uuid4(), "name": "career", "description": "キャリア", "display_order": 5, "is_active": True},
    {"id": uuid.uuid4(), "name": "other", "description": "その他", "display_order": 6, "is_active": True},
]


def upgrade() -> None:
    # content_categories テーブルのメタデータを取得
    # (created_at, updated_at はモデル側の TimestampMixin で自動設定される想定)
    # (parent_id, icon_url は今回は設定しないので省略)
    content_categories_table = sa.table(
        'content_categories',
        sa.column('id', sa.UUID),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('display_order', sa.Integer),
        sa.column('is_active', sa.Boolean) # is_active も追加
    )

    op.bulk_insert(content_categories_table, initial_categories)


def downgrade() -> None:
    # ロールバック時にはデータを削除する（nameをキーに削除する例）
    # より安全なのは id を使うことですが、initial_categories の id は実行ごとに変わるため name で行います。
    # もし name が重複する可能性がある場合は、より確実な方法を検討する必要があります。
    for category_data in initial_categories:
        # name が Python の予約語や SQL の予約語と衝突しないようにクォートする
        op.execute(
            f"DELETE FROM content_categories WHERE name = '{category_data['name']}'"
        )
