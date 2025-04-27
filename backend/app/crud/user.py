from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy import func, or_
from app.models.user import User, Role, UserEmailVerification, UserTwoFactorAuth, UserLoginInfo, UserRole as ModelUserRole, UserProfile
from app.models.enums import AccountLockReason
from app.schemas.user import UserCreate, UserUpdate, UserRole as SchemaUserRole, UserStatus as SchemaUserStatus
from app.core.security import get_password_hash
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import uuid
import logging

# --- 追加: ロガーの取得 ---
logger = logging.getLogger(__name__)
# --- ロガー取得ここまで ---

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    # Ensure necessary relations are loaded for UserResponse computed fields
    return db.query(User).options(
        selectinload(User.user_roles).selectinload(ModelUserRole.role), # Needed for computed role
        selectinload(User.login_info) # Needed for computed last_login_at
    ).filter(User.id == user_id).first()

def get_role_by_name(db: Session, role_name: str) -> Optional[Role]:
    return db.query(Role).filter(Role.name == role_name).first()

def get_multi_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[SchemaUserRole] = None,
    status: Optional[SchemaUserStatus] = None,
) -> Tuple[List[User], int]:
    query = db.query(User)

    query = query.options(
        selectinload(User.user_roles).selectinload(ModelUserRole.role),
        selectinload(User.login_info)
    )

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(User.full_name).like(search_term),
                func.lower(User.email).like(search_term)
            )
        )

    if role:
        query = query.join(User.user_roles).join(ModelUserRole.role).filter(Role.name == role.value)

    if status:
        query = query.filter(User.status == status)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    if users:
        logger.info(f"CRUD: Fetched user 0 full_name: {getattr(users[0], 'full_name', 'N/A')}")
        try:
            logger.info(f"CRUD: Fetched user 0 ORM object dict (basic): {users[0].__dict__}")
            if hasattr(users[0], 'user_roles') and users[0].user_roles:
                 logger.info(f"CRUD: Fetched user 0 role name (first): {getattr(users[0].user_roles[0].role, 'name', 'N/A')}")
            if hasattr(users[0], 'login_info') and users[0].login_info:
                logger.info(f"CRUD: Fetched user 0 last_login_at: {getattr(users[0].login_info, 'last_login_at', 'N/A')}")
            else:
                logger.info("CRUD: Fetched user 0 login_info not found or None.")
        except Exception as e:
            logger.error(f"Error logging user object details: {e}")
    else:
        logger.info("CRUD: No users found.")

    return users, total

def create_user(db: Session, *, user_in: UserCreate) -> User:
    role_name = user_in.role.value
    db_role = get_role_by_name(db, role_name)
    if not db_role:
        raise ValueError(f"Role '{role_name}' not found in database.")

    db_user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        status=user_in.status,
        is_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.flush()

    user_role_assoc = ModelUserRole(
        user_id=db_user.id,
        role_id=db_role.id,
        is_primary=True
    )
    db.add(user_role_assoc)

    try:
        email_verification = UserEmailVerification(
            id=uuid.uuid4(), user_id=db_user.id, email_verified=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        db.add(email_verification)
        login_info = UserLoginInfo(
            id=uuid.uuid4(), user_id=db_user.id, failed_login_attempts=0, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        db.add(login_info)
        db.commit()
        db.refresh(db_user, attribute_names=['user_roles', 'user_roles.role'])
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user and related records for {user_in.email}: {e}")
        raise e

    return db_user

def update_user(
    db: Session,
    *,
    db_user: User,
    user_in: UserUpdate
) -> User:
    update_data = user_in.model_dump(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password
        del update_data["password"]
    elif "password" in update_data:
        del update_data["password"]

    if "status" in update_data:
        status_value = update_data["status"]
        if isinstance(status_value, SchemaUserStatus):
            db_user.status = status_value
        del update_data["status"]

    if "role" in update_data:
        new_role_enum = update_data.get("role")
        if isinstance(new_role_enum, SchemaUserRole):
            new_role_name = new_role_enum.value
            logger.warning(f"Updating user role for {db_user.email} to {new_role_name}. Simplified logic - assumes single primary role update.")
            current_user_role = db.query(ModelUserRole).filter(ModelUserRole.user_id == db_user.id, ModelUserRole.is_primary == True).first()
            if current_user_role:
                new_role_db = get_role_by_name(db, new_role_name)
                if new_role_db:
                    if current_user_role.role_id != new_role_db.id:
                        current_user_role.role = new_role_db
                        db.add(current_user_role)
                else:
                     logger.error(f"Role '{new_role_name}' not found for update.")
            else:
                logger.error(f"Primary UserRole association not found for user {db_user.id}")
        del update_data["role"]

    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
        elif field in ['grade', 'class_number', 'student_number', 'profile_image_url']:
            if not db_user.profile:
                 db_user.profile = UserProfile(user_id=db_user.id)
                 db.add(db_user.profile)
            setattr(db_user.profile, field, value)

    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def remove_user(db: Session, *, user_id: UUID) -> Optional[User]:
    user = db.query(User).get(user_id)
    if user:
        db.query(UserEmailVerification).filter(UserEmailVerification.user_id == user_id).delete(synchronize_session=False)
        db.query(UserLoginInfo).filter(UserLoginInfo.user_id == user_id).delete(synchronize_session=False)
        db.query(UserTwoFactorAuth).filter(UserTwoFactorAuth.user_id == user_id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
        return user
    return None

def verify_user_email(db: Session, user_id: UUID) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    user.is_verified = True
    if hasattr(user, 'email_verification') and user.email_verification:
        user.email_verification.email_verified = True
        user.email_verification.updated_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    db.commit()
    return True

def setup_2fa(db: Session, user_id: UUID, totp_secret: str) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    user.is_2fa_enabled = True
    user.totp_secret = totp_secret
    user.updated_at = datetime.utcnow()
    two_factor_auth = db.query(UserTwoFactorAuth).filter(UserTwoFactorAuth.user_id == user_id).first()
    if two_factor_auth:
        two_factor_auth.enabled = True
        two_factor_auth.secret = totp_secret
        two_factor_auth.updated_at = datetime.utcnow()
    else:
        two_factor_auth = UserTwoFactorAuth(
            id=uuid.uuid4(),
            user_id=user.id,
            enabled=True,
            secret=totp_secret,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(two_factor_auth)
    db.commit()
    return True

def disable_2fa(db: Session, user_id: UUID) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    user.is_2fa_enabled = False
    user.totp_secret = None
    user.updated_at = datetime.utcnow()
    two_factor_auth = db.query(UserTwoFactorAuth).filter(UserTwoFactorAuth.user_id == user_id).first()
    if two_factor_auth:
        two_factor_auth.enabled = False
        two_factor_auth.secret = None
        two_factor_auth.updated_at = datetime.utcnow()
    db.commit()
    return True

def record_login_attempt(db: Session, user_id: UUID, success: bool) -> None:
    user = get_user(db, user_id)
    login_info = db.query(UserLoginInfo).filter(UserLoginInfo.user_id == user_id).first()
    if not user or not login_info:
         print(f"User or login info not found for user_id: {user_id}")
         return
    now = datetime.utcnow()
    if success:
        if hasattr(login_info, 'last_login_at'):
            login_info.last_login_at = now
        login_info.failed_login_attempts = 0
        login_info.locked_until = None
        login_info.account_lock_reason = None
    else:
        if hasattr(login_info, 'last_failed_login_at'):
            login_info.last_failed_login_at = now
        login_info.failed_login_attempts += 1
        if login_info.failed_login_attempts >= 5:
            login_info.locked_until = now + timedelta(minutes=15)
            login_info.account_lock_reason = AccountLockReason.FAILED_ATTEMPTS
    login_info.updated_at = now
    db.add(login_info)
    db.commit()

def is_account_locked(db: Session, user_id: UUID) -> bool:
    user = get_user(db, user_id)
    login_info = db.query(UserLoginInfo).filter(UserLoginInfo.user_id == user_id).first()
    if not user or not login_info:
        return False
    now = datetime.utcnow()
    if login_info.locked_until and login_info.locked_until > now:
        return True
    if login_info.locked_until:
        login_info.locked_until = None
        login_info.account_lock_reason = None
        db.add(login_info)
        db.commit()
    return False

