from functools import lru_cache
from pydantic_settings import BaseSettings   # <-- updated import
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    POLYGON_API_KEY: str

@lru_cache
def get_settings() -> Settings:
    return Settings()
