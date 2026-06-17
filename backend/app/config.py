from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EmployerFlow"
    app_url: str = "http://localhost:8000"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    database_url: str = "postgresql+psycopg2://employerflow:employerflow@db:5432/employerflow"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro_monthly: str = ""
    stripe_price_premium_monthly: str = ""

    cors_origins: str = "http://localhost:8000,http://localhost:3000"

    free_employer_limit: int = 100
    pro_shortlist_limit: int = 100
    premium_shortlist_limit: int = 500
    free_hiring_radar_limit: int = 0
    pro_hiring_radar_limit: int = 200
    premium_hiring_radar_limit: int = 12000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Render/Heroku provide postgres:// — normalize for SQLAlchemy + psycopg2
    if s.database_url.startswith("postgres://"):
        object.__setattr__(s, "database_url", s.database_url.replace("postgres://", "postgresql+psycopg2://", 1))
    return s