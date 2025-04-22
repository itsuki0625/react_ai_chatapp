from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # 有効期限（秒）

class TokenData(BaseModel):
    user_id: UUID
    email: EmailStr
    role: List[str]
    exp: int  # 有効期限タイムスタンプ
    jti: str  # JWT ID（一意識別子）

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False
    totp_code: Optional[str] = None  # 二要素認証用

class LoginResponse(BaseModel):
    user: Dict
    token: Token

class ErrorResponse(BaseModel):
    error: Dict[str, str]  # { "code": "error_code", "message": "エラーメッセージ" }

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class EmailVerificationRequest(BaseModel):
    token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        return v

class TwoFactorSetupResponse(BaseModel):
    provisioning_uri: str
    secret: str

class TwoFactorVerifyRequest(BaseModel):
    totp_code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str


