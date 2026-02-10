import sys
from pathlib import Path
# Add root directory to sys.path to allow importing shared
sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime

from .core.config import settings
from .api import auth_router, predictions_router, proxy_router, trading
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

@app.get("/health")
async def health_check():
    """Observability endpoint to check service status and version."""
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0", # In a real app, read this from a file or env
        "timestamp": str(datetime.now())
    }

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:8080"],  # In production, use specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# from .services.market_stream import market_stream  # Deactivated WebSocket
from .services.polling_service import polling_service
import asyncio

@app.on_event("startup")
async def startup_event():
    print("DEBUG: Executing startup_event")
    # Start REST polling in background (Replaces WebSocket)
    asyncio.create_task(polling_service.start())
    
    import os
    if os.getenv("HEADLESS_MODE") == "true" or True: # Always show in this local setup
        print("🤖 Bot running in LOCAL PAPER TRADING MODE")
        print("📈 Market Simulator ACTIVE")
        print("📡 Strategy Engine ACTIVE")

@app.on_event("shutdown")
async def shutdown_event():
    await polling_service.stop()

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
app.include_router(proxy_router, prefix="/api/ml", tags=["ml-service"])
app.include_router(trading.router, prefix="/api/trading",tags=["trading"])
from .api import strategies, trading_live
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(trading_live.router, prefix="/api/trading-live", tags=["live-trading"])

from typing import List

# ... imports ...

# ... existing code ...

# Serve frontend assets via FastAPI so the same domain handles UI + API
# Mount this LAST so it doesn't override API or WebSocket routes
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend_v2"
print(f"DEBUG: Calculated FRONTEND_DIR: {FRONTEND_DIR}")
print(f"DEBUG: FRONTEND_DIR exists? {FRONTEND_DIR.exists()}")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    print("DEBUG: Mounted frontend_v2 static files")
else:
    print("ERROR: Frontend directory not found, static files NOT mounted")

