"""Application settings using Pydantic Settings.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application configurations."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "ML-Based Solar PV & Battery EMS"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & Auth
    SECRET_KEY: str = "smart-grid-ems-super-secure-production-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite:///./smart_grid_ems.db"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000,http://localhost:8501"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Default Admin Seed
    DEFAULT_ADMIN_EMAIL: str = "admin@smartgrid.com"
    DEFAULT_ADMIN_PASSWORD: str = "AdminSecurePassword123!"

    # Default Battery Physics
    DEFAULT_BATTERY_CAPACITY_KWH: float = 10.0
    DEFAULT_BATTERY_MIN_SOC: float = 0.15
    DEFAULT_BATTERY_MAX_SOC: float = 0.95
    DEFAULT_BATTERY_MAX_CHARGE_KW: float = 5.0
    DEFAULT_BATTERY_MAX_DISCHARGE_KW: float = 5.0
    DEFAULT_BATTERY_CHARGE_EFF: float = 0.95
    DEFAULT_BATTERY_DISCHARGE_EFF: float = 0.95

    # Electricity Tariffs ($/kWh)
    DEFAULT_PEAK_PRICE: float = 0.35
    DEFAULT_OFFPEAK_PRICE: float = 0.10
    DEFAULT_STANDARD_PRICE: float = 0.18
    DEFAULT_FEED_IN_TARIFF: float = 0.08
    DEFAULT_DEGRADATION_COST: float = 0.01

    # Paths
    BASE_DIR: str = "."
    DATA_DIR: str = "data"
    MODELS_DIR: str = "models/saved"


settings = Settings()
