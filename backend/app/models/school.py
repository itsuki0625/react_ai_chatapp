from sqlalchemy import Column, String, UUID, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, TimestampMixin

class School(Base, TimestampMixin):
    __tablename__ = 'schools'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    school_code = Column(String, unique=True, nullable=False)
    address = Column(Text)
    prefecture = Column(String)
    city = Column(String)
    zip_code = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    principal_name = Column(String)
    website_url = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="school") 