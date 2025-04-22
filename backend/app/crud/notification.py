from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationSetting, BroadcastNotification
from app.models.notification import NotificationMetaData, BroadcastNotificationMetaData, BroadcastTargetRole
from app.schemas.notification import (
    NotificationCreate, NotificationUpdate, NotificationSettingCreate, NotificationSettingUpdate,
    BroadcastNotificationCreate, BroadcastNotificationUpdate
)
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy import desc

# 通知のCRUD操作
def create_notification(db: Session, notification: NotificationCreate) -> Notification:
    """新しい通知を作成する"""
    db_notification = Notification(
        id=uuid.uuid4(),
        user_id=notification.user_id,
        title=notification.title,
        content=notification.content,
        notification_type=notification.notification_type,
        related_entity_type=notification.related_entity_type,
        related_entity_id=notification.related_entity_id,
        broadcast_notification_id=notification.broadcast_notification_id,
        is_read=False,
        is_action_required=notification.is_action_required,
        action_url=notification.action_url,
        sent_at=datetime.utcnow(),
        expires_at=notification.expires_at,
        priority=notification.priority
    )
    db.add(db_notification)
    
    # メタデータがあれば追加
    if notification.metadata:
        for key, value in notification.metadata.items():
            metadata = NotificationMetaData(
                id=uuid.uuid4(),
                notification_id=db_notification.id,
                key=key,
                value=str(value)
            )
            db.add(metadata)
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification(db: Session, notification_id: UUID) -> Optional[Notification]:
    """特定の通知を取得する"""
    return db.query(Notification).filter(Notification.id == notification_id).first()

def get_user_notifications(db: Session, user_id: UUID, skip: int = 0, limit: int = 50) -> List[Notification]:
    """ユーザーの通知一覧を取得する"""
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(
        desc(Notification.sent_at)
    ).offset(skip).limit(limit).all()

def get_unread_notifications(db: Session, user_id: UUID, limit: int = 20) -> List[Notification]:
    """ユーザーの未読通知一覧を取得する"""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).order_by(
        desc(Notification.sent_at)
    ).limit(limit).all()

def mark_notification_as_read(db: Session, notification_id: UUID) -> Optional[Notification]:
    """通知を既読にする"""
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if db_notification:
        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notification)
    return db_notification

def mark_all_notifications_as_read(db: Session, user_id: UUID) -> int:
    """ユーザーの全通知を既読にする"""
    now = datetime.utcnow()
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": now
    })
    db.commit()
    return result

def delete_notification(db: Session, notification_id: UUID) -> bool:
    """通知を削除する"""
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if db_notification:
        db.delete(db_notification)
        db.commit()
        return True
    return False

# 通知設定のCRUD操作
def get_notification_settings(db: Session, user_id: UUID) -> List[NotificationSetting]:
    """ユーザーの通知設定一覧を取得する"""
    return db.query(NotificationSetting).filter(
        NotificationSetting.user_id == user_id
    ).all()

def get_notification_setting(db: Session, user_id: UUID, notification_type: str) -> Optional[NotificationSetting]:
    """特定の通知タイプの設定を取得する"""
    return db.query(NotificationSetting).filter(
        NotificationSetting.user_id == user_id,
        NotificationSetting.notification_type == notification_type
    ).first()

def create_notification_setting(db: Session, setting: NotificationSettingCreate) -> NotificationSetting:
    """通知設定を作成する"""
    db_setting = NotificationSetting(
        id=uuid.uuid4(),
        user_id=setting.user_id,
        notification_type=setting.notification_type,
        email_enabled=setting.email_enabled,
        push_enabled=setting.push_enabled,
        in_app_enabled=setting.in_app_enabled,
        quiet_hours_start=setting.quiet_hours_start,
        quiet_hours_end=setting.quiet_hours_end
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def update_notification_setting(db: Session, user_id: UUID, setting_update: NotificationSettingUpdate) -> Optional[NotificationSetting]:
    """通知設定を更新する"""
    db_setting = db.query(NotificationSetting).filter(
        NotificationSetting.user_id == user_id,
        NotificationSetting.notification_type == setting_update.notification_type
    ).first()
    
    if not db_setting:
        # 設定が存在しない場合は作成
        return create_notification_setting(db, NotificationSettingCreate(
            user_id=user_id,
            notification_type=setting_update.notification_type,
            email_enabled=setting_update.email_enabled,
            push_enabled=setting_update.push_enabled,
            in_app_enabled=setting_update.in_app_enabled,
            quiet_hours_start=setting_update.quiet_hours_start,
            quiet_hours_end=setting_update.quiet_hours_end
        ))
    
    # 既存の設定を更新
    if setting_update.email_enabled is not None:
        db_setting.email_enabled = setting_update.email_enabled
    if setting_update.push_enabled is not None:
        db_setting.push_enabled = setting_update.push_enabled
    if setting_update.in_app_enabled is not None:
        db_setting.in_app_enabled = setting_update.in_app_enabled
    if setting_update.quiet_hours_start is not None:
        db_setting.quiet_hours_start = setting_update.quiet_hours_start
    if setting_update.quiet_hours_end is not None:
        db_setting.quiet_hours_end = setting_update.quiet_hours_end
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

def initialize_default_notification_settings(db: Session, user_id: UUID) -> List[NotificationSetting]:
    """ユーザーのデフォルト通知設定を初期化する"""
    # 全通知タイプのデフォルト設定を作成
    notification_types = [
        "CHAT_MESSAGE", "DOCUMENT_DEADLINE", "EVENT_REMINDER", 
        "SUBSCRIPTION_RENEWAL", "FEEDBACK_RECEIVED", "SYSTEM_ANNOUNCEMENT"
    ]
    
    settings = []
    for notification_type in notification_types:
        # 既存の設定があるかチェック
        existing = get_notification_setting(db, user_id, notification_type)
        if not existing:
            setting = NotificationSetting(
                id=uuid.uuid4(),
                user_id=user_id,
                notification_type=notification_type,
                email_enabled=True,
                push_enabled=True,
                in_app_enabled=True
            )
            db.add(setting)
            settings.append(setting)
    
    if settings:
        db.commit()
        # refresh the objects
        for i, setting in enumerate(settings):
            db.refresh(setting)
            settings[i] = setting
    
    return settings

# 全体通知のCRUD操作
def create_broadcast_notification(db: Session, broadcast: BroadcastNotificationCreate, created_by: UUID) -> BroadcastNotification:
    """全体通知を作成する"""
    db_broadcast = BroadcastNotification(
        id=uuid.uuid4(),
        title=broadcast.title,
        content=broadcast.content,
        notification_type=broadcast.notification_type,
        action_url=broadcast.action_url,
        created_by=created_by,
        scheduled_at=broadcast.scheduled_at,
        expires_at=broadcast.expires_at,
        priority=broadcast.priority,
        is_active=True
    )
    db.add(db_broadcast)
    db.flush()  # IDを取得するためにflush
    
    # 対象ロールを設定
    if broadcast.target_roles:
        for role_id in broadcast.target_roles:
            target_role = BroadcastTargetRole(
                id=uuid.uuid4(),
                broadcast_notification_id=db_broadcast.id,
                role_id=role_id
            )
            db.add(target_role)
    
    # メタデータを設定
    if broadcast.metadata:
        for key, value in broadcast.metadata.items():
            metadata = BroadcastNotificationMetaData(
                id=uuid.uuid4(),
                broadcast_notification_id=db_broadcast.id,
                key=key,
                value=str(value)
            )
            db.add(metadata)
    
    db.commit()
    db.refresh(db_broadcast)
    return db_broadcast

def get_broadcast_notification(db: Session, broadcast_id: UUID) -> Optional[BroadcastNotification]:
    """特定の全体通知を取得する"""
    return db.query(BroadcastNotification).filter(BroadcastNotification.id == broadcast_id).first()

def get_active_broadcast_notifications(db: Session) -> List[BroadcastNotification]:
    """有効な全体通知一覧を取得する"""
    now = datetime.utcnow()
    return db.query(BroadcastNotification).filter(
        BroadcastNotification.is_active == True,
        (BroadcastNotification.expires_at == None) | (BroadcastNotification.expires_at > now),
        (BroadcastNotification.scheduled_at == None) | (BroadcastNotification.scheduled_at <= now)
    ).order_by(
        desc(BroadcastNotification.created_at)
    ).all()

def update_broadcast_notification(db: Session, broadcast_id: UUID, broadcast_update: BroadcastNotificationUpdate) -> Optional[BroadcastNotification]:
    """全体通知を更新する"""
    db_broadcast = db.query(BroadcastNotification).filter(BroadcastNotification.id == broadcast_id).first()
    if not db_broadcast:
        return None
    
    # 基本情報を更新
    if broadcast_update.title is not None:
        db_broadcast.title = broadcast_update.title
    if broadcast_update.content is not None:
        db_broadcast.content = broadcast_update.content
    if broadcast_update.notification_type is not None:
        db_broadcast.notification_type = broadcast_update.notification_type
    if broadcast_update.action_url is not None:
        db_broadcast.action_url = broadcast_update.action_url
    if broadcast_update.scheduled_at is not None:
        db_broadcast.scheduled_at = broadcast_update.scheduled_at
    if broadcast_update.expires_at is not None:
        db_broadcast.expires_at = broadcast_update.expires_at
    if broadcast_update.priority is not None:
        db_broadcast.priority = broadcast_update.priority
    if broadcast_update.is_active is not None:
        db_broadcast.is_active = broadcast_update.is_active
    
    # 対象ロールを更新
    if broadcast_update.target_roles is not None:
        # 既存のロールをすべて削除
        db.query(BroadcastTargetRole).filter(
            BroadcastTargetRole.broadcast_notification_id == broadcast_id
        ).delete()
        
        # 新しいロールを追加
        for role_id in broadcast_update.target_roles:
            target_role = BroadcastTargetRole(
                id=uuid.uuid4(),
                broadcast_notification_id=db_broadcast.id,
                role_id=role_id
            )
            db.add(target_role)
    
    db.commit()
    db.refresh(db_broadcast)
    return db_broadcast

def mark_broadcast_as_sent(db: Session, broadcast_id: UUID) -> Optional[BroadcastNotification]:
    """全体通知を送信済みにする"""
    db_broadcast = db.query(BroadcastNotification).filter(BroadcastNotification.id == broadcast_id).first()
    if db_broadcast:
        db_broadcast.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(db_broadcast)
    return db_broadcast

def get_pending_broadcasts(db: Session) -> List[BroadcastNotification]:
    """送信待ちの全体通知一覧を取得する"""
    now = datetime.utcnow()
    return db.query(BroadcastNotification).filter(
        BroadcastNotification.is_active == True,
        BroadcastNotification.sent_at == None,
        (BroadcastNotification.scheduled_at == None) | (BroadcastNotification.scheduled_at <= now)
    ).order_by(
        BroadcastNotification.created_at
    ).all()

def send_test_notification(db: Session, user_id: UUID, notification_type: str = "SYSTEM_ANNOUNCEMENT") -> Notification:
    """テスト通知を送信する"""
    test_notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        title="テスト通知",
        content="これはテスト通知です。通知設定が正しく機能しているかを確認します。",
        notification_type=notification_type,
        is_read=False,
        is_action_required=False,
        sent_at=datetime.utcnow(),
        priority="NORMAL"
    )
    db.add(test_notification)
    db.commit()
    db.refresh(test_notification)
    return test_notification 