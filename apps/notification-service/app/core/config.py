from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "Notification Service"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: SecretStr = SecretStr("postgresql+asyncpg://showbook:showbook@localhost:5432/showbook_notification")
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    USER_SERVICE_URL: str = "http://localhost:8002"
    
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_SENDER: str = "noreply@showbook.com"
    
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
