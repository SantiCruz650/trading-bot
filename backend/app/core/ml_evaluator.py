import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MLEvaluator:
    """
    Evaluates ML model performance by logging and tracking signal accuracy.
    """
    def __init__(self):
        self.history = []

    def log_event(self, ticker, price, ml_signal, original_signal, regime, action_taken, drawdown, dca_levels):
        """
        Logs a trading/prediction event for later evaluation.
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "price": price,
            "ml_signal": ml_signal,
            "original_signal": original_signal,
            "regime": regime,
            "action_taken": action_taken,
            "drawdown": drawdown,
            "dca_levels": dca_levels
        }
        self.history.append(event)
        logger.info(f"📊 ML Eval Event: {ticker} | Signal: {ml_signal} | Action: {action_taken} | Price: {price}")
        return True

    def get_summary(self):
        """
        Returns a summary of tracked performance.
        """
        return {
            "total_events": len(self.history),
            "last_event": self.history[-1] if self.history else None
        }
