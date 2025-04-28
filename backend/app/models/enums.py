import enum
from sqlalchemy import Enum as SQLAlchemyEnum

class MessageSender(str, enum.Enum):
    USER = "user"
    AI = "ai"
    # SYSTEM = "system" # Keep commented out if not used

class ChatType(str, enum.Enum):
    SELF_ANALYSIS = "self_analysis"
    ADMISSION = "admission" # 総合型選抜
    STUDY_SUPPORT = "study_support" # 汎用学習支援
    GENERAL = "general" # スキーマにあったもの (元々ここにあった)
    # CONSULTATION = "consultation" # Keep commented out if not used
    # FAQ = "faq" # Keep commented out if not used
    # 必要に応じて他のタイプを追加

class SessionType(enum.Enum):
    NORMAL = "normal"
    CONSULTATION = "consultation"
    FAQ = "faq"

class SessionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"

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

class PersonalStatementStatus(enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    REVIEWED = "reviewed"
    FINAL = "final"

class RoleType(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    COUNSELOR = "counselor"
    PARENT = "parent"

class ContentType(enum.Enum):
    VIDEO = "video"
    SLIDE = "slide"
    PDF = "pdf"
    AUDIO = "audio"
    ARTICLE = "article"

class DeviceType(enum.Enum):
    PC = "pc"
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    TV = "tv"
    OTHER = "other"

class NotificationType(enum.Enum):
    CHAT_MESSAGE = "chat_message"
    DOCUMENT_DEADLINE = "document_deadline"
    EVENT_REMINDER = "event_reminder"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    FEEDBACK_RECEIVED = "feedback_received"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    BROADCAST_MESSAGE = "broadcast_message"

class NotificationPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    URGENT = "urgent"

class StudyPlanStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

class LearningItemStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class ReactionType(enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    HELPFUL = "helpful"
    LOVE = "love"
    CONFUSED = "confused"

class TokenBlacklistReason(enum.Enum):
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    SECURITY_BREACH = "security_breach"
    MANUAL_REVOCATION = "manual_revocation"

class AccountLockReason(enum.Enum):
    FAILED_ATTEMPTS = "failed_attempts"
    SECURITY_BREACH = "security_breach"
    ADMIN_LOCK = "admin_lock"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class AuditLogAction(enum.Enum):
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_EMAIL_VERIFY = "user_email_verify"
    USER_LOCK = "user_lock"
    USER_UNLOCK = "user_unlock"
    USER_LOGIN = "user_login"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_LOGOUT = "user_logout"
    USER_ROLE_ASSIGN = "user_role_assign"
    USER_ROLE_REMOVE = "user_role_remove"
    TOKEN_ISSUE = "token_issue"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKE = "token_revoke"
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    PAYMENT_PROCESS = "payment_process"
    PAYMENT_REFUND = "payment_refund"
    CONTENT_CREATE = "content_create"
    CONTENT_UPDATE = "content_update"
    CONTENT_DELETE = "content_delete"
    FORUM_TOPIC_CREATE = "forum_topic_create"
    FORUM_TOPIC_DELETE = "forum_topic_delete"
    PERSONAL_STATEMENT_CREATE = "personal_statement_create"
    PERSONAL_STATEMENT_UPDATE = "personal_statement_update"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    SECURITY_BREACH = "security_breach"

class AuditLogStatus(enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    COMPLETED = "completed"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    UNPAID = "unpaid"

# SQLAlchemyで使用するための型定義
UserRoleType = SQLAlchemyEnum(RoleType)

# ... 他のEnum定義 