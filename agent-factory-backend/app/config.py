"""
Application configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Agent Factory Backend"
    debug: bool = True
    log_level: str = "INFO"

    # A2A Protocol
    a2a_enabled: bool = True
    a2a_api_key: str = "change-me-in-production"

    # FTE URLs
    customer_success_fte_url: str = "http://localhost:8001"

    # Server
    host: str = "0.0.0.0"
    port: int = 8003

    # Authentication & Security
    jwt_secret_key: str = "your-secret-key-change-in-production-use-env-var"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 7
    bcrypt_rounds: int = 12


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get settings instance (cached)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
