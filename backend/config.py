import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Application Meta
    PROJECT_NAME: str = "Enterprise Mobile Application"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database Configuration (MySQL 8.0 Primary)
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "app_user"
    DB_PASSWORD: str = "StrongPassword123!"
    DB_NAME: str = "app_database"
    DATABASE_URL: Optional[str] = None
    
    # JWT Cryptographic Configuration
    JWT_SECRET_KEY: str = "c8b09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OTP Configuration & Rate Limiting
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    OTP_MAX_REQUESTS_PER_HOUR: int = 5
    
    # SMS Delivery Provider (Twilio Integration)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_FROM_PHONE: Optional[str] = None

    @property
    def EFFECTIVE_DATABASE_URL(self) -> str:
        """Returns explicitly set DATABASE_URL or constructs MySQL URL from components."""
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self.DATABASE_URL.strip()
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
