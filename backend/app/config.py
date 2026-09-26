"""
config.py
---------
Loads environment variables from the .env file using pydantic-settings.
All other modules import settings from here — no os.environ calls elsewhere.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Single shared instance — import this object, not the class
settings = Settings()
