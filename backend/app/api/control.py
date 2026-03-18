from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import asyncio
from datetime import datetime

from ..models.models import User
from .auth import get_current_user
from ..core.config import settings
from pydantic import BaseModel
from ..services.polling_service import polling_service
from ..services.risk_manager import RiskManager
from ..db.session import SessionLocal, get_db
from ..models.models import Strategy

router = APIRouter()

class RiskProfileUpdate(BaseModel):
    profile: str

@router.post("/risk-profile")
async def update_risk_profile(data: RiskProfileUpdate):
    """Updates the global risk profile (NORMAL/CONSERVATIVE)."""
    if data.profile not in ["NORMAL", "CONSERVATIVE"]:
        raise HTTPException(status_code=400, detail="Perfil de riesgo inválido")
    
    risk_mgr = RiskManager()
    risk_mgr._risk_profile = data.profile
    risk_mgr.save_state()
    logger.info(f"🔄 PERFIL DE RIESGO ACTUALIZADO: {data.profile}")
    return {"message": f"Perfil de riesgo actualizado a {data.profile}"}
logger = logging.getLogger(__name__)

@router.post("/start")
async def start_bot(data: dict = None):
    """Starts the background polling service with specific mode validation (MOCK, DRY_RUN, LIVE)."""
    if polling_service.killed:
         raise HTTPException(
                status_code=403, 
                detail="SISTEMA BLOQUEADO (KILLED). Reinicie el backend físicamente."
            )

    # Detect default mode if not specified by frontend
    if not data or "mode" not in data:
        if settings.MOCK_EXCHANGE:
            mode = "MOCK"
        elif settings.DRY_RUN_REAL_API:
            mode = "DRY_RUN"
        elif settings.ENABLE_REAL_TRADING:
            mode = "LIVE"
        else:
            mode = "MOCK" # Fallback
    else:
        mode = data.get("mode").upper()

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
    
    polling_service.save_state()
    risk_mgr.save_state()
    
    logger.critical("🚨 EMERGENCY KILL SWITCH triggered via Dashboard. Bot LOCKED.")
    return {"message": "🚨 KILL SWITCH ACTIVADO. Bot bloqueado permanentemente hasta reinicio."}

@router.post("/unlock")
async def unlock_bot():
    """Unlocks the bot after an EMERGENCY KILL was triggered."""
    risk_mgr = RiskManager()
    if not polling_service.killed and not risk_mgr.kill_switch_active:
        return {"message": "El bot no está bloqueado."}
        
    polling_service.killed = False
    polling_service.last_action = "STOP"
    
    risk_mgr = RiskManager()
    risk_mgr.reset_circuit_breaker()
    
    polling_service.save_state()
    
    logger.info("🔓 SYSTEM UNLOCKED via Dashboard. Bot can be started again.")
    return {"message": "🔓 SISTEMA DESBLOQUEADO. Puede iniciar el bot nuevamente."}

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
@router.get("/debug/binance-test")
async def test_binance_connectivity():
    """Directly tests the Binance API keys configured in settings."""
    import ccxt
    import requests
    
    # 1. Get current IP to help user with whitelisting
    try:
        current_ip = requests.get('https://api.ipify.org', timeout=5).text
    except Exception as e:
        current_ip = f"Error detecting IP: {e}"

    def clean_key(val):
        if not val: return ""
        return str(val).strip().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

    api_key = clean_key(settings.BINANCE_API_KEY)
    api_secret = clean_key(settings.BINANCE_API_SECRET)
    
    if not api_key or not api_secret:
        return {"error": "API keys are missing in environment variables.", "current_ip": current_ip}
        
    try:
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        
        test_exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot', # Added defaultType
                'adjustForTimeDifference': True, # Crucial for -2015 errors
            }
        })
        balance = test_exchange.fetch_balance()
        return {
            "success": True,
            "message": "API Keys verified!",
            "current_ip": current_ip,
            "key_used": masked_key,
            "permissions": balance.get('info', {}).get('permissions', [])
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "current_ip": current_ip,
            "hint": f"Enséñale esta IP {current_ip} a tu amigo para que la ponga en Binance."
        }

@router.get("/debug/emergency-cleanup")
async def emergency_cleanup(db: Session = Depends(get_db)):
    """One-off deep cleanup to delete 'santi' data and account to resolve Supabase egress issues."""
    from app.models.models import User, Strategy, StrategyExecution, PaperTrade, LiveTrade, Prediction, Alert
    from sqlalchemy import func
    
    target_usernames = ["santi", "santiagomiguelcruz", "Santi"]
    santi_user = db.query(User).filter(func.lower(User.username).in_([u.lower() for u in target_usernames])).first()
    
    if not santi_user:
        logger.warning(f"Cleanup: User with names {target_usernames} not found.")
        return {"error": f"User {target_usernames} not found. Check spelling (Case insensitive)."}

    # 1. Delete Predictions & Alerts
    pred_count = db.query(Prediction).filter(Prediction.owner_id == santi_user.id).delete(synchronize_session=False)
    alert_count = db.query(Alert).filter(Alert.owner_id == santi_user.id).delete(synchronize_session=False)

    # 2. Delete Strategies & Executions
    strategies = db.query(Strategy).filter(Strategy.user_id == santi_user.id).all()
    strategy_ids = [s.id for s in strategies]
    exec_count = 0
    strat_count = 0
    
    if strategy_ids:
        exec_count = db.query(StrategyExecution).filter(StrategyExecution.strategy_id.in_(strategy_ids)).delete(synchronize_session=False)
        strat_count = db.query(Strategy).filter(Strategy.id.in_(strategy_ids)).delete(synchronize_session=False)
    
    # 3. Delete Trades
    paper_count = db.query(PaperTrade).filter(PaperTrade.owner_id == santi_user.id).delete(synchronize_session=False)
    live_count = db.query(LiveTrade).filter(LiveTrade.user_id == santi_user.id).delete(synchronize_session=False)
    
    # 4. Delete the User Account itself
    uname = santi_user.username
    db.delete(santi_user)
    
    db.commit()
    logger.info(f"🔥 DEEP CLEANUP: User {uname} and all related data deleted from Supabase.")
    
    return {
        "success": f"Cleaned up ALL data and deleted account for {uname}",
        "deleted": {
            "predictions": pred_count,
            "alerts": alert_count,
            "strategies": strat_count,
            "executions": exec_count,
            "paper_trades": paper_count,
            "live_trades": live_count,
            "user_account": uname
        }
    }
