"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn
from typing import Dict, Any


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://orion:orion_secret@postgres:5432/orion_ai"
    )

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # AI
    openrouter_key: str = Field(alias="OPENROUTER_API_KEY")
    anthropic_key: str = Field(alias="ANTHROPIC_API_KEY")
    gemini_key: str = Field(alias="GEMINI_API_KEY")

    primary_model: str = "openai/gpt-4o-mini"
    deep_model: str = "claude-3-5-sonnet-20240620"
    vision_model: str = "gemini-1.5-flash"

    # Auth
    secret_key: str = Field(alias="SECRET_KEY")
    access_token_expire_minutes: int = 60

    # Stripe
    stripe_secret: str = Field(alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_pro: str = Field(alias="STRIPE_PRICE_PRO")
    stripe_price_business: str = Field(alias="STRIPE_PRICE_BUSINESS")

    # Email
    sendgrid_key: str = Field(alias="SENDGRID_API_KEY")
    sendgrid_from: str = Field(alias="SENDGRID_FROM_EMAIL")

    # Plans
    plans: Dict[str, Dict[str, Any]] = {
        "free": {"credits": 3, "price": 0, "agents": ["strategic", "marketing"]},
        "pro": {"credits": 10, "price": 9.99, "agents": ["strategic", "marketing", "competitor", "content"]},
        "business": {"credits": 50, "price": 29.99, "agents": "all"}
    }

    # Gamification
    xp_per_report: int = 10
    xp_per_referral: int = 50
    levels: Dict[int, int] = {1: 0, 2: 100, 3: 300, 4: 600, 5: 1000}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def db_url_str(self) -> str:
        return str(self.database_url)


settings = Settings()
