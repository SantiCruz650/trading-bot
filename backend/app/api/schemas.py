"""
Schemas for live trading endpoints
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class TradeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str  # e.g., "BTC/USDT"
    side: str  # "buy" or "sell"
    amount: Optional[float] = None  # Will be calculated if not provided
    stop_loss_pct: Optional[float] = 0.02  # Default 2%


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    success: bool
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    value_usdt: float
    message: str


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    currency: str
    amount: float
    current_price: float
    value_usdt: float
