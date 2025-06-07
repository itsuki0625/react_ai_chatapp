from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy import func, or_, select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, Role, UserEmailVerification, UserTwoFactorAuth, UserLoginInfo, UserRole as ModelUserRole, UserProfile, RolePermission
from app.models.enums import AccountLockReason
from app.schemas.user import UserCreate, UserUpdate, UserStatus as SchemaUserStatus
from app.core.security import get_password_hash
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import uuid
import logging
from app.crud import crud_role

# --- 追加: ロガーの取得 ---
logger = logging.getLogger(__name__)
# --- ロガー取得ここまで ---

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(
        select(User).options(
            selectinload(User.user_roles)
            .selectinload(ModelUserRole.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission),
            selectinload(User.login_info)
        ).filter(User.id == user_id)
    )
    return result.scalars().first()

async def get_role_by_name(db: AsyncSession, role_name: str) -> Optional[Role]:
    result = await db.execute(select(Role).filter(Role.name == role_name))
    return result.scalars().first()

async def get_multi_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[SchemaUserStatus] = None,
) -> Tuple[List[User], int]:
    stmt = select(User)

    stmt = stmt.options(
        selectinload(User.user_roles).selectinload(ModelUserRole.role),
        selectinload(User.login_info)
    )

    if search:
        search_term = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(User.full_name).like(search_term),
                func.lower(User.email).like(search_term)
            )
        )

    if role:
        stmt = stmt.join(User.user_roles).join(ModelUserRole.role).where(Role.name == role)

    if status:
        stmt = stmt.where(User.status == status)

    count_stmt = select(func.count()).select_from(stmt.alias())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().unique().all()

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

async def create_user(db: AsyncSession, *, user_in: UserCreate) -> User:
    logger.info(f"Attempting to create user with email: {user_in.email}")
    role_name = user_in.role
    db_role = await crud_role.get_role_by_name(db, role_name)
    if not db_role:
        # Ensure this part is handled correctly, maybe raise an error or log as critical
        logger.error(f"Role '{role_name}' not found in database during user creation for {user_in.email}.")
        raise ValueError(f"Role '{role_name}' not found in database.")

    db_user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        status=SchemaUserStatus.ACTIVE, # Default status, ensure this is intended
        is_verified=True, # Default verification, ensure this is intended
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    await db.flush() # db_user.id is available after flush
    logger.info(f"User object created and flushed for email: {user_in.email}, user_id: {db_user.id}")

    user_role_assoc = ModelUserRole(
        user_id=db_user.id,
        role_id=db_role.id,
        is_primary=True
    )
    db.add(user_role_assoc)
    logger.info(f"UserRole association created for user_id: {db_user.id}")

    try:
        email_verification = UserEmailVerification(
            id=uuid.uuid4(), user_id=db_user.id, email_verified=False, created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        db.add(email_verification)
        logger.info(f"UserEmailVerification object created for user_id: {db_user.id}")
        
        logger.info(f"Attempting to create UserLoginInfo for user_id: {db_user.id}")
        login_info = UserLoginInfo(
            id=uuid.uuid4(),
            user_id=db_user.id, # Ensure this is correct
            failed_login_attempts=0,
            # last_login_at is intentionally left null on creation
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(login_info)
        logger.info(f"UserLoginInfo object added to session for user_id: {db_user.id}")

        logger.info(f"Attempting to commit all new records for user: {user_in.email}")
        await db.commit()
        logger.info(f"Successfully committed new user and related records for email: {user_in.email}")
        
        # コミット後に関連情報を含めてユーザーを再取得して返す
        loaded_user = await get_user(db, db_user.id)
        if not loaded_user:
             # 通常ここには到達しないはずだが、念のためエラーハンドリング
             logger.error(f"Failed to reload user {db_user.id} after creation.")
             raise ValueError(f"Failed to reload user {db_user.id} after creation.")
        return loaded_user

    except Exception as e:
        logger.error(f"Error during commit or related record creation for {user_in.email}: {e}", exc_info=True)
        await db.rollback()
        logger.info(f"Rolled back transaction for user: {user_in.email}")
        raise e

async def update_user(
    db: AsyncSession,
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
        elif isinstance(status_value, str):
            try:
                db_user.status = SchemaUserStatus(status_value)
            except ValueError:
                logger.warning(f"Invalid status value '{status_value}' received for update.")
        del update_data["status"]

    if "role" in update_data and update_data["role"] is not None:
        new_role_name: str = update_data["role"]

        new_role_db = await crud_role.get_role_by_name(db, new_role_name)

        if new_role_db:
            current_user_role_result = await db.execute(
                select(ModelUserRole).filter(
                    ModelUserRole.user_id == db_user.id,
                    ModelUserRole.is_primary == True
                )
            )
            current_user_role = current_user_role_result.scalars().first()

            if current_user_role:
                if current_user_role.role_id != new_role_db.id:
                    logger.info(f"Updating primary role for user {db_user.id} from {current_user_role.role_id} to {new_role_db.id} ({new_role_name})")
                    current_user_role.role_id = new_role_db.id
                    db.add(current_user_role)
                    # ★ デバッグ用: セッションから最新の値を確認
                    logger.info(f"Role ID updated in session - User: {db_user.id}, New Role ID: {current_user_role.role_id}")
                else:
                    logger.info(f"User {db_user.id} already has primary role '{new_role_name}'. No change needed.")
            else:
                logger.warning(f"Primary UserRole association not found for user {db_user.id}. Creating new one for role '{new_role_name}'.")
                new_user_role_assoc = ModelUserRole(
                    user_id=db_user.id,
                    role_id=new_role_db.id,
                    is_primary=True
                )
                db.add(new_user_role_assoc)
        else:
            logger.error(f"Role '{new_role_name}' was not found during update process for user {db_user.id}. This should have been caught earlier.")

        del update_data["role"]

    for field, value in update_data.items():
        if hasattr(db_user, field):
            setattr(db_user, field, value)
        elif field in ['grade', 'class_number', 'student_number']:
            if not db_user.profile:
                 db_user.profile = UserProfile(user_id=db_user.id)
                 db.add(db_user.profile)

    db_user.updated_at = datetime.utcnow()
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def remove_user(db: AsyncSession, *, user_id: UUID) -> Optional[User]:
    user = await get_user(db, user_id)
    if user:
        logger.info(f"Deleting user object for user {user_id}")
        await db.delete(user)
        await db.commit()
        logger.info(f"Successfully deleted user {user_id}")
        return user
    logger.warning(f"User with ID {user_id} not found for deletion.")
    return None

async def verify_user_email(db: AsyncSession, user_id: UUID) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    user.is_verified = True
    if hasattr(user, 'email_verification') and user.email_verification:
        user.email_verification.email_verified = True
        user.email_verification.updated_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def setup_2fa(db: AsyncSession, user_id: UUID, totp_secret: str) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    user.is_2fa_enabled = True
    user.totp_secret = totp_secret
    user.updated_at = datetime.utcnow()
    result = await db.execute(select(UserTwoFactorAuth).filter(UserTwoFactorAuth.user_id == user_id))
    two_factor_auth = result.scalars().first()
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
    await db.commit()
    return True

async def disable_2fa(db: AsyncSession, user_id: UUID) -> bool:
    user = await get_user(db, user_id)
    if not user:
        return False
    user.is_2fa_enabled = False
    user.totp_secret = None
    user.updated_at = datetime.utcnow()
    result = await db.execute(select(UserTwoFactorAuth).filter(UserTwoFactorAuth.user_id == user_id))
    two_factor_auth = result.scalars().first()
    if two_factor_auth:
        two_factor_auth.enabled = False
        two_factor_auth.secret = None
        two_factor_auth.updated_at = datetime.utcnow()
    await db.commit()
    return True

async def record_login_attempt(db: AsyncSession, user_id: UUID, success: bool) -> None:
    logger.info(f"Attempting to record login for user_id: {user_id}, success: {success}")
    user = await get_user(db, user_id)
    if not user:
        logger.warning(f"User not found in record_login_attempt for user_id: {user_id}")
        return

    result = await db.execute(select(UserLoginInfo).filter(UserLoginInfo.user_id == user_id))
    login_info = result.scalars().first()

    if not login_info:
        logger.warning(f"UserLoginInfo not found for user_id: {user_id}")
        # Consider adding logic here to create UserLoginInfo if it doesn't exist
        # login_info = UserLoginInfo(user_id=user_id, created_at=datetime.utcnow())
        # db.add(login_info)
        # logger.info(f"Created new UserLoginInfo for user_id: {user_id}")
        return # Or handle as appropriate

    now = datetime.utcnow()
    logger.info(f"Current time (UTC): {now}")

    if success:
        logger.info(f"Login successful for user_id: {user_id}. Current last_login_at: {login_info.last_login_at}")
        login_info.last_login_at = now
        login_info.failed_login_attempts = 0
        login_info.locked_until = None
        login_info.account_lock_reason = None
        logger.info(f"Updated last_login_at to: {login_info.last_login_at} for user_id: {user_id}")
    else:
        logger.info(f"Login failed for user_id: {user_id}")
        if hasattr(login_info, 'last_failed_login_at'): # Keep this check for last_failed_login_at
            login_info.last_failed_login_at = now
        login_info.failed_login_attempts += 1
        if login_info.failed_login_attempts >= 5: # Threshold should be configurable
            login_info.locked_until = now + timedelta(minutes=15) # Lock duration should be configurable
            login_info.account_lock_reason = AccountLockReason.FAILED_ATTEMPTS
    
    login_info.updated_at = now
    try:
        db.add(login_info)
        await db.commit()
        await db.refresh(login_info) # Refresh to get the latest state from DB
        logger.info(f"Successfully committed UserLoginInfo for user_id: {user_id}. Refreshed last_login_at: {login_info.last_login_at}")
    except Exception as e:
        logger.error(f"Error committing UserLoginInfo for user_id: {user_id}: {e}", exc_info=True)
        await db.rollback()

async def is_account_locked(db: AsyncSession, user_id: UUID) -> bool:
    user = await get_user(db, user_id)
    result = await db.execute(select(UserLoginInfo).filter(UserLoginInfo.user_id == user_id))
    login_info = result.scalars().first()
    if not user or not login_info:
        return False
    now = datetime.utcnow()
    if login_info.locked_until and login_info.locked_until > now:
        return True
    if login_info.locked_until:
        login_info.locked_until = None
        login_info.account_lock_reason = None
        db.add(login_info)
        await db.commit()
    return False

