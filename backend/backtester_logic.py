import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.attributes import flag_modified
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backtester")

Base = declarative_base()

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    type = Column(String)
    params = Column(JSON)

class StrategyExecution(Base):
    __tablename__ = "strategy_executions"
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    order_type = Column(String)
    price = Column(Float)
    amount = Column(Float)
    timestamp = Column(DateTime)

class BacktestExchange:
    def __init__(self, initial_balance=1000.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.orders = []

    def get_balance(self):
        return self.balance

    def place_market_order(self, symbol, side, amount, price):
        cost = amount * price
        if side == 'buy':
            if cost > self.balance:
                return None
            self.balance -= cost
        else:
            self.balance += cost
        
        order = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'timestamp': datetime.utcnow()
        }
        self.orders.append(order)
        return order

class BacktestEngine:
    def __init__(self, initial_balance=1000.0):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.exchange = BacktestExchange(initial_balance)
        
        # Create a dummy strategy
        self.strategy = Strategy(
            ticker="ETH",
            type="DCA",
            params={"amount": 2.0, "interval_hours": 0.02} # ~72s
        )
        self.db.add(self.strategy)
        self.db.commit()

    def _get_position_stats(self):
        executions = self.db.query(StrategyExecution).filter(
            StrategyExecution.strategy_id == self.strategy.id
        ).all()
        
        total_eth = 0.0
        total_cost = 0.0
        
        for ex in executions:
            eth_amount = ex.amount / ex.price
            if ex.order_type == "BUY":
                total_eth += eth_amount
                total_cost += ex.amount
            else:
                if total_eth > 0:
                    avg_price = total_cost / total_eth
                    total_eth -= eth_amount
                    total_cost -= (avg_price * eth_amount)
        
        if total_eth <= 0:
            return 0.0, 0.0
            
        avg_price = total_cost / total_eth
        return avg_price, total_eth

    def evaluate(self, current_price, timestamp):
        # Ensure timestamp is naive UTC
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert(None)
            
        params = self.strategy.params or {}
        params["total_cycles"] = params.get("total_cycles", 0) + 1
        
        avg_price, total_eth = self._get_position_stats()
        current_balance = self.exchange.get_balance()
        
        # 3. Drawdown Guard
        price_history = params.get("price_history", [])
        # Keep only last 10 minutes (600s)
        price_history = [p for p in price_history if (timestamp - datetime.fromisoformat(p['ts'])).total_seconds() < 600]
        price_history.append({'ts': timestamp.isoformat(), 'price': current_price})
        params['price_history'] = price_history
        
        paused_until = params.get("paused_until")
        if paused_until and timestamp < datetime.fromisoformat(paused_until):
            self.strategy.params = params
            flag_modified(self.strategy, "params")
            self.db.commit()
            return None

        if len(price_history) > 1:
            oldest_price = price_history[0]['price']
            drop_pct = (current_price - oldest_price) / oldest_price
            if drop_pct <= -0.04:
                params['paused_until'] = (timestamp + timedelta(minutes=30)).isoformat()
                logger.info(f"🚨 Drawdown detected ({drop_pct*100:.1f}%). Buying paused for 30m.")
                self.strategy.params = params
                flag_modified(self.strategy, "params")
                self.db.commit()
                return None

        # 4. Check Sell Condition (Trailing Take Profit)
        if total_eth > 0 and avg_price > 0:
            profit_pct = (current_price - avg_price) / avg_price
            
            ttp_active = params.get("ttp_active", False)
            highest_price = params.get("highest_price", 0.0)
            
            if profit_pct >= 0.015 or ttp_active:
                if not ttp_active:
                    params["ttp_active"] = True
                    params["highest_price"] = current_price
                    logger.info(f"🎯 TTP Armed for {self.strategy.ticker} at ${current_price:,.2f}")
                else:
                    if current_price > highest_price:
                        params["highest_price"] = current_price
                    
                    drop_from_peak = (params["highest_price"] - current_price) / params["highest_price"]
                    if drop_from_peak >= 0.0075:
                        eth_to_sell = total_eth * 0.20
                        if eth_to_sell * current_price > 1.0:
                            # Reset TTP
                            params["ttp_active"] = False
                            params["highest_price"] = 0.0
                            # Set Cooldown
                            params["cooldown_cycles"] = 3
                            self.strategy.params = params
                            flag_modified(self.strategy, "params")
                            self.db.commit()
                            return self._execute_trade("SELL", eth_to_sell * current_price, current_price, timestamp)

        # 5. Check Buy Condition (Intelligent DCA + Cooldown)
        cooldown = params.get("cooldown_cycles", 0)
        if cooldown > 0:
            params["cooldown_cycles"] -= 1
            self.strategy.params = params
            flag_modified(self.strategy, "params")
            self.db.commit()
            return None

        can_buy = True
        if current_balance < 100:
            can_buy = False
        elif current_balance > 150:
            can_buy = True

        if can_buy:
            last_buy = self.db.query(StrategyExecution).filter(
                StrategyExecution.strategy_id == self.strategy.id,
                StrategyExecution.order_type == "BUY"
            ).order_by(StrategyExecution.timestamp.desc()).first()
            
            should_buy = False
            if not last_buy:
                should_buy = True
            else:
                time_since = timestamp - last_buy.timestamp
                if time_since > timedelta(hours=params.get("interval_hours", 24)):
                    should_buy = True
            
            if should_buy:
                self.strategy.params = params
                flag_modified(self.strategy, "params")
                return self._execute_trade("BUY", params.get("amount", 2.0), current_price, timestamp)
        
        self.strategy.params = params
        flag_modified(self.strategy, "params")
        self.db.commit()
        return None

    def _execute_trade(self, order_type, amount, price, timestamp):
        order = self.exchange.place_market_order(self.strategy.ticker, order_type.lower(), amount / price, price)
        if not order:
            return None
            
        execution = StrategyExecution(
            strategy_id=self.strategy.id,
            order_type=order_type.upper(),
            price=price,
            amount=amount,
            timestamp=timestamp
        )
        self.db.add(execution)
        self.db.commit()
        return order

def run_backtest(df, initial_balance=1000.0):
    engine = BacktestEngine(initial_balance)
    equity_curve = []
    
    for index, row in df.iterrows():
        timestamp = index
        price = row['close']
        
        engine.evaluate(price, timestamp)
        
        # Calculate current equity
        avg_p, total_eth = engine._get_position_stats()
        current_equity = engine.exchange.get_balance() + (total_eth * price)
        equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'equity': current_equity,
            'price': price
        })
        
    # Calculate metrics
    final_equity = equity_curve[-1]['equity']
    total_pnl = final_equity - initial_balance
    
    # Max Drawdown
    max_equity = initial_balance
    max_dd = 0
    for point in equity_curve:
        if point['equity'] > max_equity:
            max_equity = point['equity']
        dd = (max_equity - point['equity']) / max_equity
        if dd > max_dd:
            max_dd = dd
            
    # Win Rate
    executions = engine.db.query(StrategyExecution).all()
    sells = [e for e in executions if e.order_type == "SELL"]
    # For win rate, we need to track PnL of each sell. 
    # This is simplified in backtester by looking at price vs avg_price at sell time.
    # But for now let's just count them.
    
    return {
        'total_pnl': total_pnl,
        'final_equity': final_equity,
        'max_drawdown': max_dd,
        'total_trades': len(executions),
        'equity_curve': equity_curve
    }
