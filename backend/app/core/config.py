from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-here"
    DATABASE_URL: str = "postgresql+asyncpg://scrooge:password@db/scrooge_db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:80", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
