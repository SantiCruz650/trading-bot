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

    def __new__(cls, testnet: bool = False, local_simulation: bool = False):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ExchangeService, cls).__new__(cls)
                    cls._instance.initialized = False
        return cls._instance

    def __init__(self, testnet: bool = False, local_simulation: bool = False):
        """
        Initialize exchange connection
        
        Args:
            testnet: If True, use Binance testnet
            local_simulation: If True, use internal MarketSimulator (NO NETWORK)
        """
        if self.initialized:
            return
            
        # Prioridad a settings. Si local_simulation se pasa como True, se respeta, 
        # pero por defecto seguimos MOCK_EXCHANGE.
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
            # Get API credentials from settings and AGGRESSIVELY SANITIZE
            def clean_key(val):
                if not val: return ""
                # Remove all whitespace, newlines, and common "smart" characters from Google Docs/Chat
                return str(val).strip().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

            if self.testnet:
                api_key = clean_key(settings.BINANCE_TESTNET_API_KEY)
                api_secret = clean_key(settings.BINANCE_TESTNET_API_SECRET)
            else:
                api_key = clean_key(settings.BINANCE_API_KEY)
                api_secret = clean_key(settings.BINANCE_API_SECRET)
            
            if not api_key or not api_secret:
                logger.warning("Missing API credentials. Defaulting to LOCAL SIMULATION.")
                self.local_simulation = True
                return
            
            # Diagnostic: Log key metadata safely
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
            logger.info(f"🔑 Initializing Binance API (Key: {masked_key}, Length: {len(api_key)}, Secret Length: {len(api_secret)})")

            # Initialize ccxt Binance exchange
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True, # Crucial for -2015 errors
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

    def round_amount(self, symbol: str, amount: float) -> float:
        """Round amount based on exchange rules"""
        if self.local_simulation or not self.exchange:
            return round(amount, 6)
        return float(self.exchange.amount_to_precision(symbol, amount))

    def round_price(self, symbol: str, price: float) -> float:
        """Round price based on exchange rules"""
        if self.local_simulation or not self.exchange:
            return round(price, 2)
        return float(self.exchange.price_to_precision(symbol, price))

    def get_balance(self, currency: str = 'USDT', user_mode: str = "LIVE", username: str = "prodbymontu") -> float:
        """Get account balance"""
        # Force simulation if user mode is MOCK
        is_simulation = self.local_simulation or user_mode == "MOCK"
        
        if is_simulation:
            if username == "test":
                if not hasattr(self, 'test_virtual_balance'):
                    self.test_virtual_balance = 13000.0
                return self.test_virtual_balance
            else:
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
            # Expects symbol format (e.g. BTC/USDT)
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
        stop_loss_pct: Optional[float] = None,
        user_mode: str = "MOCK",
        username: str = "test"
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
            
            # --- SECURITY AUDIT: Precision Rounding ---
            amount = self.round_amount(symbol, amount)
            # Fetch current market price again if needed, or just use the one we got
            price = self.round_price(symbol, price)
                
            cost = amount * price
            
            # Force simulation if user mode is MOCK
            is_simulation = self.local_simulation or user_mode == "MOCK"
            
            # --- SECURITY AUDIT: Balance Validation (Real API) ---
            if not is_simulation:
                try:
                    current_free_usdt = self.get_balance('USDT')
                    # Estimate cost with 0.1% buffer for fees
                    estimated_total_cost = cost * 1.001 
                    if side == 'buy' and estimated_total_cost > current_free_usdt:
                        logger.error(f"❌ Fondos insuficientes: Necesitas {estimated_total_cost:.2f} USDT, tienes {current_free_usdt:.2f} USDT")
                        raise ValueError("Fondos insuficientes")
                except Exception as e:
                    if "Fondos insuficientes" in str(e): raise e
                    logger.warning(f"Could not verify balance before trade: {e}")
            
            if is_simulation:
                # Update virtual balance with fees (0.1% = 0.001)
                fee = cost * 0.001
                if side == 'buy':
                    if username == "test":
                        if cost + fee > getattr(self, 'test_virtual_balance', 13000.0):
                            logger.error(f"Insufficient test virtual balance: {getattr(self, 'test_virtual_balance', 13000.0)} < {cost + fee}")
                            return None
                        self.test_virtual_balance -= (cost + fee)
                        current_virtual = self.test_virtual_balance
                    else:
                        if cost + fee > self.virtual_balance:
                            logger.error(f"Insufficient virtual balance (including fees): {self.virtual_balance} < {cost + fee}")
                            return None
                        self.virtual_balance -= (cost + fee)
                        current_virtual = self.virtual_balance
                else:
                    if username == "test":
                        self.test_virtual_balance += (cost - fee)
                        current_virtual = self.test_virtual_balance
                    else:
                        self.virtual_balance += (cost - fee)
                        current_virtual = self.virtual_balance
                
                order_id = f"sim_{int(datetime.now().timestamp())}"
                logger.info(f"✅ [SIM {username}] {side.upper()} {amount} {symbol} @ ${price:,.2f} | Fee: ${fee:.4f} | Balance: ${current_virtual:,.2f}")
                
                return {
                    'id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'fee': fee,
                    'status': 'filled'
                }
            
            # DRY_RUN Safety Block
            if user_mode == "DRY_RUN":
                latency = 0
                try:
                    import time
                    start_t = time.perf_counter()
                    # Just a test call to check connectivity and latency
                    self.exchange.fetch_status()
                    latency = (time.perf_counter() - start_t) * 1000
                except:
                    pass
                    
                fee = cost * 0.001
                order_id = f"dry_run_{int(datetime.now().timestamp())}"
                intent_label = f"INTENT_{side.upper()}"
                
                logger.warning(f"🛡️ DRY_RUN | {amount} {symbol} @ ${price:,.2f} | Fee (Est): ${fee:.4f} | Latency: {latency:.2f}ms")
                print(f"🛡️ DRY_RUN: {intent_label} {amount} {symbol} intercepted. Latency: {latency:.2f}ms")
                
                return {
                    'id': order_id,
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'fee': fee,
                    'status': 'filled',
                    'info': {'dry_run': True, 'latency_ms': latency, 'intent': intent_label}
                }

            # Real order via ccxt (ONLY IF user_mode == LIVE)
            if user_mode == "LIVE":
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

def get_exchange(testnet: bool = False, local_simulation: bool = False) -> ExchangeService:
    """Get or create exchange service instance"""
    global _exchange_instance
    if _exchange_instance is None:
        _exchange_instance = ExchangeService(testnet=testnet, local_simulation=local_simulation)
    return _exchange_instance
