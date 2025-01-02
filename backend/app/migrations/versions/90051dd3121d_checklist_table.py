"""checklist table

Revision ID: 90051dd3121d
Revises: c714219ac74a
Create Date: 2024-01-xx xx:xx:xx.xxxxxx

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = '90051dd3121d'
down_revision: Union[str, None] = 'c714219ac74a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('checklist_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('chat_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('checklist_items', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('completion_status', sa.Boolean(), nullable=True, default=False),
        sa.Column('ai_feedback', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['chat_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_evaluations_id'), 'checklist_evaluations', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_checklist_evaluations_id'), table_name='checklist_evaluations')
    op.drop_table('checklist_evaluations')
