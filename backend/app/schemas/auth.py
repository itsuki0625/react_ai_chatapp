from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True 

class LoginResponse(BaseModel):
    email: EmailStr
    full_name: str
    role: str 

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str 


