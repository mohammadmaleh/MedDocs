from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: str
    id: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    status: str
    user_id: int
    created_at: datetime


class ChatSessionResponse(BaseModel):
    id: int
    created_at: datetime
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    session_id: int
    role: str
    content: str
    created_at: datetime
    id: int
    model_config = ConfigDict(from_attributes=True)
