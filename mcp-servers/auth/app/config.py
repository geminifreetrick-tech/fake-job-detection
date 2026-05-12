from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_user: str = "fjd"
    postgres_password: str = "fjd_dev_password"
    postgres_db: str = "fjd"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    jwt_secret: str = "change-me-jwt-signing-secret"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7
    jwt_algorithm: str = "HS256"

    service_token: str = "change-me-internal-service-token"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
