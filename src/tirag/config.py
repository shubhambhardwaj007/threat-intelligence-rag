from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIRAG_", env_file=".env", extra="ignore")

    env: str = "dev"                 # dev | prod
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    postgres_dsn: str = ""
    nvd_api_key: str = ""            # optional, raises NVD rate limits


@lru_cache
def get_settings() -> Settings:
    return Settings()
