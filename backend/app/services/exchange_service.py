"""
Exchange Service - Binance Integration
Handles all communication with Binance exchange for live trading
"""
import ccxt
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)


from ..core.config import settings
from .market_simulator import market_simulator

class ExchangeService:
    """
    Wrapper for exchange API.
    Supports LOCAL_SIMULATION (no internet), testnet, and live.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, testnet: bool = True, local_simulation: bool = True):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ExchangeService, cls).__new__(cls)
                    cls._instance.initialized = False
        return cls._instance

    def __init__(self, testnet: bool = True, local_simulation: bool = True):
        """
        Initialize exchange connection
        
        Args:
            testnet: If True, use Binance testnet
            local_simulation: If True, use internal MarketSimulator (NO NETWORK)
        """
        if self.initialized:
            return
            
        # Prioridad a settings
        self.dry_run_real = settings.DRY_RUN_REAL_API
        self.local_simulation = settings.OBSERVATION_ONLY or local_simulation or settings.MOCK_EXCHANGE
        self.testnet = settings.BINANCE_TESTNET
        
        # Check for missing keys
        if not self.local_simulation:
            if not settings.BINANCE_API_KEY or not settings.BINANCE_API_SECRET:
                if not self.testnet or (not settings.BINANCE_TESTNET_API_KEY or not settings.BINANCE_TESTNET_API_SECRET):
                    logger.warning("Missing API credentials. Forcing LOCAL SIMULATION (MOCK).")
                    self.local_simulation = True

        # Si Dry Run Real está activo, forzamos desactivación de simulación local 
        # para que intente conectar a API real, pero con el bloqueo de seguridad activo.
        if self.dry_run_real and not settings.MOCK_EXCHANGE:
            # Re-check keys for dry_run_real
            if settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET:
                self.local_simulation = False
                self.testnet = False # Usar Live API
                print("🚀 DRY_RUN_REAL_API ACTIVE: Connecting to REAL API with Safety Block")
            else:
                print("⚠️ DRY_RUN_REAL_API requested but keys missing. Staying in MOCK mode.")
                self.local_simulation = True
        
        self.exchange = None
        self.virtual_balance = 1000.0  # Initial virtual balance for local simulation
        
        if not self.local_simulation:
            self._initialize_exchange()
        else:
            if settings.MOCK_EXCHANGE:
                print("🧪 MOCK_EXCHANGE_MODE ACTIVE: All calls simulated.")
            print("💰 Virtual balance initialized: 1000.0 USDT")
            print("📈 Market Simulator ACTIVE (Local Paper Trading)")
            
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
                logger.warning("Missing API credentials. Defaulting to LOCAL SIMULATION.")
                self.local_simulation = True
                return
            
            # Initialize ccxt Binance exchange
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
            
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                logger.info("✅ Connected to Binance TESTNET (Paper Trading)")
            else:
                logger.warning("⚠️ Connected to Binance LIVE (REAL MONEY)")
                
            self.exchange.load_markets()
            logger.info(f"Exchange initialized successfully. Markets loaded: {len(self.exchange.markets)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}. Falling back to LOCAL SIMULATION.")
            self.local_simulation = True
    
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get account balance"""
        if self.local_simulation:
            return self.virtual_balance
            
        try:
            balance = self.exchange.fetch_balance()
            return float(balance.get(currency, {}).get('free', 0.0))
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """Get current market price"""
        if self.local_simulation:
            # Use local simulator
            # Ensure symbol format is correct (e.g. BTC/USDT)
            if '/' not in symbol and 'USDT' in symbol:
                symbol = symbol.replace('USDT', '/USDT')
            return market_simulator.get_price(symbol)
            
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
        """Place a market order"""
        try:
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
            
            if amount <= 0:
                raise ValueError(f"Invalid amount: {amount}. Must be positive")
            
            price = self.get_ticker_price(symbol)
            if not price:
                return None
                
            cost = amount * price
            
            if self.local_simulation:
                if side == 'buy' and cost > self.virtual_balance:
                    logger.error(f"Insufficient virtual balance: {self.virtual_balance} < {cost}")
                    return None
                
                # Update virtual balance
                if side == 'buy':
                    self.virtual_balance -= cost
                else:
                    self.virtual_balance += cost
                
                order_id = f"sim_{int(datetime.now().timestamp())}"
                logger.info(f"✅ [SIM] {side.upper()} {amount} {symbol} @ ${price:,.2f} | Balance: ${self.virtual_balance:,.2f}")
                
                return {
                    'id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': 'filled'
                }
            
            # DRY_RUN_REAL_API Safety Block
            if self.dry_run_real or not settings.ENABLE_REAL_TRADING:
                latency = 0
                try:
                    import time
                    start_t = time.perf_counter()
                    # Just a test call to check connectivity and latency
                    self.exchange.fetch_status()
                    latency = (time.perf_counter() - start_t) * 1000
                except:
                    pass
                    
                order_id = f"dry_run_{int(datetime.now().timestamp())}"
                intent_label = f"INTENT_{side.upper()}"
                
                logger.warning(f"🛡️ {intent_label} | {amount} {symbol} @ ${price:,.2f} | Latency: {latency:.2f}ms")
                print(f"🛡️ DRY_RUN: {intent_label} {amount} {symbol} intercepted. Latency: {latency:.2f}ms")
                
                return {
                    'id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': 'filled',
                    'info': {'dry_run': True, 'latency_ms': latency, 'intent': intent_label}
                }

            # Real order via ccxt (ONLY IF ENABLE_REAL_TRADING IS TRUE)
            if settings.ENABLE_REAL_TRADING:
                logger.info(f"🚀 EXECUTING REAL {side.upper()} market order: {amount} {symbol}")
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=side,
                    amount=amount
                )
                return order
            
            return None
            
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

def get_exchange(testnet: bool = True, local_simulation: bool = True) -> ExchangeService:
    """Get or create exchange service instance"""
    global _exchange_instance
    if _exchange_instance is None:
        _exchange_instance = ExchangeService(testnet=testnet, local_simulation=local_simulation)
    return _exchange_instance
