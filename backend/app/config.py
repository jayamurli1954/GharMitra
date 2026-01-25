"""
Application configuration using Pydantic Settings
Loads environment variables from .env file
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./gharmitra.db"
    DATABASE_ECHO: bool = False  # Set to True to see SQL queries in logs

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # Application
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # Default port (can be overridden in .env)

    # CORS
    # In development, allow all origins for mobile device access
    # In production, specify exact origins (including Vercel deployments)
    ALLOWED_ORIGINS: str = "http://localhost:19006,http://localhost:3000,http://localhost:3001,http://localhost:3005,http://localhost:3006,https://gharmitra.vercel.app,https://*.vercel.app"
    API_VERSION: str = "v1"
    APP_NAME: str = "GharMitra API"

    # Email (Optional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@gharmitra.com"

    # File Upload
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    UPLOAD_DIR: str = "./uploads"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Encryption (for sensitive fields like storage_location, verification_notes)
    ENCRYPTION_KEY: str = ""  # Must be set in .env file (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")

    # Deployment Mode: "standalone" (local installation) or "saas" (cloud-hosted)
    DEPLOYMENT_MODE: str = "saas"  # Default to SaaS mode

    # Logging
    LOG_LEVEL: str = "INFO"

    # Razorpay Payment Gateway
    RAZORPAY_KEY_ID: str = ""  # Get from Razorpay Dashboard
    RAZORPAY_KEY_SECRET: str = ""  # Get from Razorpay Dashboard
    RAZORPAY_WEBHOOK_SECRET: str = ""  # Set in Razorpay Webhook settings
    RAZORPAY_ENABLED: bool = False  # Enable when keys are configured
    RAZORPAY_LOGO_URL: str = ""  # Society logo URL for checkout
    RAZORPAY_CONVENIENCE_FEE_PERCENTAGE: float = 2.0  # 2% convenience fee
    RAZORPAY_CONVENIENCE_FEE_BEARER: str = "member"  # "member" or "society" or "shared"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables (like frontend API_URL, APP_VERSION, NODE_ENV)

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Create settings instance
settings = Settings()
