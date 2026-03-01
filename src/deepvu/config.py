from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    DATABASE_URL: str = "postgresql+asyncpg://deepvu:deepvu_dev@localhost:5432/deepvu"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    RATE_LIMIT_PER_USER: int = 100
    RATE_LIMIT_PER_TENANT: int = 1000

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""


settings = Settings()
