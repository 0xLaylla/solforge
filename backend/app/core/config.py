"""Application configuration via pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MiMo provider
    mimo_api_key: str
    mimo_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    mimo_model: str = "mimo-v2.5-pro"

    # Token tracker
    token_tracker_db: str = "./data/usage.db"
    daily_token_budget: int = 20_000_000

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Timeouts
    agent_timeout: int = 120
    synthesis_timeout: int = 180


settings = Settings()
