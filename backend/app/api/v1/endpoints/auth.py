from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from app.core.security import verify_password, get_password_hash
from app.crud.user import get_user_by_email, create_user
from app.api.deps import get_db
from app.schemas.auth import Token, LoginResponse, SignUpRequest
from app.api.deps import get_current_user, User
from fastapi.responses import JSONResponse
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        user = get_user_by_email(db, email=form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        request.session["role"] = user.role.permissions

        # 明示的にJSONレスポンスを返す
        return JSONResponse(content={
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.permissions
        })
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=dict)
async def read_users_me(request: Request) -> Any:
    """
    Get current user.
    """
    if "user_id" not in request.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return {
        "user_id": request.session["user_id"],
        "email": request.session["email"],
        "role": request.session["role"]
    }

@router.get("/test-auth", response_model=dict)
async def test_auth(current_user: User = Depends(get_current_user)):
    """
    認証テスト用エンドポイント
    """
    return {
        "message": "認証成功",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.name
        }
    }

@router.post("/signup", response_model=dict)
async def signup(
    request: Request,
    user_data: SignUpRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    新規ユーザー登録
    """
    try:
        # メールアドレスの重複チェック
        existing_user = get_user_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # パスワードのハッシュ化
        hashed_password = get_password_hash(user_data.password)
        
        # ユーザーの作成
        user = create_user(
            db=db,
            email=user_data.email,
            password=hashed_password,
            full_name=user_data.full_name
        )
        
        # セッションにユーザー情報を保存
        request.session["user_id"] = str(user.id)
        request.session["email"] = user.email
        request.session["role"] = user.role.permissions
        
        return {
            "message": "User created successfully",
            "user": {
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.permissions
            }
        }
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 