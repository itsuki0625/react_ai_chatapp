import enum
from sqlalchemy import Enum as SQLAlchemyEnum

class SessionType(enum.Enum):
    NORMAL = "normal"
    CONSULTATION = "consultation"
    FAQ = "faq"

class SessionStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"

class SenderType(enum.Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"

class MessageType(enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"

class DocumentStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"

class PersonalStatementStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    REVIEWED = "REVIEWED"
    FINAL = "FINAL"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# SQLAlchemyで使用するための型定義
UserRoleType = SQLAlchemyEnum(UserRole)

# ... 他のEnum定義 