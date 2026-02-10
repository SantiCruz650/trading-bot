import json
import os
from datetime import datetime

class MLEvaluator:
    def __init__(self, log_path="/home/santiagomiguelcruz/trading-bot/data/ml_evaluation_extended.json"):
        self.log_path = log_path
        self._init_log()

    def _init_log(self):
        if not os.path.exists(os.path.dirname(self.log_path)):
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w") as f:
                json.dump({"sessions": []}, f)

    def log_event(self, ticker, price, ml_signal, original_signal, regime, action_taken, drawdown=0, dca_levels=0):
        """
        Log a trading event for later A/B analysis.
        action_taken: 'EXECUTED', 'BLOCKED_BY_ML', 'SKIPPED_BY_ALGO'
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
        
        with open(self.log_path, "r+") as f:
            data = json.load(f)
            data["sessions"].append(event)
            f.seek(0)
            json.dump(data, f, indent=4)

    def calculate_metrics(self):
        """
        Calculate advanced metrics from logged events.
        """
        if not os.path.exists(self.log_path):
            return {}
            
        with open(self.log_path, "r") as f:
            data = json.load(f)
            events = data["sessions"]

        if not events:
            return {}

        # 1. Avoided Drawdown (AD)
        # Logic: For each BLOCKED_BY_ML event, check the price 24h later.
        # If price_later < price_entry, it was a "Correct Block".
        # AD = Sum of (price_entry - price_later) for correct blocks.
        
        # 2. ML Alpha
        # Comparison of ROI of EXECUTED vs ROI of BLOCKED (theoretical).
        
        # 3. False Positive Cost (FPC)
        # ROI of EXECUTED events that were negative.

        metrics = {
            "total_events": len(events),
            "blocked_by_ml": len([e for e in events if e["action_taken"] == "BLOCKED_BY_ML"]),
            "executed": len([e for e in events if e["action_taken"] == "EXECUTED"]),
            "regime_distribution": {}
        }
        
        for e in events:
            regime = e.get("regime", "UNKNOWN")
            metrics["regime_distribution"][regime] = metrics["regime_distribution"].get(regime, 0) + 1
            
        return metrics
