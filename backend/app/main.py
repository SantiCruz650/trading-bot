import sys
from pathlib import Path
import os

# 1. Enforce .env existence
env_path = Path(__file__).resolve().parent.parent / ".env"
if not env_path.exists():
    print(f"CRITICAL ERROR: Configuration file not found at {env_path}")
    print("El backend NO puede arrancar sin el archivo .env en /backend/.env")
    sys.exit(1)

# Add root directory to sys.path to allow importing shared
sys.path.append(str(Path(__file__).resolve().parents[2]))

import asyncio
import logging

# Configure logging to ensure visibility on Render (Python 3.11+)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

from .core.config import settings
from .api import auth_router, predictions_router, proxy_router, trading, control
from .db.session import engine
from .models.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

from app.services.report_service import generate_report

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
    # root_path is only needed for reverse proxy setups like ngrok
    # For local dev, we'll handle /api prefix in the router includes
)

@app.get("/report")
def get_daily_report(date: str = None):
    return generate_report(date)

@app.get("/healthz")
async def health_check_render():
    """Health check for Render deployment."""
    return {"status": "ok", "timestamp": str(datetime.now())}

@app.get("/health")
async def health_check():
    """Observability endpoint to check service status and version."""
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0",
        "timestamp": str(datetime.now())
    }

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

from .services.polling_service import polling_service
import asyncio

@app.on_event("startup")
async def startup_event():
    logger.info("DEBUG: Executing startup_event")
    
    # Initialize Strategy Engine (Persistent State)
    from app.services.strategy_engine import StrategyEngine
    engine = StrategyEngine()
    
    # Inject Engine into PollingService
    polling_service.engine = engine
    logger.info("📡 Strategy Engine integrated with Polling Service")
    
    # Start REST polling in background
    asyncio.create_task(polling_service.start())
    
    if os.getenv("HEADLESS_MODE") == "true" or True: # Always show in this local setup
        logger.info(f"🤖 Bot running in MODE: {settings.MOCK_EXCHANGE and 'MOCK' or 'PAPER/LIVE'}")

@app.on_event("shutdown")
async def shutdown_event():
    await polling_service.stop()

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
app.include_router(proxy_router, prefix="/api/ml", tags=["ml-service"])
app.include_router(control.router, prefix="/api", tags=["control"])

# Alias for front-end compatibility (Etapa 4.2.5)
app.include_router(control.router, prefix="/api/trading", tags=["control-alias"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])

from .api import strategies, trading_live
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(trading_live.router, prefix="/api/trading-live", tags=["live-trading"])

