from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"
    ADMIN_HOST: str = "0.0.0.0"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    SECRET_KEY: str = "your-secret-key-change-in-production-1234567890"
    MONGO_URL: Optional[str] = "mongodb://localhost:27017"
    DB_NAME: Optional[str] = "test_database"
    CORS_ORIGINS: Optional[str] = "*"
    
    # Phase 9: Hardening and Limits
    RATE_LIMIT_REQUESTS: int = 60  # Requests per window
    RATE_LIMIT_WINDOW: int = 60  # Window size in seconds
    MAX_RESPONSE_SIZE_MB: int = 15  # Max response size for non-media content
    REQUEST_TIMEOUT: int = 15  # Request timeout in seconds
    ENABLE_RATE_LIMITING: bool = True  # Toggle rate limiting
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()
