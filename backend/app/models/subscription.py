from sqlalchemy import Column, String, UUID, Boolean, DateTime, ForeignKey, Integer, Float, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .base import Base, TimestampMixin

class StripeDbProduct(Base, TimestampMixin):
    __tablename__ = 'stripe_db_products'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_product_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    active = Column(Boolean, default=True)
    metadata_ = Column('metadata', JSON)

    # Relationships
    subscription_plans = relationship("SubscriptionPlan", back_populates="stripe_db_product")

class Subscription(Base, TimestampMixin):
    __tablename__ = 'subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    status = Column(String, nullable=False)  # 'active', 'past_due', 'canceled', 'unpaid', 'trialing'
    plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'), nullable=False)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at = Column(DateTime)
    canceled_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    campaign_code_id = Column(UUID(as_uuid=True), ForeignKey('campaign_codes.id'))
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    campaign_code = relationship("CampaignCode", back_populates="subscriptions")
    payment_history = relationship("PaymentHistory", back_populates="subscription")
    invoices = relationship("Invoice", back_populates="subscription")

class SubscriptionPlan(Base, TimestampMixin):
    __tablename__ = 'subscription_plans'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=False)
    description = Column(String)
    price_id = Column(String, nullable=False)
    stripe_db_product_id = Column(UUID(as_uuid=True), ForeignKey('stripe_db_products.id'), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default='jpy', nullable=False)
    interval = Column(String, nullable=False)  # 'month', 'year'
    interval_count = Column(Integer, default=1, nullable=False)
    trial_days = Column(Integer)
    is_active = Column(Boolean, default=True)
    features = Column(JSON)
    plan_metadata = Column(JSON)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    invoice_items = relationship("InvoiceItem", back_populates="subscription_plan")
    stripe_db_product = relationship("StripeDbProduct", back_populates="subscription_plans")

class PaymentHistory(Base, TimestampMixin):
    __tablename__ = 'payment_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'))
    stripe_payment_intent_id = Column(String)
    stripe_invoice_id = Column(String)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default='jpy', nullable=False)
    status = Column(String, nullable=False)  # 'succeeded', 'pending', 'failed'
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey('payment_methods.id'))
    payment_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payment_history")
    subscription = relationship("Subscription", back_populates="payment_history")
    payment_method = relationship("PaymentMethod", back_populates="payment_history")

class PaymentMethod(Base, TimestampMixin):
    __tablename__ = 'payment_methods'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    stripe_payment_method_id = Column(String, nullable=False)
    method_type = Column(String, nullable=False)  # 'card', 'bank_transfer', 'convenience_store' etc.
    is_default = Column(Boolean, default=False)
    last_four = Column(String)
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    brand = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User")
    payment_history = relationship("PaymentHistory", back_populates="payment_method")

class StripeCoupon(Base, TimestampMixin):
    __tablename__ = 'stripe_coupons'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_coupon_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String)
    duration = Column(String, nullable=False) # 'forever', 'once', 'repeating'
    duration_in_months = Column(Integer)
    amount_off = Column(Integer)
    percent_off = Column(Float)
    currency = Column(String)
    
    redeem_by_timestamp = Column('redeem_by', Integer, nullable=True)

    max_redemptions = Column(Integer)
    times_redeemed = Column(Integer, default=0)
    
    valid = Column(Boolean, nullable=True) # スキーマの `valid` に合わせる
                                        
    livemode = Column(Boolean, nullable=True) # スキーマに合わせて追加

    # Stripeオブジェクトの作成日時 (Unix timestamp)
    stripe_created_timestamp = Column('stripe_created', Integer, nullable=True) # 追加

    metadata_ = Column('metadata', JSON) # 'metadata' というカラム名でJSON型

    # TimestampMixin が created_at, updated_at (DBレコードのタイムスタンプ) を提供

    campaign_codes = relationship("CampaignCode", back_populates="coupon")

class CampaignCode(Base, TimestampMixin):
    __tablename__ = 'campaign_codes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False, unique=True, index=True)
    description = Column(String)
    max_uses = Column(Integer)
    used_count = Column(Integer, default=0)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    stripe_promotion_code_id = Column(String, nullable=True, unique=True, index=True)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey('stripe_coupons.id'), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    coupon = relationship("StripeCoupon", back_populates="campaign_codes")
    subscriptions = relationship("Subscription", back_populates="campaign_code")
    redemptions = relationship("CampaignCodeRedemption", back_populates="campaign_code")
    
    @property
    def is_valid(self):
        """コードが現在有効かどうかをDB情報で簡易チェック"""
        now = datetime.utcnow()
        if not self.is_active: return False
        if self.valid_from and self.valid_from > now: return False
        if self.valid_until and self.valid_until < now: return False
        if self.max_uses is not None and self.used_count >= self.max_uses: return False
        return True

class CampaignCodeRedemption(Base, TimestampMixin):
    __tablename__ = 'campaign_code_redemptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_code_id = Column(UUID(as_uuid=True), ForeignKey('campaign_codes.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    discount_applied = Column(Float, nullable=False)
    
    # Relationships
    campaign_code = relationship("CampaignCode", back_populates="redemptions")
    user = relationship("User")
    subscription = relationship("Subscription")

class Invoice(Base, TimestampMixin):
    __tablename__ = 'invoices'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'))
    stripe_invoice_id = Column(String)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default='jpy', nullable=False)
    status = Column(String, nullable=False)  # 'draft', 'open', 'paid', 'uncollectible', 'void'
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    paid_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base, TimestampMixin):
    __tablename__ = 'invoice_items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('invoices.id'), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    subscription_plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")
    subscription_plan = relationship("SubscriptionPlan", back_populates="invoice_items") 