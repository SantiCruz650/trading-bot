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
    new_strategy = Strategy(
        user_id=current_user.id,
        ticker=strategy.ticker,
        type=strategy.type,
        params=strategy.params,
        status="ACTIVE"
    )
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy

@router.get("/")
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
