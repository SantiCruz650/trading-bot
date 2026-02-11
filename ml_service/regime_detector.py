import pandas as pd
import numpy as np

class MarketRegimeDetector:
    def __init__(self, atr_window=14, adx_window=14):
        self.atr_window = atr_window
        self.adx_window = adx_window
        
    def detect_regime(self, df: pd.DataFrame) -> str:
        """
        Classify market regime based on Volatility and Trend Strength.
        Regimes: 'RANGE', 'TENDENCY', 'CRISIS'
        """
        if len(df) < max(self.atr_window, self.adx_window) + 1:
            return "RANGE" # Default to safe regime if not enough data
            
        latest = df.iloc[-1]
        
        # Calculate percentiles for ATR (Volatility)
        # In a real system, these would be calculated over a longer history
        atr_history = df['atr_14'].dropna()
        if len(atr_history) < 20:
            atr_percentile = 50 # Neutral
        else:
            atr_percentile = (atr_history < latest['atr_14']).mean() * 100
            
        adx = latest['adx_14']
        price_change_1d = latest.get('price_change_1d', 0)
        
        # 1. CRISIS (Fast Drop)
        # High volatility + Negative price change
        if atr_percentile > 90 and price_change_1d < -0.02:
            return "CRISIS"
            
        # 2. TENDENCY (Expansion)
        # Strong ADX + Moderate/High Volatility
        if adx > 25 and atr_percentile > 40:
            return "TENDENCY"
            
        # 3. RANGE (Chop)
        # Low Volatility or Weak ADX
        return "RANGE"

    def get_strictness_params(self, regime: str) -> dict:
        """Return strictness parameters based on regime"""
        if regime == "CRISIS":
            return {"allow_trading": False, "threshold": 1.0, "label": "ABSOLUTE"}
        elif regime == "TENDENCY":
            return {"allow_trading": True, "threshold": 0.70, "label": "STRICT"}
        else: # RANGE
            return {"allow_trading": True, "threshold": 0.45, "label": "PERMISSIVE"}
