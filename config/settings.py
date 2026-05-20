from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    db_host: str = Field(..., alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")
    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_schema: str = Field("public", alias="DB_SCHEMA")

    log_dir: str = Field("logs", alias="LOG_DIR")
    log_file: str = Field("bot.log", alias="LOG_FILE")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    warning_enabled: bool = Field(True, alias="WARNING_ENABLED")
    warning_ttl_seconds: int = Field(15, alias="WARNING_TTL_SECONDS")
    warning_message: str = Field(
        "⚠️ {user}, ваше сообщение удалено: запрещена нецензурная лексика.",
        alias="WARNING_MESSAGE",
    )

    @property
    def database_dsn(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
