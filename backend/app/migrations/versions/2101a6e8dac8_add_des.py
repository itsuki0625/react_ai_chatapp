"""add des

Revision ID: 2101a6e8dac8
Revises: e3aa8f6ff620
Create Date: 2025-05-01 00:31:12.750922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2101a6e8dac8'
down_revision: Union[str, None] = 'e3aa8f6ff620'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('admission_methods', sa.Column('description', sa.Text(), nullable=True))
    op.create_index(op.f('ix_admission_methods_name'), 'admission_methods', ['name'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_admission_methods_name'), table_name='admission_methods')
    op.drop_column('admission_methods', 'description')
    # ### end Alembic commands ###
