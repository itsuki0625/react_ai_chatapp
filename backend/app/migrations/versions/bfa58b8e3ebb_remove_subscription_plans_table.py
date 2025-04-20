"""Remove subscription_plans table

Revision ID: bfa58b8e3ebb
Revises: 4e009e4cff56
Create Date: 2025-04-20 14:34:52.290193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa58b8e3ebb'
down_revision: Union[str, None] = '4e009e4cff56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
