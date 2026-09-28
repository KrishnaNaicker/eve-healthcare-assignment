from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://eve_user:eve_password@localhost:5432/eve_healthcare"
    jwt_secret_key: str = "local-development-secret-change-before-deployment-32chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 30
    admin_email: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
