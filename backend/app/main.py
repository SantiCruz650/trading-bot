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

app = FastAPI(
    title=settings.PROJECT_NAME
    # root_path is only needed for reverse proxy setups like ngrok
    # For local dev, we'll handle /api prefix in the router includes
)

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

from .services.market_stream import market_stream
import asyncio

@app.on_event("startup")
async def startup_event():
    # Start market stream in background
    asyncio.create_task(market_stream.start())

@app.on_event("shutdown")
async def shutdown_event():
    await market_stream.stop()

# Include routers with /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
app.include_router(proxy_router, prefix="/api/ml", tags=["ml-service"])
app.include_router(trading.router, prefix="/api/trading",tags=["trading"])
from .api import strategies, trading_live
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(trading_live.router, prefix="/api/trading-live", tags=["live-trading"])

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from .services.websocket_manager import manager

# ... imports ...

# ... existing code ...

# Serve frontend assets via FastAPI so the same domain handles UI + API
@app.websocket("/ws/predictions")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, maybe listen for client pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve frontend assets via FastAPI so the same domain handles UI + API
# Mount this LAST so it doesn't override API or WebSocket routes
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

