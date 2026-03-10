import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "MCrypto Backend API"
    VERSION: str = "1.0.0"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "extra": "ignore"
    }

    # Database: Use DATABASE_URL from env (Supabase/Render) or fallback to local SQLite
    _db_url: str = os.getenv("DATABASE_URL", f"sqlite:////home/santiagomiguelcruz/trading-bot/backend/tradingbot.db")
    # Normalize postgres:// to postgresql:// for SQLAlchemy compatibility
    DATABASE_URL: str = _db_url.replace("postgres://", "postgresql://", 1) if _db_url.startswith("postgres://") else _db_url
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "a_very_secret_key_change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Services
    # ML service base URL (Environment variables take precedence)
    ML_SERVICE_URL: str = "DIRECT_PYTHON_IMPORT"
    FRONTEND_URL: str = "https://santicruz650.github.io"
    NGROK_URL: str = "" # Optional override
    
    # Environment
    ENV: str = "production"
    DRY_RUN_REAL_API: bool = True
    ENABLE_REAL_TRADING: bool = False
    MOCK_EXCHANGE: bool = True
    
    # Binance
    BINANCE_TESTNET: bool = True
    BINANCE_TESTNET_API_KEY: str = ""
    BINANCE_TESTNET_API_SECRET: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # Trading
    BASE_TRADE_AMOUNT: float = 2.0
    OBSERVATION_ONLY: bool = False
    MAX_SIMULTANEOUS_ORDERS: int = 5

    # ETAPA 2A - Risk Containment
    ETAPA_2A_ACTIVE: bool = True
    GEC_SOFT_CAP: float = 0.20
    GEC_HARD_CAP: float = 0.30
    FREEZE_DD_THRESHOLD: float = 0.015  # 1.5%
    KILL_SWITCH_DD_THRESHOLD: float = 0.030  # 3.0%
    KILL_SWITCH_ER_THRESHOLD: float = 0.95
    KILL_SWITCH_CONSECUTIVE_LOSSES: int = 5

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "https://santicruz650.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080"
    ]

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
