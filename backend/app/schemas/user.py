from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TokenPayload(BaseModel):
    user_id: int


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=71)
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        return v


class UserLogin(UserBase):
    password: str = Field(..., min_length=1, max_length=71)


class UserUpdate(BaseModel):
    language: Literal["en", "ru"] | None = None
    currency: Literal["USD", "RUB"] | None = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    language: str = "en"
    currency: str = "USD"
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrencyRate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    timestamp: datetime
