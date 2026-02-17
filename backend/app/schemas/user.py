from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TokenPayload(BaseModel):
    user_id: int


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(UserBase):
    password: str


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
