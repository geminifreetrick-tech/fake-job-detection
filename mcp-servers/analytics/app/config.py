from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_token: str = "change-me-internal-service-token"
    db_mcp_url: str = "http://db-mcp:8500"
    http_timeout_seconds: float = 8.0
    cache_ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
