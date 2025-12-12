"""
Exchange Service - Binance Integration
Handles all communication with Binance exchange for live trading
"""
import ccxt
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


from ..core.config import settings

class ExchangeService:
    """
    Wrapper for Binance exchange API using ccxt
    Supports both live trading and testnet (paper trading)
    """
    _instance = None

    def __new__(cls, testnet: bool = True):
        if cls._instance is None:
            cls._instance = super(ExchangeService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, testnet: bool = True):
        """
        Initialize exchange connection
        
        Args:
            testnet: If True, use Binance testnet (paper trading)
            If False, use live Binance (REAL MONEY)
        """
        if self.initialized:
            return
            
        self.testnet = testnet
        self.exchange = None
        self._initialize_exchange()
        self.initialized = True
        
    def _initialize_exchange(self):
        """Initialize Binance exchange connection"""
        try:
            # Get API credentials from settings
            if self.testnet:
                api_key = settings.BINANCE_TESTNET_API_KEY
                api_secret = settings.BINANCE_TESTNET_API_SECRET
            else:
                api_key = settings.BINANCE_API_KEY
                api_secret = settings.BINANCE_API_SECRET
            
            if not api_key or not api_secret:
                raise ValueError(
                    f"Missing API credentials in environment variables. "
                    f"Set {'BINANCE_TESTNET_API_KEY/SECRET' if self.testnet else 'BINANCE_API_KEY/SECRET'}"
                )
            
            # Initialize ccxt Binance exchange
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,  # Critical for avoiding API bans
                'options': {
                    'defaultType': 'spot',  # Use spot trading (not futures)
                }
            })
            
            # Set testnet URL if in testnet mode
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                logger.info("✅ Connected to Binance TESTNET (Paper Trading)")
            else:
                logger.warning("⚠️ Connected to Binance LIVE (REAL MONEY)")
                
            # Test connection
            self.exchange.load_markets()
            logger.info(f"Exchange initialized successfully. Markets loaded: {len(self.exchange.markets)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise
    
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get account balance for specific currency"""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance.get(currency, {}).get('free', 0.0))
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        amount: float,
        stop_loss_pct: Optional[float] = None
    ) -> Optional[Dict]:
        """Place a market order (executes immediately at current price)"""
        try:
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
            
            if amount <= 0:
                raise ValueError(f"Invalid amount: {amount}. Must be positive")
            
            logger.info(f"Placing {side.upper()} market order: {amount} {symbol}")
            
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount
            )
            
            logger.info(f"✅ Order placed successfully: {order['id']}")
            
            # If stop-loss specified and order is a buy, place stop-loss order
            if stop_loss_pct and side == 'buy':
                fill_price = float(order.get('average', order.get('price', 0)))
                if fill_price > 0:
                    stop_price = fill_price * (1 - stop_loss_pct)
                    self._place_stop_loss(symbol, amount, stop_price)
            
            return order
            
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    def _place_stop_loss(self, symbol: str, amount: float, stop_price: float):
        """Place a stop-loss order"""
        try:
            logger.info(f"Placing stop-loss: {amount} {symbol} @ {stop_price}")
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='stop_loss_limit',
                side='sell',
                amount=amount,
                price=stop_price,
                params={'stopPrice': stop_price}
            )
            
            logger.info(f"✅ Stop-loss placed: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing stop-loss: {e}")
            return None
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all open orders (EMERGENCY USE)"""
        try:
            open_orders = self.exchange.fetch_open_orders(symbol=symbol)
            cancelled = 0
            
            for order in open_orders:
                try:
                    self.exchange.cancel_order(order['id'], order['symbol'])
                    cancelled += 1
                except:
                    pass
            
            logger.warning(f"⚠️ Cancelled {cancelled} open orders")
            return cancelled
            
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return 0
    
    def close_all_positions(self) -> Dict[str, float]:
        """EMERGENCY: Close all positions immediately at market price"""
        try:
            balance = self.exchange.fetch_balance()
            closed = {}
            
            for currency, amounts in balance.get('total', {}).items():
                amount = float(amounts)
                if currency == 'USDT' or amount <= 0:
                    continue
                
                symbol = f"{currency}/USDT"
                if symbol in self.exchange.markets:
                    logger.warning(f"🚨 EMERGENCY CLOSE: Selling {amount} {currency}")
                    order = self.place_market_order(symbol, 'sell', amount)
                    if order:
                        closed[symbol] = amount
            
            return closed
            
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            return {}


# Singleton instance
_exchange_instance = None

def get_exchange(testnet: bool = True) -> ExchangeService:
    """Get or create exchange service instance"""
    global _exchange_instance
    if _exchange_instance is None:
        _exchange_instance = ExchangeService(testnet=testnet)
    return _exchange_instance
