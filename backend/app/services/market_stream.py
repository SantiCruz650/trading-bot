import asyncio
import json
import websockets
import logging
from typing import List, Set
from .websocket_manager import manager

from app.db.session import SessionLocal
from app.services.strategy_engine import StrategyEngine

logger = logging.getLogger(__name__)

class MarketStreamService:
    def __init__(self):
        self.base_url = "wss://stream.binance.com:9443/ws"
        self.tickers = ["btcusdt", "ethusdt", "adausdt", "solusdt", "dogeusdt"]
        self.running = False
        self.task = None

    async def start(self):
        self.running = True
        streams = "/".join([f"{t}@trade" for t in self.tickers])
        url = f"{self.base_url}/{streams}"
        
        logger.info(f"Connecting to Binance Stream: {url}")
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info("Connected to Binance WebSocket")
                    while self.running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        await self.process_message(data)
            except Exception as e:
                logger.error(f"Binance connection error: {e}")
                await asyncio.sleep(5)  # Reconnect delay

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def process_message(self, data: dict):
        try:
            symbol = data.get('s', '').replace('USDT', '')
            price = float(data.get('p', 0))
            
            if symbol and price:
                # Broadcast to frontend
                await manager.broadcast({
                    "type": "price_update",
                    "ticker": symbol,
                    "price": price,
                    "timestamp": data.get('E')
                })
                
                # Trigger Strategy Engine
                await asyncio.to_thread(self._run_strategy_engine, symbol, price)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _run_strategy_engine(self, ticker, price):
        db = SessionLocal()
        try:
            engine = StrategyEngine(db)
            engine.evaluate_strategies(ticker, price)
        except Exception as e:
            logger.error(f"Strategy Engine Error: {e}")
        finally:
            db.close()

market_stream = MarketStreamService()
