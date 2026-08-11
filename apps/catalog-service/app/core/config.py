import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator

current_dir = os.path.dirname(os.path.abspath(__file__))
service_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
env_path = os.path.join(service_dir, ".env")

class Settings(BaseSettings):
    DATABASE_URL: SecretStr
    TESTING: bool = False
    LOG_LEVEL: str = "INFO"

    # Redis config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = "6379"
    REDIS_PASSWORD: Optional[str] = None

    # Service integrations
    VENUE_SERVICE_URL: str = "http://localhost:8001"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: SecretStr) -> SecretStr:
        raw_val = v.get_secret_value()
        if raw_val.startswith("postgresql://"):
            new_val = raw_val.replace("postgresql://", "postgresql+asyncpg://", 1)
            return SecretStr(new_val)
        return v

    class Config:
        env_file = env_path
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
