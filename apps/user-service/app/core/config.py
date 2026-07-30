from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "User Service"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: SecretStr = SecretStr("postgresql+asyncpg://showbook:showbook@localhost:5432/showbook_user")
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_password"
    
    JWT_SECRET: SecretStr = SecretStr("88793a8c1873271f85bc9ec9585785a06145770118fa88e4bc84669b2464c2f1")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRY: int = 30  # minutes
    REFRESH_TOKEN_EXPIRY: int = 7   # days
    
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"
    
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_FROM: str = "noreply@showbook.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
