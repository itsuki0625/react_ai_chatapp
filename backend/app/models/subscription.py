from sqlalchemy import Column, String, UUID, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .base import Base, TimestampMixin

class Subscription(Base, TimestampMixin):
    __tablename__ = 'subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    status = Column(String, nullable=False)  # 'active', 'past_due', 'canceled', 'unpaid', 'trialing'
    plan_name = Column(String, nullable=False)
    price_id = Column(String, nullable=False)  # Stripeの価格ID
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    campaign_code_id = Column(UUID(as_uuid=True), ForeignKey('campaign_codes.id'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    campaign_code = relationship("CampaignCode", back_populates="subscriptions")
    payment_history = relationship("PaymentHistory", back_populates="subscription")

class PaymentHistory(Base, TimestampMixin):
    __tablename__ = 'payment_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True)
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_invoice_id = Column(String, nullable=True)
    amount = Column(Integer, nullable=False)
    currency = Column(String, default='jpy')
    status = Column(String, nullable=False)  # 'succeeded', 'pending', 'failed'
    payment_method = Column(String, nullable=True)
    payment_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payment_history")
    subscription = relationship("Subscription", back_populates="payment_history")

class CampaignCode(Base, TimestampMixin):
    __tablename__ = 'campaign_codes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # キャンペーンコードの所有者（アフィリエイター等）
    discount_type = Column(String, nullable=False)  # 'percentage', 'fixed'
    discount_value = Column(Float, nullable=False)  # 割引率(%)または固定金額
    max_uses = Column(Integer, nullable=True)  # 最大使用回数（nullは無制限）
    used_count = Column(Integer, default=0)  # 使用回数
    valid_from = Column(DateTime, nullable=True)  # 有効期間開始
    valid_until = Column(DateTime, nullable=True)  # 有効期間終了
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_campaign_codes")
    subscriptions = relationship("Subscription", back_populates="campaign_code")
    
    @property
    def is_valid(self):
        """コードが現在有効かどうかをチェック"""
        now = datetime.utcnow()
        
        # 非アクティブの場合
        if not self.is_active:
            return False
            
        # 有効期間のチェック
        if self.valid_from and self.valid_from > now:
            return False
            
        if self.valid_until and self.valid_until < now:
            return False
            
        # 使用回数のチェック
        if self.max_uses and self.used_count >= self.max_uses:
            return False
            
        return True 