from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_token: str = "change-me-internal-service-token"
    google_cse_api_key: str | None = None
    google_cse_engine_id: str | None = None
    # When no API key is set we fall back to a heuristic-only signal so the
    # service still returns something meaningful in dev/offline environments.
    fallback_when_no_key: bool = True
    http_timeout_seconds: float = 10.0
    cache_ttl_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
