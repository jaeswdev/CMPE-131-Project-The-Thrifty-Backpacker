"""
Application configuration.
Reads values from .env at startup and validates them with pydantic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings — every module imports from here."""

    # === RapidAPI (Booking.com via Tipsters) ===
    RAPIDAPI_KEY: str
    RAPIDAPI_HOST: str = "booking-com.p.rapidapi.com"
    RAPIDAPI_BASE_URL: str = "https://booking-com.p.rapidapi.com"

    # === JWT Authentication ===
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # === Database ===
    DATABASE_URL: str = "sqlite:///./travel_booking.db"

    # === App metadata ===
    APP_NAME: str = "Thrifty Backpacker API"
    APP_VERSION: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere
settings = Settings()