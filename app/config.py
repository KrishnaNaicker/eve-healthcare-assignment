"""Central settings loaded from environment variables or a local .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://eve_user:eve_password@localhost:5432/eve_healthcare"
    jwt_secret_key: str = "local-development-only-change-me"
    jwt_access_token_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
