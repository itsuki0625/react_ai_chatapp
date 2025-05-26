from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy import Column, DateTime

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 