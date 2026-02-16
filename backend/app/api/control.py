from fastapi import APIRouter, Depends, HTTPException
import logging
import asyncio
from datetime import datetime

from ..models.models import User
from .auth import get_current_user
from ..core.config import settings
from ..services.polling_service import polling_service
from ..services.risk_manager import RiskManager
from ..db.session import SessionLocal
from ..models.models import Strategy

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/start")
async def start_bot(data: dict = None):
    """Starts the background polling service with specific mode validation (MOCK, DRY_RUN, LIVE)."""
    if polling_service.killed:
         raise HTTPException(
                status_code=403, 
                detail="SISTEMA BLOQUEADO (KILLED). Reinicie el backend físicamente."
            )

    mode = (data or {}).get("mode", "MOCK").upper()
    if mode not in ["MOCK", "DRY_RUN", "LIVE"]:
        raise HTTPException(status_code=400, detail="Modo de inicio inválido. Use MOCK, DRY_RUN o LIVE.")

    if mode == "MOCK":
        if not settings.MOCK_EXCHANGE:
            raise HTTPException(
                status_code=400, 
                detail="El modo MOCK requiere MOCK_EXCHANGE=True en el archivo .env."
            )
    else:
        # For DRY_RUN or LIVE, we REQUIRE APIs
        if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
            raise HTTPException(
                status_code=400, 
                detail=f"El modo {mode} requiere API keys válidas configuradas."
            )
        
        if mode == "LIVE" and not settings.ENABLE_REAL_TRADING:
             raise HTTPException(
                status_code=400, 
                detail="El modo LIVE requiere ENABLE_REAL_TRADING=True en el archivo .env."
            )

    if not polling_service.running:
        asyncio.create_task(polling_service.start(mode=mode))
        return {"message": f"Bot iniciado correctamente en modo {mode}."}
    return {"message": f"El bot ya está en ejecución ({polling_service.active_mode})."}

@router.post("/stop")
async def stop_bot(data: dict = None):
    """Stops the background polling service."""
    if polling_service.running:
        await polling_service.stop()
        return {"message": "Bot detenido. Las posiciones permanecen abiertas."}
    return {"message": "El bot ya estaba detenido."}

@router.get("/status")
async def get_bot_status():
    """Returns the current operational status of the bot (Canonical Etapa 4.2)."""
    risk_mgr = RiskManager()
    
    status = "STOPPED"
    if polling_service.running:
        status = "RUNNING"
    
    if polling_service.killed:
        status = "KILLED"
        
    uptime = 0
    if polling_service.start_time and polling_service.running:
        uptime = (datetime.now() - polling_service.start_time).total_seconds()
        
    return {
        "status": status,
        "mode": polling_service.active_mode or ("MOCK" if settings.MOCK_EXCHANGE else "STOPPED"),
        "uptime": int(uptime),
        "last_action": polling_service.last_action,
        "risk_state": risk_mgr.gec_state,
        "api_ready": bool(settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET)
    }

@router.post("/kill")
async def kill_bot():
    """EMERGENCY: Triggers Kill Switch, cancels all intentions and locks the bot."""
    if polling_service.running:
        await polling_service.stop()
    
    polling_service.killed = True
    polling_service.last_action = "KILL"
        
    risk_mgr = RiskManager()
    risk_mgr._kill_switch_active = True
    risk_mgr._gec_state = "KILL_SWITCH"
    
    logger.critical("🚨 EMERGENCY KILL SWITCH triggered via Dashboard. Bot LOCKED.")
    return {"message": "🚨 KILL SWITCH ACTIVADO. Bot bloqueado permanentemente hasta reinicio."}

@router.get("/debug/engine")
async def debug_engine_state():
    """Provides deep visibility into the Strategy Engine's current state."""
    db = SessionLocal()
    try:
        active_strategies = db.query(Strategy).filter(Strategy.status == "ACTIVE").all()
        strategy_data = [
            {
                "id": s.id,
                "ticker": s.ticker,
                "type": s.type,
                "params_count": len(s.params) if s.params else 0
            } for s in active_strategies
        ]
        
        return {
            "polling_running": polling_service.running,
            "polling_tickers": polling_service.tickers,
            "polling_mode": polling_service.active_mode,
            "engine_initialized": polling_service.engine is not None,
            "active_strategies_count": len(active_strategies),
            "strategies": strategy_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return {"error": str(e)}
    finally:
        db.close()
