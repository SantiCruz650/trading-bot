from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, Strategy
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class StrategyCreate(BaseModel):
    ticker: str
    type: str # GRID, DCA
    params: Dict[str, Any]

@router.post("/create")
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Standardize and validate ticker format BASE/QUOTE (e.g., BTC/USDT)
    ticker = strategy.ticker.upper()
    if "/" not in ticker:
        # Fallback/Auto-fix if they just send BTC, but log it or enforce it
        # The requirement says NO hidden conversion, so let's enforce it or be very explicit.
        if ticker in ["BTC", "ETH", "ADA", "SOL", "DOGE"]:
             ticker = f"{ticker}/USDT"
        else:
             raise HTTPException(status_code=400, detail="Ticker must be in BASE/QUOTE format (e.g., BTC/USDT)")

    new_strategy = Strategy(
        user_id=current_user.id,
        ticker=ticker,
        type=strategy.type,
        params=strategy.params,
        status="ACTIVE"
    )
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy

@router.get("")
def get_strategies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Strategy).filter(Strategy.user_id == current_user.id).all()

@router.post("/{strategy_id}/stop")
def stop_strategy(strategy_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.status = "TERMINATED"
    db.commit()
    return {"message": "Strategy stopped"}

@router.get("/{strategy_id}")
def get_strategy_detail(strategy_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy

@router.get("/{strategy_id}/executions")
def get_strategy_executions(strategy_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy.executions
