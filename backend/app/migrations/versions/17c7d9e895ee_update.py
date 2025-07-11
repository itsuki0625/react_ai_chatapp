"""update

Revision ID: 17c7d9e895ee
Revises: e20ef2f16227
Create Date: 2025-05-05 05:35:38.728875

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17c7d9e895ee'
down_revision: Union[str, None] = 'e20ef2f16227'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('stripe_coupons',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('stripe_coupon_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('duration', sa.String(), nullable=False),
    sa.Column('duration_in_months', sa.Integer(), nullable=True),
    sa.Column('amount_off', sa.Integer(), nullable=True),
    sa.Column('percent_off', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('redeem_by', sa.DateTime(), nullable=True),
    sa.Column('max_redemptions', sa.Integer(), nullable=True),
    sa.Column('times_redeemed', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stripe_coupons_stripe_coupon_id'), 'stripe_coupons', ['stripe_coupon_id'], unique=True)
    op.add_column('campaign_codes', sa.Column('stripe_promotion_code_id', sa.String(), nullable=True))
    op.add_column('campaign_codes', sa.Column('coupon_id', sa.UUID(), nullable=True))
    op.drop_constraint('campaign_codes_code_key', 'campaign_codes', type_='unique')
    op.create_index(op.f('ix_campaign_codes_code'), 'campaign_codes', ['code'], unique=True)
    op.create_index(op.f('ix_campaign_codes_coupon_id'), 'campaign_codes', ['coupon_id'], unique=False)
    op.create_index(op.f('ix_campaign_codes_stripe_promotion_code_id'), 'campaign_codes', ['stripe_promotion_code_id'], unique=True)
    op.drop_constraint('campaign_codes_discount_type_id_fkey', 'campaign_codes', type_='foreignkey')
    op.create_foreign_key(None, 'campaign_codes', 'stripe_coupons', ['coupon_id'], ['id'])
    op.drop_column('campaign_codes', 'discount_value')
    op.drop_column('campaign_codes', 'discount_type_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('campaign_codes', sa.Column('discount_type_id', sa.UUID(), autoincrement=False, nullable=False))
    op.add_column('campaign_codes', sa.Column('discount_value', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'campaign_codes', type_='foreignkey')
    op.create_foreign_key('campaign_codes_discount_type_id_fkey', 'campaign_codes', 'discount_types', ['discount_type_id'], ['id'])
    op.drop_index(op.f('ix_campaign_codes_stripe_promotion_code_id'), table_name='campaign_codes')
    op.drop_index(op.f('ix_campaign_codes_coupon_id'), table_name='campaign_codes')
    op.drop_index(op.f('ix_campaign_codes_code'), table_name='campaign_codes')
    op.create_unique_constraint('campaign_codes_code_key', 'campaign_codes', ['code'])
    op.drop_column('campaign_codes', 'coupon_id')
    op.drop_column('campaign_codes', 'stripe_promotion_code_id')
    op.drop_index(op.f('ix_stripe_coupons_stripe_coupon_id'), table_name='stripe_coupons')
    op.drop_table('stripe_coupons')
    # ### end Alembic commands ###
