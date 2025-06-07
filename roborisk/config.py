from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    POLYGON_API_KEY: str
    OPENROUTER_API_KEY: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
