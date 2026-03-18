import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class StrategyStateStore:
    """
    Singleton store for high-frequency, non-critical strategy state 
    to reduce database egress (e.g., price_history, pending_ml_evaluations).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StrategyStateStore, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        # Structure: {strategy_id: {"price_history": [], "pending_evals": []}}
        self._states: Dict[int, Dict[str, Any]] = {}
        self.initialized = True
        logger.info("🧠 StrategyStateStore (In-Memory) initialized")

    def get_state(self, strategy_id: int) -> Dict[str, Any]:
        """Retrieve state for a strategy, initializing if not exists."""
        if strategy_id not in self._states:
            self._states[strategy_id] = {
                "price_history": [],
                "pending_ml_evaluations": []
            }
        return self._states[strategy_id]

    def update_price_history(self, strategy_id: int, price: float):
        """Add price to history and maintain max 200 points."""
        state = self.get_state(strategy_id)
        history = state["price_history"]
        
        # Maintain ~50 mins at 15s (or ~100 mins at 30s)
        history = history[-199:]
        history.append({
            "ts": datetime.utcnow().isoformat(),
            "price": price
        })
        state["price_history"] = history

    def add_ml_evaluation(self, strategy_id: int, evaluation: Dict[str, Any]):
        """Store pending ML evaluation."""
        state = self.get_state(strategy_id)
        state["pending_ml_evaluations"].append(evaluation)

    def set_ml_evaluations(self, strategy_id: int, evaluations: List[Dict[str, Any]]):
        """Overwrite pending ML evaluations."""
        state = self.get_state(strategy_id)
        state["pending_ml_evaluations"] = evaluations

# Global singleton
state_store = StrategyStateStore()
