import asyncio
import logging
from datetime import datetime
from typing import List

from app.db.session import SessionLocal
from app.services.strategy_engine import StrategyEngine
from app.services.exchange_service import get_exchange
from app.models.models import Strategy, StrategyExecution

logger = logging.getLogger(__name__)

class PollingService:
    def __init__(self, interval_seconds: int = 60):
        self.tickers = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT", "DOGE/USDT"]
        self.interval = interval_seconds
        self.running = False
        self.task = None
        self.start_time = None
        self.last_action = "STOP"
        self.killed = False
        self.active_mode = None
        self.engine = None  # Will be injected at startup

    def save_state(self):
        """Persist current polling state to database."""
        from app.models.models import SystemState
        
        db = SessionLocal()
        try:
            state_data = {
                "running": self.running,
                "killed": self.killed,
                "active_mode": self.active_mode,
                "last_action": self.last_action
            }
            
            # Upsert
            state = db.query(SystemState).filter(SystemState.key == "polling_state").first()
            if not state:
                state = SystemState(key="polling_state", value=state_data)
                db.add(state)
            else:
                state.value = state_data
            
            db.commit()
            logger.debug("💾 PollingService state saved to DB")
        except Exception as e:
            logger.error(f"❌ Error saving PollingService state: {e}")
        finally:
            db.close()

    def load_state(self):
        """Load polling state from database."""
        from app.models.models import SystemState
        
        db = SessionLocal()
        try:
            state = db.query(SystemState).filter(SystemState.key == "polling_state").first()
            if state and state.value:
                data = state.value
                self.killed = data.get("killed", False)
                self.active_mode = data.get("active_mode", "MOCK")
                self.last_action = data.get("last_action", "STOP")
                was_running = data.get("running", False)
                logger.info(f"📂 Polling state loaded from DB. Killed: {self.killed}, Was Running: {was_running}")
                return was_running
        except Exception as e:
            logger.error(f"❌ Error loading PollingService state: {e}")
        finally:
            db.close()
        return False

    async def start(self, mode: str = "MOCK"):
        if self.killed:
            logger.error("❌ Cannot start polling: System KILLED and locked.")
            return

        self.running = True
        self.start_time = datetime.now()
        self.last_action = "START"
        self.active_mode = mode
        self.save_state()
        
        from app.core.config import settings
        logger.info(f"🤖 Bot running in {self.active_mode} MODE")
        logger.info(f"🚀 Interval: {self.interval}s | Tickers: {', '.join(self.tickers)}")
        
        cycle_count = 0
        while self.running:
            try:
                # ETAPA 7: Only reload global state from DB every 4 cycles (~2 mins at 30s)
                # to reduce Supabase egress unless important change detected.
                if cycle_count % 4 == 0:
                    self.load_state()
                    from app.services.risk_manager import RiskManager
                    RiskManager().load_state()
                
                cycle_count += 1
                
                if self.killed:
                    logger.warning("🚨 Polling loop active but system is KILLED. Skipping cycle.")
                    await asyncio.sleep(self.interval)
                    continue

                # Use settings to determine simulation mode
                exchange = get_exchange(local_simulation=settings.OBSERVATION_ONLY)
                
                for symbol in self.tickers:
                    if not self.running:
                        break
                        
                    price = exchange.get_ticker_price(symbol)
                    if price:
                        # Log only every 2 cycles per ticker to reduce log spam/egress
                        if cycle_count % 2 == 0:
                            balance = exchange.get_balance()
                            logger.info(f"🕒 [{datetime.now().strftime('%H:%M:%S')}] {symbol}: ${price:,.2f} | Bal: ${balance:,.2f}")
                        
                        # Trigger Strategy Engine
                        await asyncio.to_thread(self._run_strategy_engine, symbol, price)
                
                # Wait for the next interval
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"❌ Polling cycle error: {e}")
                await asyncio.sleep(10)

    async def stop(self):
        self.running = False
        self.last_action = "STOP"
        self.save_state()
        if self.task:
            self.task.cancel()
        logger.info("🛑 Polling Service stopped")

    def _run_strategy_engine(self, ticker, price):
        if not self.engine:
            logger.warning("⚠️ Strategy Engine not initialized yet in PollingService")
            return
            
        db = SessionLocal()
        try:
            self.engine.evaluate_strategies(ticker, price, db)
        except Exception as e:
            logger.error(f"Strategy Engine Error for {ticker}: {e}")
        finally:
            db.close()

    def _get_accumulated(self, ticker):
        """Calculate total accumulated asset for a ticker across all strategies using optimized SQL aggregates."""
        from sqlalchemy import func
        db = SessionLocal()
        try:
            # Join StrategyExecution with Strategy to filter by ticker
            # Optimize by performing calculation at DB level
            total_buy = db.query(func.sum(StrategyExecution.amount / StrategyExecution.price)).join(Strategy).filter(
                Strategy.ticker == ticker,
                StrategyExecution.order_type == "BUY"
            ).scalar() or 0.0
            
            total_sell = db.query(func.sum(StrategyExecution.amount / StrategyExecution.price)).join(Strategy).filter(
                Strategy.ticker == ticker,
                StrategyExecution.order_type == "SELL"
            ).scalar() or 0.0
            
            return total_buy - total_sell
        except Exception as e:
            logger.error(f"Error calculating accumulated for {ticker}: {e}")
            return 0.0
        finally:
            db.close()

polling_service = PollingService(interval_seconds=30)
