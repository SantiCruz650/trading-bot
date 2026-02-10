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

    async def start(self):
        self.running = True
        logger.info(f"🤖 Bot running in LOCAL PAPER TRADING MODE")
        logger.info(f"📈 Market Simulator ACTIVE")
        logger.info(f"🚀 Interval: {self.interval}s | Tickers: {', '.join(self.tickers)}")
        
        while self.running:
            try:
                # Use local_simulation=True for 100% local paper trading
                exchange = get_exchange(local_simulation=True)
                
                for symbol in self.tickers:
                    if not self.running:
                        break
                        
                    # In local simulation, ExchangeService.exchange is None,
                    # but we can call get_ticker_price which uses market_simulator.
                    price = exchange.get_ticker_price(symbol)
                    if price:
                        ticker_name = symbol.split('/')[0]
                        balance = exchange.get_balance()
                        
                        # Get accumulated asset amount for this ticker
                        # We'll use a helper to get this from the database
                        accumulated = self._get_accumulated(ticker_name)
                        
                        # Log the cycle
                        print(f"🕒 [{datetime.now().strftime('%H:%M:%S')}] {symbol}: ${price:,.2f} | Balance: ${balance:,.2f} | {ticker_name}: {accumulated:.6f}")
                        
                        # Trigger Strategy Engine
                        await asyncio.to_thread(self._run_strategy_engine, ticker_name, price)
                
                # Wait for the next interval
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"❌ Polling cycle error: {e}")
                await asyncio.sleep(10)  # Silent retry delay

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("🛑 Polling Service stopped")

    def _run_strategy_engine(self, ticker, price):
        db = SessionLocal()
        try:
            engine = StrategyEngine(db)
            engine.evaluate_strategies(ticker, price)
        except Exception as e:
            logger.error(f"Strategy Engine Error for {ticker}: {e}")
        finally:
            db.close()

    def _get_accumulated(self, ticker):
        """Calculate total accumulated asset for a ticker across all strategies."""
        db = SessionLocal()
        try:
            # Join StrategyExecution with Strategy to filter by ticker
            executions = db.query(StrategyExecution).join(Strategy).filter(
                Strategy.ticker == ticker
            ).all()
            
            total_asset = 0.0
            for ex in executions:
                asset_amount = ex.amount / ex.price
                if ex.order_type == "BUY":
                    total_asset += asset_amount
                else:
                    total_asset -= asset_amount
            return total_asset
        except Exception:
            return 0.0
        finally:
            db.close()

polling_service = PollingService(interval_seconds=15)
