from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "MCrypto Backend API"
    VERSION: str = "1.0.0"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    model_config = {"env_file": ".env"}

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/tradingbot.db"
    
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
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Binance
    BINANCE_TESTNET_API_KEY: str = ""
    BINANCE_TESTNET_API_SECRET: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "https://localhost:8080",
        "https://*.ngrok.io",
        "https://*.ngrok-free.app",
        "https://*.ngrok-free.dev",
        "https://*.onrender.com"
    ]

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()