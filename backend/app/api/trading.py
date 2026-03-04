from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..db.session import get_db
from ..models.models import User, PaperTrade, Alert
from .auth import get_current_user
from ..services.telegram_service import telegram_service

router = APIRouter()

# --- Pydantic Models ---
class TradeCreate(BaseModel):
    ticker: str
    amount: float
    price: float
    type: str  # BUY or SELL

class AlertCreate(BaseModel):
    ticker: str
    target_price: float
    condition: str  # ABOVE or BELOW

class TradeResponse(BaseModel):
    id: int
    ticker: str
    amount: float
    price: float
    type: str
    status: str
    pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    ticker: str
    target_price: float
    condition: str
    is_active: bool

    class Config:
        from_attributes = True

# --- Endpoints ---



@router.post("/trade", response_model=TradeResponse)
async def execute_trade(
    trade: TradeCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Basic validation
    if trade.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get risk manager
    from ..services.risk_manager import RiskManager
    # In a real app, bankroll would come from user's portfolio balance
    risk_manager = RiskManager(bankroll=10000.0) 
    
    # Calculate SL/TP using centralized logic
    stop_loss, take_profit = risk_manager.calculate_sl_tp(trade.price, trade.type)

    db_trade = PaperTrade(
        ticker=trade.ticker,
        amount=trade.amount,
        price=trade.price,
        type=trade.type,
        stop_loss=stop_loss,
        take_profit=take_profit,
        owner_id=current_user.id
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)

    # Send Telegram Alert
    message = f"🔔 Trade Executed: {trade.type} {trade.amount} {trade.ticker} @ ${trade.price}\n🛡️ SL: ${stop_loss:.2f} | 🎯 TP: ${take_profit:.2f}"
    background_tasks.add_task(telegram_service.send_alert, message)

    return db_trade

@router.get("/trades", response_model=List[TradeResponse])
def get_trades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(PaperTrade).filter(PaperTrade.owner_id == current_user.id).order_by(PaperTrade.created_at.desc()).all()

@router.get("/portfolio")
def get_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculates current portfolio holdings based on trade history.
    """
    trades = db.query(PaperTrade).filter(PaperTrade.owner_id == current_user.id).all()
    
    portfolio = {}
    
    for trade in trades:
        if trade.ticker not in portfolio:
            portfolio[trade.ticker] = {"amount": 0.0, "total_cost": 0.0}
        
        if trade.type == "BUY":
            portfolio[trade.ticker]["amount"] += trade.amount
            portfolio[trade.ticker]["total_cost"] += (trade.amount * trade.price)
        elif trade.type == "SELL":
            portfolio[trade.ticker]["amount"] -= trade.amount
            # Cost basis reduction logic (simplified: proportional)
            # In a real app, use FIFO or LIFO
            if portfolio[trade.ticker]["amount"] < 0:
                 portfolio[trade.ticker]["amount"] = 0 # Prevent negative holdings
            
    # Format for frontend
    result = []
    for ticker, data in portfolio.items():
        if data["amount"] > 0.000001: # Filter out empty positions
            avg_price = data["total_cost"] / data["amount"] if data["amount"] > 0 else 0
            result.append({
                "ticker": ticker,
                "amount": data["amount"],
                "price": avg_price, # Avg Entry Price
                "value": 0, # Current value would require live price, frontend can fetch
                "pnl": 0
            })
            
    return result

@router.post("/alert", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_alert = Alert(
        ticker=alert.ticker,
        target_price=alert.target_price,
        condition=alert.condition,
        owner_id=current_user.id
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)

    # Send Telegram Alert
    message = f"✅ Alert Set: {alert.ticker} {alert.condition} ${alert.target_price}"
    background_tasks.add_task(telegram_service.send_alert, message)

    return db_alert

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Alert).filter(Alert.owner_id == current_user.id).all()

@router.delete("/alert/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.owner_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    return {"message": "Alert deleted"}

@router.get("/balance")
async def get_trading_balance(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch current balance and stats for dashboard."""
    from ..services.exchange_service import get_exchange
    from ..services.risk_manager import RiskManager
    from ..core.config import settings
    
    exchange = get_exchange(local_simulation=settings.OBSERVATION_ONLY)
    risk_mgr = RiskManager()
    
    balance = exchange.get_balance()
    stats = risk_mgr.get_daily_stats()
    
    # Mock some data for dashboard consistency if needed
    return {
        "balance": balance,
        "equity": balance + (stats.get("exposure", 0) * balance), # Simplified
        "prices": {"ETH": exchange.get_ticker_price("ETH/USDT") or 0},
        "stats": stats
    }
