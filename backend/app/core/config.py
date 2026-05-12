from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_mcp_url: str = "http://auth-mcp:8700"
    db_mcp_url: str = "http://db-mcp:8500"
    ml_engine_url: str = "http://ml-engine:8100"
    memory_mcp_url: str = "http://memory-mcp:8200"

    service_token: str = "change-me-internal-service-token"
    jwt_secret: str = "change-me-jwt-signing-secret"
    jwt_algorithm: str = "HS256"

    backend_cors_origins: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.backend_cors_origins.split(",") if o.strip()]


settings = Settings()
