import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ARDCAEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self.base_multiplier = self.config.get("base_multiplier", 1.0)
        self.max_multiplier = self.config.get("max_multiplier", 3.0)
        self.min_multiplier = self.config.get("min_multiplier", 0.1)

    def calculate_order_multiplier(self, volatility, trend, ml_confidence, current_drawdown):
        """
        Adaptive Risk DCA (AR-DCA) sizing logic.
        Multipliers based on 4 axes.
        """
        # 1. Volatility Axis (Inverse)
        vol_score = 1.0
        if volatility > 0.05: vol_score = 0.5
        elif volatility > 0.02: vol_score = 0.8
        elif volatility < 0.005: vol_score = 1.5

        # 2. Trend Axis
        trend_score = 1.0
        if trend == "TREND_UP": trend_score = 1.2
        elif trend == "TREND_DOWN": trend_score = 0.6
        elif trend == "HIGH_VOLATILITY": trend_score = 0.3

        # 3. ML Confidence Axis
        ml_score = 1.0
        if ml_confidence > 0.8: ml_score = 1.5
        elif ml_confidence > 0.65: ml_score = 1.2
        elif ml_confidence < 0.45: ml_score = 0.5

        # 4. Drawdown Axis (Defensive)
        dd_score = 1.0
        if current_drawdown > 0.15: dd_score = 0.2
        elif current_drawdown > 0.08: dd_score = 0.5
        elif current_drawdown > 0.04: dd_score = 0.8

        final_multiplier = self.base_multiplier * vol_score * trend_score * ml_score * dd_score
        
        # Constraints
        final_multiplier = max(self.min_multiplier, min(self.max_multiplier, final_multiplier))
        
        logger.info(f"AR-DCA Multiplier: {final_multiplier:.2f} (V:{vol_score} T:{trend_score} ML:{ml_score} DD:{dd_score})")
        return final_multiplier
