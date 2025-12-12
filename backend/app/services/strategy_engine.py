from sqlalchemy.orm import Session
from app.models.models import Strategy, StrategyExecution, PaperTrade
from datetime import datetime, timedelta
import json

class StrategyEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_strategies(self, ticker: str, current_price: float):
        """Check all active strategies for this ticker and execute if needed."""
        strategies = self.db.query(Strategy).filter(
            Strategy.ticker == ticker, 
            Strategy.status == "ACTIVE"
        ).all()
        
        results = []
        for strategy in strategies:
            if strategy.type == "GRID":
                res = self._evaluate_grid(strategy, current_price)
            elif strategy.type == "DCA":
                res = self._evaluate_dca(strategy, current_price)
            
            if res:
                results.append(res)
        return results

    def _evaluate_dca(self, strategy, current_price):
        """
        DCA Logic: Buy if enough time has passed since last buy.
        Params: {"amount": 100, "interval_hours": 24}
        """
        params = strategy.params
        amount = params.get("amount", 100)
        interval_hours = params.get("interval_hours", 24)
        
        # Get last execution
        last_exec = self.db.query(StrategyExecution).filter(
            StrategyExecution.strategy_id == strategy.id
        ).order_by(StrategyExecution.timestamp.desc()).first()
        
        should_buy = False
        if not last_exec:
            should_buy = True
        else:
            time_since = datetime.utcnow() - last_exec.timestamp
            if time_since > timedelta(hours=interval_hours):
                should_buy = True
        
        if should_buy:
            return self._execute_trade(strategy, "BUY", amount, current_price)
        return None

    def _evaluate_grid(self, strategy, current_price):
        """
        Simple Grid Logic:
        Params: {"min_price": 50000, "max_price": 60000, "grids": 10, "amount_per_grid": 50}
        """
        # Full grid logic is complex. For this MVP, we will simulate a buy
        # if price drops into a lower grid zone and we don't have an open position there.
        # This is a placeholder for the full implementation.
        return None

    def _execute_trade(self, strategy, order_type, amount, price):
        # 1. Record Execution
        execution = StrategyExecution(
            strategy_id=strategy.id,
            order_type=order_type,
            price=price,
            amount=amount
        )
        self.db.add(execution)
        
        # 2. Create Paper Trade
        trade = PaperTrade(
            ticker=strategy.ticker,
            amount=amount / price, # Quantity
            price=price,
            type=order_type,
            status="OPEN",
            owner_id=strategy.user_id
        )
        self.db.add(trade)
        self.db.commit()
        
        return f"Executed {order_type} for {strategy.ticker} at ${price}"
