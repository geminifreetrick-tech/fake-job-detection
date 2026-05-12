from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    service_token: str = "change-me-internal-service-token"

    # Names of collections we manage.
    collection_user_context: str = "user_context"
    collection_known_scams: str = "known_scams"
    collection_articles: str = "articles"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
