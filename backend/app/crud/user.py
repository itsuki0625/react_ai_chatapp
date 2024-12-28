from sqlalchemy.orm import Session
from app.models.user import User, Role
from uuid import UUID

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role_name: str = "生徒",
    school_id: UUID | None = None
) -> User:
    """
    新規ユーザーを作成する

    Args:
        db: データベースセッション
        email: メールアドレス
        password: ハッシュ化されたパスワード
        full_name: フルネーム
        role_id: ロールID
        school_id: 学校ID（オプション）

    Returns:
        作成されたユーザーオブジェクト
    """
    role_id = get_role_id(db, role_name)
    try:
        user = User(
            email=email,
            hashed_password=password,
            full_name=full_name,
            role_id=role_id,
            school_id=school_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {str(e)}")  # エラーログを追加
        raise

# role_idを取得する
def get_role_id(db: Session, role_name: str) -> UUID:
    return db.query(Role).filter(Role.name == role_name).first().id

