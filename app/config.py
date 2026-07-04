from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    telegram_bot_token: str
    telegram_chat_id: str
    telegram_api_base: str = "https://api.telegram.org"
    webhook_port: int = 9091


settings = Settings()
