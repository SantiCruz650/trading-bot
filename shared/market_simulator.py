import random
from typing import Dict, List
from datetime import datetime

class MarketSimulator:
    """
    Simulates market data using a random walk algorithm.
    Provides OHLCV data for local paper trading without external APIs.
    """
    def __init__(self):
        # Initial prices for supported tickers
        self.prices = {
            "BTC/USDT": 45000.0,
            "ETH/USDT": 2500.0,
            "ADA/USDT": 0.50,
            "SOL/USDT": 100.0,
            "DOGE/USDT": 0.08
        }
        # Volatility factors for each ticker
        self.volatility = {
            "BTC/USDT": 0.0005,
            "ETH/USDT": 0.0008,
            "ADA/USDT": 0.0015,
            "SOL/USDT": 0.0020,
            "DOGE/USDT": 0.0030
        }

    def get_price(self, symbol: str) -> float:
        """Update and return the current price for a symbol using random walk."""
        if symbol not in self.prices:
            return 0.0
        
        # Random walk: price = price * (1 + random_change)
        change = random.uniform(-self.volatility[symbol], self.volatility[symbol])
        self.prices[symbol] *= (1 + change)
        
        return self.prices[symbol]

    def get_ohlcv(self, symbol: str) -> List:
        """Generate a simulated 1m OHLCV candle."""
        current_price = self.get_price(symbol)
        if current_price == 0.0:
            return []
            
        # Simulate high/low/open around current price
        vol = self.volatility[symbol]
        open_price = current_price * (1 + random.uniform(-vol/2, vol/2))
        high = max(open_price, current_price) * (1 + random.uniform(0, vol))
        low = min(open_price, current_price) * (1 - random.uniform(0, vol))
        volume = random.uniform(10, 100)
        
        # Format: [timestamp, open, high, low, close, volume]
        return [
            int(datetime.now().timestamp() * 1000),
            open_price,
            high,
            low,
            current_price,
            volume
        ]

# Singleton instance
market_simulator = MarketSimulator()
