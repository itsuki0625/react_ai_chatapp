"""add_self_analysis_tables

Revision ID: eed8bb7be501
Revises: bba18f297f28
Create Date: 2025-05-25 21:12:49.390230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eed8bb7be501'
down_revision: Union[str, None] = 'bba18f297f28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('self_analysis_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('current_step', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('self_analysis_cots',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('step', sa.String(), nullable=False),
    sa.Column('cot', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['self_analysis_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('self_analysis_notes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('step', sa.String(), nullable=False),
    sa.Column('content', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['self_analysis_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('self_analysis_reflections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('step', sa.String(), nullable=False),
    sa.Column('level', sa.String(), nullable=False),
    sa.Column('reflection', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['self_analysis_sessions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('self_analysis_summaries',
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('q1', sa.String(), nullable=True),
    sa.Column('q2', sa.String(), nullable=True),
    sa.Column('q3', sa.String(), nullable=True),
    sa.Column('q4', sa.String(), nullable=True),
    sa.Column('q5', sa.String(), nullable=True),
    sa.Column('q6', sa.String(), nullable=True),
    sa.Column('q7', sa.String(), nullable=True),
    sa.Column('q8', sa.String(), nullable=True),
    sa.Column('q9', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['self_analysis_sessions.id'], ),
    sa.PrimaryKeyConstraint('session_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('self_analysis_summaries')
    op.drop_table('self_analysis_reflections')
    op.drop_table('self_analysis_notes')
    op.drop_table('self_analysis_cots')
    op.drop_table('self_analysis_sessions')
    # ### end Alembic commands ###
