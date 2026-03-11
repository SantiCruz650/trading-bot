import random
import logging

logger = logging.getLogger(__name__)

class MarketSimulator:
    """
    Simulates real-time market behavior for testing and mock mode.
    Maintains a dictionary of prices and provides tiny movements to mimic life.
    """
    def __init__(self):
        self.prices = {
            "ETH/USDT": 2036.0,
            "BTC/USDT": 45000.0,
            "BNB/USDT": 300.0
        }

    def get_price(self, symbol: str) -> float:
        # Ensure symbol format is canonical for the simulator
        if symbol not in self.prices:
            # Fallback for dynamic symbols
            self.prices[symbol] = 100.0
            
        # Add a tiny bit of noise (+/- 0.01%) to make it feel alive in the dashboard
        noise_factor = (random.random() - 0.5) * 0.0002 # 0.02% range
        current_price = self.prices[symbol]
        mock_price = current_price * (1 + noise_factor)
        
        # Slightly drift the base price so it actually moves over time
        self.prices[symbol] = mock_price
        
        return mock_price

    def update_price(self, symbol: str, price: float):
        """Allows manual price overrides if needed for testing scenarios."""
        self.prices[symbol] = price

# Canonical singleton instance for the app
market_simulator = MarketSimulator()
