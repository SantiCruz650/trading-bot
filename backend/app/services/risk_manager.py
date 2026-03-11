import math
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RiskManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, bankroll: float = 10000.0):
        if getattr(self, "initialized", False):
            return
            
        self.bankroll = bankroll
        self.max_risk_per_trade = 0.05 # Never risk more than 5% of bankroll
        
        # ETAPA 2A - State Management
        self._gec_state = "NORMAL"  # NORMAL, SOFT_CAP, HARD_CAP, KILL_SWITCH
        self._freeze_active = False
        self._freeze_reason = None
        self._kill_switch_active = False
        
        # Daily tracking (reset at midnight)
        self._daily_start_time = datetime.utcnow().date()
        self._daily_start_equity = bankroll
        self._daily_peak_equity = bankroll
        self._current_equity = bankroll
        
        # Position tracking
        self._total_position_value = 0.0
        
        # Consecutive losses tracking
        self._consecutive_losses = 0
        self._last_cycle_profitable = None
        
        # Import settings
        try:
            from app.core.config import settings
            self.settings = settings
        except ImportError:
            # Fallback defaults
            class FallbackSettings:
                ETAPA_2A_ACTIVE = True
                GEC_SOFT_CAP = 0.65
                GEC_HARD_CAP = 0.80
                FREEZE_DD_THRESHOLD = 0.015
                KILL_SWITCH_DD_THRESHOLD = 0.030
                KILL_SWITCH_ER_THRESHOLD = 0.95
                KILL_SWITCH_CONSECUTIVE_LOSSES = 5
            self.settings = FallbackSettings()

        self.load_state()
        self.initialized = True

    def save_state(self):
        """Persist current risk state to database."""
        from app.db.session import SessionLocal
        from app.models.models import SystemState
        
        db = SessionLocal()
        try:
            state_data = {
                "gec_state": self._gec_state,
                "freeze_active": self._freeze_active,
                "freeze_reason": self._freeze_reason,
                "kill_switch_active": self._kill_switch_active,
                "consecutive_losses": self._consecutive_losses
            }
            
            # Upsert
            state = db.query(SystemState).filter(SystemState.key == "risk_manager_state").first()
            if not state:
                state = SystemState(key="risk_manager_state", value=state_data)
                db.add(state)
            else:
                state.value = state_data
            
            db.commit()
            logger.debug("💾 RiskManager state saved to DB")
        except Exception as e:
            logger.error(f"❌ Error saving RiskManager state: {e}")
        finally:
            db.close()

    def load_state(self):
        """Load risk state from database."""
        from app.db.session import SessionLocal
        from app.models.models import SystemState
        
        db = SessionLocal()
        try:
            state = db.query(SystemState).filter(SystemState.key == "risk_manager_state").first()
            if state and state.value:
                data = state.value
                self._gec_state = data.get("gec_state", "NORMAL")
                self._freeze_active = data.get("freeze_active", False)
                self._freeze_reason = data.get("freeze_reason")
                self._kill_switch_active = data.get("kill_switch_active", False)
                self._consecutive_losses = data.get("consecutive_losses", 0)
                logger.info(f"📂 RiskManager state loaded from DB: {self._gec_state}")
        except Exception as e:
            logger.error(f"❌ Error loading RiskManager state: {e}")
        finally:
            db.close()

    def calculate_kelly_bet(self, win_prob: float, win_loss_ratio: float = 2.0) -> float:
        """
        Calculate optimal bet size using Kelly Criterion.
        f* = (bp - q) / b
        where:
        f* = fraction of bankroll to wager
        b = odds received on the wager (win_loss_ratio)
        p = probability of winning
        q = probability of losing (1 - p)
        """
        if win_prob <= 0.5:
            return 0.0
            
        q = 1.0 - win_prob
        f_star = ((win_loss_ratio * win_prob) - q) / win_loss_ratio
        
        # Half-Kelly is safer for real trading to avoid ruin
        safe_kelly = f_star * 0.5
        
        # Cap at max risk
        return max(0.0, min(safe_kelly, self.max_risk_per_trade))

    def get_position_size(self, confidence: str, current_price: float) -> float:
        """
        Determine position size based on ML confidence.
        """
        # Map confidence to probability (simplified)
        if confidence == "HIGH":
            win_prob = 0.65
        elif confidence == "MEDIUM":
            win_prob = 0.55
        else:
            win_prob = 0.50
            
        kelly_fraction = self.calculate_kelly_bet(win_prob)
        position_value = self.bankroll * kelly_fraction
        
        return position_value / current_price

    def calculate_sl_tp(self, entry_price: float, side: str, risk_reward_ratio: float = 2.0) -> tuple:
        """
        Calculate Stop Loss and Take Profit levels.
        Default strategy: 1:2 Risk/Reward with dynamic stop loss based on volatility (simulated here as fixed %)
        """
        # In a real app, this would use ATR (Average True Range) for dynamic stops
        stop_loss_pct = 0.02 # 2% default stop loss
        
        if side.upper() == 'BUY':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + (stop_loss_pct * risk_reward_ratio))
        else: # SELL
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - (stop_loss_pct * risk_reward_ratio))
            
        return stop_loss, take_profit

    # ============================================================================
    # ETAPA 2A - Global Exposure Cap (GEC)
    # ============================================================================
    
    def update_equity(self, current_balance: float, total_position_value: float):
        """Update current equity and position tracking."""
        self._check_daily_reset()
        
        self._current_equity = current_balance + total_position_value
        self._total_position_value = total_position_value
        
        # Update peak equity
        if self._current_equity > self._daily_peak_equity:
            self._daily_peak_equity = self._current_equity
            
        # Log equity
        logger.debug(f"💰 Equity Update: Balance=${current_balance:.2f}, Positions=${total_position_value:.2f}, Total=${self._current_equity:.2f}")
    
    def calculate_exposure_ratio(self) -> float:
        """Calculate Exposure Ratio (ER) = total_position_value / total_equity."""
        if self._current_equity <= 0:
            return 0.0
        
        er = self._total_position_value / self._current_equity
        logger.debug(f"📊 Exposure Ratio: {er:.4f} (Positions: ${self._total_position_value:.2f} / Equity: ${self._current_equity:.2f})")
        return er
    
    def calculate_daily_drawdown(self) -> float:
        """Calculate daily drawdown from peak equity."""
        if self._daily_peak_equity <= 0:
            return 0.0
        
        dd = (self._daily_peak_equity - self._current_equity) / self._daily_peak_equity
        logger.debug(f"📉 Daily Drawdown: {dd*100:.2f}% (Peak: ${self._daily_peak_equity:.2f}, Current: ${self._current_equity:.2f})")
        return dd
    
    def update_gec_state(self):
        """Update GEC state based on current ER."""
        if not self.settings.ETAPA_2A_ACTIVE:
            return
        
        er = self.calculate_exposure_ratio()
        old_state = self._gec_state
        
        # Check Kill-Switch conditions first
        if self._should_trigger_kill_switch():
            if self._gec_state != "KILL_SWITCH":
                self._gec_state = "KILL_SWITCH"
                self._kill_switch_active = True
                logger.critical(f"🚨🚨🚨 KILL-SWITCH ACTIVATED at {datetime.utcnow().isoformat()} - Trading HALTED")
                self._log_kill_switch_trigger()
        elif er >= self.settings.GEC_HARD_CAP:
            self._gec_state = "HARD_CAP"
        elif er >= self.settings.GEC_SOFT_CAP:
            self._gec_state = "SOFT_CAP"
        else:
            self._gec_state = "NORMAL"
        
        # Log state transition
        if old_state != self._gec_state:
            logger.warning(f"⚠️ GEC State Transition: {old_state} → {self._gec_state} | ER={er:.4f} | Timestamp: {datetime.utcnow().isoformat()}")
            self.save_state()
    
    def get_gec_adjustments(self) -> Dict[str, float]:
        """Get order size and DCA step adjustments based on GEC state."""
        adjustments = {
            "order_size_multiplier": 1.0,
            "dca_step_multiplier": 1.0
        }
        
        if self._gec_state == "SOFT_CAP":
            adjustments["order_size_multiplier"] = 0.70  # Reduce by 30%
            adjustments["dca_step_multiplier"] = 1.25    # Increase by 25%
            logger.info(f"⚖️ GEC Soft Cap Active: Order size -30%, DCA step +25%")
        
        return adjustments
    
    def can_open_position(self, db, side: str = "BUY") -> Tuple[bool, str]:
        """Check if opening a new position is allowed based on GEC state and limits."""
        if not self.settings.ETAPA_2A_ACTIVE:
            return True, "OK"
        
        # --- SECURITY AUDIT: Limit Simultaneous Orders ---
        if side.upper() == "BUY":
            from app.models.models import PaperTrade
            open_positions_count = db.query(PaperTrade).filter(PaperTrade.status == "OPEN").count()
            max_orders = getattr(self.settings, "MAX_SIMULTANEOUS_ORDERS", 5)
            if open_positions_count >= max_orders:
                reason = f"🚫 Límite de órdenes alcanzado: {open_positions_count}/{max_orders} posiciones abiertas."
                logger.warning(reason)
                return False, reason

        # Update GEC state first
        self.update_gec_state()
        
        # Check Kill-Switch
        if self._kill_switch_active:
            reason = "🚨 Kill-Switch active - All trading HALTED"
            logger.error(reason)
            return False, reason
        
        # Check Freeze
        if self._freeze_active:
            reason = f"❄️ Freeze active - {self._freeze_reason}"
            logger.warning(reason)
            return False, reason
        
        # Hard Cap blocks all new BUYs
        if self._gec_state == "HARD_CAP" and side.upper() == "BUY":
            reason = f"🚫 Hard Cap reached (ER={self.calculate_exposure_ratio():.4f}) - BUY orders blocked (Exit-Only mode)"
            logger.warning(reason)
            return False, reason
        
        return True, "OK"
    
    # ============================================================================
    # ETAPA 2A - Freeze Mechanism
    # ============================================================================
    
    def check_freeze_conditions(self, regime: str = "UNKNOWN"):
        """Check and activate Freeze if conditions are met."""
        if not self.settings.ETAPA_2A_ACTIVE:
            return
        
        dd = self.calculate_daily_drawdown()
        
        # Freeze on high drawdown
        if dd > self.settings.FREEZE_DD_THRESHOLD:
            if not self._freeze_active:
                self._activate_freeze(f"Daily Drawdown exceeds {self.settings.FREEZE_DD_THRESHOLD*100:.1f}% (Current: {dd*100:.2f}%)")
        # Freeze on high volatility regime
        elif regime == "HIGH_VOLATILITY":
            if not self._freeze_active:
                self._activate_freeze("HIGH_VOLATILITY regime detected")
        else:
            # Deactivate freeze if conditions normalized
            if self._freeze_active:
                self._deactivate_freeze()
    
    def _activate_freeze(self, reason: str):
        """Activate Freeze mechanism."""
        self._freeze_active = True
        self._freeze_reason = reason
        timestamp = datetime.utcnow().isoformat()
        logger.warning(f"❄️ FREEZE ACTIVATED at {timestamp} - Reason: {reason}")
        self.save_state()
    
    def _deactivate_freeze(self):
        """Deactivate Freeze mechanism."""
        timestamp = datetime.utcnow().isoformat()
        logger.info(f"✅ FREEZE DEACTIVATED at {timestamp} - Conditions normalized")
        self._freeze_active = False
        self._freeze_reason = None
        self.save_state()
    
    # ============================================================================
    # ETAPA 2A - Kill-Switch
    # ============================================================================
    
    def _should_trigger_kill_switch(self) -> bool:
        """Check if Kill-Switch should be triggered."""
        if not self.settings.ETAPA_2A_ACTIVE:
            return False
        
        if self._kill_switch_active:
            return True  # Already active
        
        dd = self.calculate_daily_drawdown()
        er = self.calculate_exposure_ratio()
        
        # Condition 1: Daily DD > 3.0%
        if dd > self.settings.KILL_SWITCH_DD_THRESHOLD:
            logger.critical(f"🚨 Kill-Switch Condition 1 MET: DD={dd*100:.2f}% > {self.settings.KILL_SWITCH_DD_THRESHOLD*100:.1f}%")
            return True
        
        # Condition 2: ER > 0.95
        if er > self.settings.KILL_SWITCH_ER_THRESHOLD:
            logger.critical(f"🚨 Kill-Switch Condition 2 MET: ER={er:.4f} > {self.settings.KILL_SWITCH_ER_THRESHOLD:.2f}")
            return True
        
        # Condition 3: 5 consecutive losses
        if self._consecutive_losses >= self.settings.KILL_SWITCH_CONSECUTIVE_LOSSES:
            logger.critical(f"🚨 Kill-Switch Condition 3 MET: {self._consecutive_losses} consecutive losses >= {self.settings.KILL_SWITCH_CONSECUTIVE_LOSSES}")
            return True
        
        return False
    
    def _log_kill_switch_trigger(self):
        """Log detailed information when Kill-Switch triggers."""
        er = self.calculate_exposure_ratio()
        dd = self.calculate_daily_drawdown()
        
        log_msg = f"""
        ╔════════════════════════════════════════════════════════════╗
        ║               KILL-SWITCH ACTIVATION LOG                   ║
        ╠════════════════════════════════════════════════════════════╣
        ║ Timestamp: {datetime.utcnow().isoformat()}
        ║ Exposure Ratio: {er:.4f}
        ║ Daily Drawdown: {dd*100:.2f}%
        ║ Consecutive Losses: {self._consecutive_losses}
        ║ Current Equity: ${self._current_equity:.2f}
        ║ Daily Peak Equity: ${self._daily_peak_equity:.2f}
        ║ Position Value: ${self._total_position_value:.2f}
        ╚════════════════════════════════════════════════════════════╝
        """
        logger.critical(log_msg)
    
    def record_cycle_outcome(self, profitable: bool):
        """Record whether a trading cycle was profitable or not."""
        if profitable:
            self._consecutive_losses = 0
            self._last_cycle_profitable = True
            logger.debug(f"✅ Profitable cycle - Consecutive losses reset to 0")
        else:
            self._consecutive_losses += 1
            self._last_cycle_profitable = False
            logger.debug(f"❌ Losing cycle - Consecutive losses: {self._consecutive_losses}")
        
        self.save_state()
    
    # ============================================================================
    # Properties
    # ============================================================================
    
    @property
    def gec_state(self) -> str:
        return self._gec_state
    
    @property
    def freeze_active(self) -> bool:
        return self._freeze_active
    
    @property
    def freeze_reason(self) -> Optional[str]:
        return self._freeze_reason
    
    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch_active
    
    @property
    def circuit_breaker_active(self):
        """Legacy property for compatibility."""
        return self._freeze_active or self._kill_switch_active

    @property
    def circuit_breaker_reason(self):
        """Legacy property for compatibility."""
        if self._kill_switch_active:
            return "Kill-Switch Active"
        return self._freeze_reason
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def _check_daily_reset(self):
        """Reset daily stats if new day."""
        current_date = datetime.utcnow().date()
        if current_date > self._daily_start_time:
            logger.info(f"📅 Daily reset: {self._daily_start_time} → {current_date}")
            self._daily_start_time = current_date
            self._daily_start_equity = self._current_equity
            self._daily_peak_equity = self._current_equity
            # Note: Do NOT reset consecutive losses (spans multiple days)

    def can_trade(self, current_balance: float) -> tuple:
        """Check if trading is allowed based on risk rules"""
        if current_balance < 10.0:
            return False, "Insufficient balance"
        
        # Check ETAPA 2A conditions
        if self.settings.ETAPA_2A_ACTIVE:
            can_open, reason = self.can_open_position()
            if not can_open:
                return False, reason
        
        return True, "OK"

    def calculate_position_size(self, balance: float, price: float) -> tuple:
        """Calculate safe position size"""
        # Risk 2% of balance
        risk_amount = balance * 0.02
        # Assuming stop loss is 2%, then position size = risk_amount / 0.02 = balance
        # But let's be conservative: 10% of balance per trade
        position_value = balance * 0.10
        
        # Apply GEC adjustments if ETAPA 2A active
        if self.settings.ETAPA_2A_ACTIVE:
            adjustments = self.get_gec_adjustments()
            position_value *= adjustments["order_size_multiplier"]
        
        amount = position_value / price
        return position_value, amount

    def record_trade(self, value: float, is_opening: bool):
        """Record trade for stats"""
        # Update position value
        if is_opening:
            self._total_position_value += value
        else:
            self._total_position_value = max(0, self._total_position_value - value)

    def get_daily_stats(self):
        """Get daily risk stats"""
        return {
            "trades": 0,
            "pnl": self._current_equity - self._daily_start_equity,
            "exposure": self.calculate_exposure_ratio(),
            "daily_drawdown": self.calculate_daily_drawdown(),
            "gec_state": self._gec_state,
            "freeze_active": self._freeze_active,
            "freeze_reason": self._freeze_reason,
            "kill_switch_active": self._kill_switch_active
        }

    def reset_circuit_breaker(self):
        """Reset circuit breaker (manual action required)"""
        logger.warning(f"⚠️ Manual circuit breaker reset requested")
        self._freeze_active = False
        self._freeze_reason = None
        self.save_state()
        # Note: Kill-Switch cannot be reset via this method (requires restart)
