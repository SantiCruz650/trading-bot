from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..db.session import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    first_login = Column(Boolean, default=True)
    predictions = relationship("Prediction", back_populates="owner")
    paper_trades = relationship("PaperTrade", back_populates="owner")
    alerts = relationship("Alert", back_populates="owner")
    strategies = relationship("Strategy", back_populates="user")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    last_close = Column(Float)
    predicted_close = Column(String)
    signal = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="predictions")

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    amount = Column(Float)
    price = Column(Float)
    type = Column(String)  # BUY or SELL
    status = Column(String, default="OPEN")
    pnl = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="paper_trades")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    target_price = Column(Float)
    condition = Column(String)  # ABOVE or BELOW
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="alerts")

from sqlalchemy import JSON

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String, index=True)
    type = Column(String) # "GRID", "DCA"
    status = Column(String, default="ACTIVE") # "ACTIVE", "PAUSED", "TERMINATED"
    params = Column(JSON) # Stores {"min_price": 50000, "grids": 10} etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="strategies")
    executions = relationship("StrategyExecution", back_populates="strategy")

class StrategyExecution(Base):
    __tablename__ = "strategy_executions"
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    order_type = Column(String) # "BUY", "SELL"
    price = Column(Float)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    strategy = relationship("Strategy", back_populates="executions")

class LiveTrade(Base):
    """Track all live trading activity"""
    __tablename__ = "live_trades"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_id = Column(String, index=True)  # Exchange order ID
    symbol = Column(String, index=True)  # e.g., "BTC/USDT"
    side = Column(String)  # "buy" or "sell"
    amount = Column(Float)  # Amount traded
    price = Column(Float)  # Execution price
    value_usdt = Column(Float)  # Total value in USDT
    fee = Column(Float, default=0.0)  # Trading fee
    pnl = Column(Float, default=0.0)  # P&L if closing trade
    stop_loss_pct = Column(Float, nullable=True)  # Stop-loss percentage
    status = Column(String, default="filled")  # Order status
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class SystemState(Base):
    """Stores global system state (Risk Manager status, Polling status, etc.)"""
    __tablename__ = "system_state"
    key = Column(String, primary_key=True, index=True)
    value = Column(JSON) # Supports complex objects or simple strings/bools
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)