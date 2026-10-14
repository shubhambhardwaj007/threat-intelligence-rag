from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIRAG_", env_file=".env", extra="ignore")

    env: str = "dev"                 # dev | prod
    data_dir: str = "./data"         # Colab: a Drive folder; prod: a mounted volume
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    postgres_dsn: str = ""
    nvd_api_key: str = ""            # optional, raises NVD rate limits
    nvd_data_years: tuple[int, int] = (2024, 2026)
    attack_versions: dict[str,str] = {"enterprise-attack": "20.0","ics-attack": "20.0","mobile-attack": "20.0"}
    attack_index_domains: list[str] = ["enterprise-attack"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
