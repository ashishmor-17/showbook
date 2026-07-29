from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    PROJECT_NAME: str = "Venue Service"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: SecretStr = SecretStr("postgresql+asyncpg://venue_service:venue_password@localhost:5432/showbook_venue")
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redis_password"
    
    INVENTORY_SERVICE_URL: str = "http://localhost:8005"
    
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
