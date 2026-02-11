import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskGovernor:
    def __init__(self, config=None):
        self.config = config or {}
        self.global_dd_limit = self.config.get("global_dd_limit", 0.15)
        self.emergency_freeze_limit = self.config.get("emergency_freeze_limit", 0.20)
        self.system_state = "NORMAL"

    def evaluate_global_risk(self, total_equity, portfolio_ath):
        """
        Coordinador global de riesgo.
        """
        if portfolio_ath <= 0: return "NORMAL"
        
        current_dd = (portfolio_ath - total_equity) / portfolio_ath
        
        if current_dd >= self.emergency_freeze_limit:
            self.system_state = "EMERGENCY_FREEZE"
            logger.critical(f"🛑 EMERGENCY FREEZE: Global DD {current_dd*100:.2f}% exceeds {self.emergency_freeze_limit*100:.2f}%")
        elif current_dd >= self.global_dd_limit:
            self.system_state = "PROTECTIVE_MODE"
            logger.warning(f"⚠️ PROTECTIVE MODE: Global DD {current_dd*100:.2f}% exceeds {self.global_dd_limit*100:.2f}%")
        else:
            self.system_state = "NORMAL"
            
        return self.system_state

    def can_execute_intent(self, intent_type, symbol_metrics):
        """
        Check if an execution intent (BUY/SELL) is allowed by global state.
        """
        if self.system_state == "EMERGENCY_FREEZE":
            return False, "Global Emergency Freeze active"
        
        if self.system_state == "PROTECTIVE_MODE" and intent_type == "BUY":
            if symbol_metrics.get("shs", 0) < 70:
                return False, "Protective Mode: Only high SHS (>70) buys allowed"
                
        return True, "Approved"
