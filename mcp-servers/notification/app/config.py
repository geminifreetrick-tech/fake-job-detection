from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_token: str = "change-me-internal-service-token"

    # SMTP. When SMTP_HOST is blank we run in "console" mode: emails are
    # logged but not actually sent, which is convenient for local dev and CI.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    email_from: str = "no-reply@fake-job-detection.local"

    # Where to fan-out websocket pushes
    backend_url: str = "http://backend:8000"

    db_mcp_url: str = "http://db-mcp:8500"
    http_timeout_seconds: float = 8.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
