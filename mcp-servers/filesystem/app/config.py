from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_token: str = "change-me-internal-service-token"
    upload_dir: str = "/app/uploads"
    reports_dir: str = "/app/reports"
    max_upload_bytes: int = 25 * 1024 * 1024  # 25 MB

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
