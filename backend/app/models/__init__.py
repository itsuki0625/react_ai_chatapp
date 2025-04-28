from app.models.base import Base, TimestampMixin
from app.models.content import (
    Content, ContentTag, ContentCategory, ContentCategoryRelation, 
    ContentViewHistory, ContentViewHistoryMetaData, ContentRating
)
from .user import (
    User, Role, Permission, RolePermission, UserProfile, UserLoginInfo, 
    UserEmailVerification, UserTwoFactorAuth, UserRole, UserRoleAssignment, 
    UserRoleMetadata, TokenBlacklist, UserContactInfo
)
from .school import School, SchoolDetails, SchoolContact
from .university import University, UniversityDetails, UniversityContact, Department, DepartmentDetails
from .admission import AdmissionMethod, AdmissionMethodDetails
from .desired_school import DesiredSchool, DesiredDepartment
from .document import Document, DocumentSubmission
from .schedule import ScheduleEvent, EventCompletion
from .personal_statement import PersonalStatement, PersonalStatementSubmission, Feedback
from .chat import (
    ChatSession, ChatMessage, ChatAttachment, ChatMessageMetadata
)
from .system import (
    SystemLog, SystemSetting, Notification, NotificationMetaData, 
    NotificationSetting, BroadcastNotification, BroadcastTargetRole, 
    BroadcastTargetSchool, BroadcastNotificationMetaData, AuditLog, 
    AuditLogDetails, AuditLogAdditionalInfo
)
from .subscription import (
    Subscription, SubscriptionPlan, PaymentHistory, PaymentMethod, 
    CampaignCode, DiscountType, CampaignCodeRedemption, Invoice, InvoiceItem
)
from .enums import (
    SessionType, SessionStatus, SenderType, MessageType, DocumentStatus,
    PersonalStatementStatus, RoleType, ContentType, DeviceType,
    NotificationType, NotificationPriority, StudyPlanStatus, DifficultyLevel,
    QuestionType, LearningItemStatus, ReactionType, TokenBlacklistReason,
    AccountLockReason, AuditLogAction, AuditLogStatus
)
from .checklist import ChecklistEvaluation
from .study_plan import StudyPlan, StudyGoal, StudyPlanTemplate
from .quiz import Quiz, QuizQuestion, QuizAnswer, UserQuizAttempt, UserQuizAnswer
from .communication import Conversation, Message
from .forum import (
    ForumCategory, ForumTopic, ForumPost, ForumPostReaction, ForumTopicView
)
from .learning_path import (
    LearningPath, LearningPathPrerequisite, LearningPathAudience, 
    LearningPathItem, UserLearningPath, UserLearningPathItem, 
    UserLearningPathNote, StudyPlanItem
)

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    
    # User related
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserProfile",
    "UserLoginInfo",
    "UserEmailVerification",
    "UserTwoFactorAuth",
    "UserRole",
    "UserRoleAssignment",
    "UserRoleMetadata",
    "TokenBlacklist",
    "UserContactInfo",
    
    # School related
    "School",
    "SchoolDetails",
    "SchoolContact",
    
    # University related
    "University",
    "UniversityDetails",
    "UniversityContact",
    "Department",
    "DepartmentDetails",
    
    # Admission related
    "AdmissionMethod",
    "AdmissionMethodDetails",
    
    # Desired school related
    "DesiredSchool",
    "DesiredDepartment",
    
    # Document related
    "Document",
    "DocumentSubmission",
    
    # Schedule related
    "ScheduleEvent",
    "EventCompletion",
    
    # Personal statement related
    "PersonalStatement",
    "PersonalStatementSubmission",
    "Feedback",
    
    # Chat related
    "ChatSession",
    "ChatMessage",
    "ChatAttachment",
    "ChatMessageMetadata",
    
    # System related
    "SystemLog",
    "SystemSetting",
    "Notification",
    "NotificationMetaData",
    "NotificationSetting",
    "BroadcastNotification",
    "BroadcastTargetRole",
    "BroadcastTargetSchool",
    "BroadcastNotificationMetaData",
    "AuditLog",
    "AuditLogDetails",
    "AuditLogAdditionalInfo",
    
    # Content related
    "Content",
    "ContentTag",
    "ContentCategory",
    "ContentCategoryRelation",
    "ContentViewHistory",
    "ContentViewHistoryMetaData",
    "ContentRating",
    
    # Subscription related
    "Subscription",
    "SubscriptionPlan",
    "PaymentHistory",
    "PaymentMethod",
    "CampaignCode",
    "DiscountType",
    "CampaignCodeRedemption",
    "Invoice",
    "InvoiceItem",
    
    # Study Plan related
    "StudyPlan",
    "StudyGoal",
    "StudyPlanTemplate",
    "StudyPlanItem",
    
    # Quiz related
    "Quiz",
    "QuizQuestion",
    "QuizAnswer",
    "UserQuizAttempt",
    "UserQuizAnswer",
    
    # Communication related
    "Conversation",
    "Message",
    
    # Forum related
    "ForumCategory",
    "ForumTopic",
    "ForumPost",
    "ForumPostReaction", 
    "ForumTopicView",
    
    # Learning Path related
    "LearningPath",
    "LearningPathPrerequisite",
    "LearningPathAudience",
    "LearningPathItem",
    "UserLearningPath",
    "UserLearningPathItem",
    "UserLearningPathNote",
    
    # Checklist related
    "ChecklistEvaluation",
    
    # Enums
    "SessionType",
    "SessionStatus",
    "SenderType",
    "MessageType",
    "DocumentStatus",
    "PersonalStatementStatus",
    "RoleType",
    "ContentType",
    "DeviceType",
    "NotificationType",
    "NotificationPriority",
    "StudyPlanStatus",
    "DifficultyLevel",
    "QuestionType",
    "LearningItemStatus",
    "ReactionType",
    "TokenBlacklistReason",
    "AccountLockReason",
    "AuditLogAction",
    "AuditLogStatus"
]
