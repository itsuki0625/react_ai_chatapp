from sqlalchemy import Column, String, Text, UUID, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func # func.now() のためにインポート
import uuid
from .base import Base, TimestampMixin
from .agent_call import AgentCall # AgentCall モデルをインポート

class AgentInteractionEvent(Base, TimestampMixin):
    __tablename__ = 'agent_interaction_events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    parent_interaction_id = Column(UUID(as_uuid=True), ForeignKey('agent_interaction_events.id'), nullable=True)
    # agent_calls.id は SERIAL (Integer) なので、Integer型で参照します。
    agent_call_id = Column(Integer, ForeignKey('agent_calls.id'), nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=True)
    tool_name = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    structured_content = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)

    # Relationships
    # 親イベントへのリレーションシップ (自己参照)
    # `backref` は SQLAlchemy 2.0 では非推奨傾向のため、`back_populates` を使用するか、
    # もしくは片方向リレーションシップを検討します。ここでは一旦 backref のままにしておきます。
    parent_event = relationship("AgentInteractionEvent", remote_side=[id], backref="child_events")
    
    # AgentCall モデルへのリレーションシップを有効化
    agent_call = relationship("AgentCall", back_populates="interaction_events") 

    __table_args__ = (
        Index('idx_agent_interaction_events_session_id', 'session_id'),
        Index('idx_agent_interaction_events_timestamp', 'timestamp'),
        Index('idx_agent_interaction_events_event_type', 'event_type'),
    )

    def __repr__(self):
        return f"<AgentInteractionEvent(id={self.id}, session_id={self.session_id}, event_type='{self.event_type}')>"

# agent_calls テーブルの id が SERIAL (Integer) の場合の agent_call_id の定義例
# agent_call_id = Column(Integer, ForeignKey(\'agent_calls.id\'), nullable=True) 