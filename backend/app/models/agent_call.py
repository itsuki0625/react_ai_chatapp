from sqlalchemy import Column, String, Text, UUID, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid # session_id が UUID のため
from .base import Base, TimestampMixin # TimestampMixin を created_at に使用

class AgentCall(Base, TimestampMixin): # TimestampMixin を継承
    __tablename__ = 'agent_calls'

    id = Column(Integer, primary_key=True, index=True) # SERIAL PRIMARY KEY
    session_id = Column(UUID(as_uuid=True), nullable=True) # review.md では nullable
    agent_name = Column(Text, nullable=True)
    model = Column(Text, nullable=True)
    prompt_tok = Column(Integer, nullable=True)
    completion_tok = Column(Integer, nullable=True)
    yen = Column(Numeric(12, 4), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # created_at は TimestampMixin から継承されるので明示的な定義は不要

    # AgentInteractionEventへのリレーションシップ
    # AgentInteractionEvent.agent_call_id がこのテーブルの id を参照する
    interaction_events = relationship("AgentInteractionEvent", back_populates="agent_call")

    def __repr__(self):
        return f"<AgentCall(id={self.id}, agent_name='{self.agent_name}', model='{self.model}')>" 