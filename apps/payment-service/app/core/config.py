from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "Payment Service"
    API_V1_STR: str = "/api/v1"
    
    # Connects to showbook_booking database (shared with booking-service)
    DATABASE_URL: SecretStr = SecretStr("postgresql+asyncpg://showbook:showbook@localhost:5432/showbook_booking")
    
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    GATEWAY_SECRET: str = "payment_gateway_secret_key"
    PAYMENT_SERVICE_URL: str = "http://localhost:8007"
    
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
