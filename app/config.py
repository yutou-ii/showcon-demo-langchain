from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr = Field(validation_alias="OPENAI_API_KEY")
    openai_base_url: str = Field(validation_alias="OPENAI_BASE_URL")
    openai_model: str = Field(validation_alias="OPENAI_MODEL")
    skills_root: Path = Field(
        default=Path("skills"),
        validation_alias="SKILLS_ROOT",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
