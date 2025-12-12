"""
Trading Router - API endpoints for live trading
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..db.session import get_db
from ..auth.auth import get_current_user
from ..models.models import User as UserModel, LiveTrade
from ..services.exchange_service import get_exchange
from ..services.risk_manager import RiskManager
from ..services.alert_service import get_alert_service
from .schemas import TradeRequest, TradeResponse, PositionResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    trade: TradeRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a trade with risk management
    
    Request body:
    {
        "symbol": "BTC/USDT",
        "side": "buy" or "sell",
        "amount": 0.001,  # Optional, will be calculated if not provided
        "stop_loss_pct": 0.02  # Optional, default 2%
    }
    """
    try:
        # Get services
        exchange = get_exchange(testnet=True)  # Always testnet for now
        risk_mgr = RiskManager()
        alert_svc = get_alert_service()
        
        # Get current balance
        balance = exchange.get_balance('USDT')
        
        # Check if trading is allowed
        can_trade, reason = risk_mgr.can_trade(balance)
        if not can_trade:
            raise HTTPException(status_code=403, detail=f"Trading blocked: {reason}")
        
        # Get current price
        price = exchange.get_ticker_price(trade.symbol)
        if not price:
            raise HTTPException(status_code=503, detail=f"Could not fetch price for {trade.symbol}")
        
        # Calculate position size if not provided
        if trade.amount is None:
            _, amount = risk_mgr.calculate_position_size(balance, price)
            trade.amount = amount
        
        # Validate amount
        if trade.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        # Execute trade
        order = exchange.place_market_order(
            symbol=trade.symbol,
            side=trade.side,
            amount=trade.amount,
            stop_loss_pct=trade.stop_loss_pct or 0.02
        )
        
        if not order:
            raise HTTPException(status_code=500, detail="Failed to execute trade")
        
        # Record trade
        value_usdt = trade.amount * price
        risk_mgr.record_trade(value_usdt, is_opening=(trade.side == 'buy'))
        
        # Save to database
        db_trade = LiveTrade(
            user_id=current_user.id,
            order_id=order['id'],
            symbol=trade.symbol,
            side=trade.side,
            amount=trade.amount,
            price=price,
            value_usdt=value_usdt,
            stop_loss_pct=trade.stop_loss_pct or 0.02
        )
        db.add(db_trade)
        db.commit()
        
        # Send alert
        await alert_svc.send_trade_alert(
            symbol=trade.symbol,
            side=trade.side,
            amount=trade.amount,
            price=price,
            value=value_usdt,
            success=True
        )
        
        logger.info(
            f"✅ Trade executed: {trade.side.upper()} {trade.amount} {trade.symbol} @ ${price}"
        )
        
        return TradeResponse(
            success=True,
            order_id=order['id'],
            symbol=trade.symbol,
            side=trade.side,
            amount=trade.amount,
            price=price,
            value_usdt=value_usdt,
            message="Trade executed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance(current_user: UserModel = Depends(get_current_user)):
    """Get current account balance"""
    try:
        exchange = get_exchange(testnet=True)
        balance = exchange.get_balance('USDT')
        
        return {
            "currency": "USDT",
            "balance": balance,
            "formatted": f"${balance:,.2f}"
        }
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions(current_user: UserModel = Depends(get_current_user)):
    """Get all open positions"""
    try:
        exchange = get_exchange(testnet=True)
        balance_response = exchange.exchange.fetch_balance()
        
        positions = []
        for currency, amounts in balance_response.get('total', {}).items():
            amount = float(amounts)
            if currency != 'USDT' and amount > 0:
                symbol = f"{currency}/USDT"
                price = exchange.get_ticker_price(symbol)
                
                if price:
                    value = amount * price
                    positions.append({
                        "symbol": symbol,
                        "currency": currency,
                        "amount": amount,
                        "current_price": price,
                        "value_usdt": value
                    })
        
        total_value = sum(p['value_usdt'] for p in positions)
        
        return {
            "positions": positions,
            "count": len(positions),
            "total_value_usdt": total_value
        }
        
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency/close-all")
async def emergency_close_all(current_user: UserModel = Depends(get_current_user)):
    """
    EMERGENCY: Close all positions immediately
    USE WITH CAUTION
    """
    try:
        exchange = get_exchange(testnet=True)
        closed = exchange.close_all_positions()
        
        logger.warning(f"🚨 EMERGENCY CLOSE executed by user {current_user.username}")
        
        return {
            "success": True,
            "closed_positions": closed,
            "message": f"Closed {len(closed)} positions"
        }
        
    except Exception as e:
        logger.error(f"Emergency close error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency/cancel-orders")
async def emergency_cancel_orders(current_user: UserModel = Depends(get_current_user)):
    """
    EMERGENCY: Cancel all pending orders
    """
    try:
        exchange = get_exchange(testnet=True)
        cancelled = exchange.cancel_all_orders()
        
        logger.warning(f"🚨 EMERGENCY CANCEL executed by user {current_user.username}")
        
        return {
            "success": True,
            "cancelled_count": cancelled,
            "message": f"Cancelled {cancelled} orders"
        }
        
    except Exception as e:
        logger.error(f"Emergency cancel error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk/stats")
async def get_risk_stats(current_user: UserModel = Depends(get_current_user)):
    """Get current risk management statistics"""
    try:
        risk_mgr = RiskManager()
        stats = risk_mgr.get_daily_stats()
        
        return {
            "daily_trades": stats['trades'],
            "daily_pnl": stats['pnl'],
            "current_exposure": stats['exposure'],
            "circuit_breaker_active": risk_mgr.circuit_breaker_active,
            "circuit_breaker_reason": risk_mgr.circuit_breaker_reason
        }
        
    except Exception as e:
        logger.error(f"Error fetching risk stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/reset-circuit-breaker")
async def reset_circuit_breaker(current_user: UserModel = Depends(get_current_user)):
    """
    Reset circuit breaker (manual action required)
    Only use after reviewing why it was triggered
    """
    try:
        risk_mgr = RiskManager()
        risk_mgr.reset_circuit_breaker()
        
        logger.info(f"Circuit breaker reset by user {current_user.username}")
        
        return {
            "success": True,
            "message": "Circuit breaker reset. Trading enabled."
        }
        
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
