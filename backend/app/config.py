from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/tradingintel"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Gupshup WhatsApp BSP
    GUPSHUP_API_KEY: str = ""
    GUPSHUP_APP_NAME: str = ""
    GUPSHUP_SOURCE_NUMBER: str = ""

    # Postmark
    POSTMARK_API_KEY: str = ""
    POSTMARK_FROM_EMAIL: str = "alerts@tradingintel.in"

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    # Application
    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str = "changeme-in-production-secret-key"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
