from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_store_dir: str = "/app/model_store"
    tesseract_cmd: str = "/usr/bin/tesseract"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
