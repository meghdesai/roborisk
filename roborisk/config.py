from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env"):
    OPENROUTER_API_KEY: str
    MONGODB_URI: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
