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

    # Database
    DATABASE_URL: str = f"sqlite:////home/santiagomiguelcruz/trading-bot/backend/tradingbot.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "a_very_secret_key_change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Services
    # ML service base URL
    ML_SERVICE_URL: str = "http://localhost:8001"
    FRONTEND_URL: str = "http://localhost:8080"
    
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

    # ETAPA 2A - Risk Containment
    ETAPA_2A_ACTIVE: bool = True
    GEC_SOFT_CAP: float = 0.65
    GEC_HARD_CAP: float = 0.80
    FREEZE_DD_THRESHOLD: float = 0.015  # 1.5%
    KILL_SWITCH_DD_THRESHOLD: float = 0.030  # 3.0%
    KILL_SWITCH_ER_THRESHOLD: float = 0.95
    KILL_SWITCH_CONSECUTIVE_LOSSES: int = 5

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "https://localhost:8080",
        "https://*.ngrok.io",
        "https://*.ngrok-free.app",
        "https://*.ngrok-free.dev",
        "https://*.onrender.com",
        "https://*.netlify.app"
    ]

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()