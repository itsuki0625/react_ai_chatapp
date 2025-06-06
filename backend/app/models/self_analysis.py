from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin

class SelfAnalysisSession(Base, TimestampMixin):
    __tablename__ = 'self_analysis_sessions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    current_step = Column(String, nullable=False)

    notes = relationship('SelfAnalysisNote', back_populates='session')
    cots = relationship('COT', back_populates='session')
    reflections = relationship('Reflection', back_populates='session')
    summary = relationship('Summary', back_populates='session', uselist=False)

class SelfAnalysisNote(Base, TimestampMixin):
    __tablename__ = 'self_analysis_notes'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('self_analysis_sessions.id'), nullable=False)
    step = Column(String, nullable=False)
    content = Column(JSON, nullable=False)

    session = relationship('SelfAnalysisSession', back_populates='notes')

class COT(Base, TimestampMixin):
    __tablename__ = 'self_analysis_cots'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('self_analysis_sessions.id'), nullable=False)
    step = Column(String, nullable=False)
    cot = Column(String, nullable=False)

    session = relationship('SelfAnalysisSession', back_populates='cots')

class Reflection(Base, TimestampMixin):
    __tablename__ = 'self_analysis_reflections'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey('self_analysis_sessions.id'), nullable=False)
    step = Column(String, nullable=False)
    level = Column(String, nullable=False)
    reflection = Column(String, nullable=False)

    session = relationship('SelfAnalysisSession', back_populates='reflections')

class Summary(Base):
    __tablename__ = 'self_analysis_summaries'

    session_id = Column(String, ForeignKey('self_analysis_sessions.id'), primary_key=True)
    q1 = Column(String, nullable=True)
    q2 = Column(String, nullable=True)
    q3 = Column(String, nullable=True)
    q4 = Column(String, nullable=True)
    q5 = Column(String, nullable=True)
    q6 = Column(String, nullable=True)
    q7 = Column(String, nullable=True)
    q8 = Column(String, nullable=True)
    q9 = Column(String, nullable=True)

    session = relationship('SelfAnalysisSession', back_populates='summary') 