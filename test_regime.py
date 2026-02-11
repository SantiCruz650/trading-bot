import pandas as pd
import numpy as np
from ml_service.enhanced_features import create_enhanced_features
from ml_service.regime_detector import MarketRegimeDetector

def test_regime_detection():
    # Create dummy data
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
    
    # 1. RANGE Scenario (Low volatility, no trend)
    df_range = pd.DataFrame({
        'date': dates,
        'close': [1000 + np.sin(i/5)*10 for i in range(100)],
        'volume': [100] * 100,
        'fear_greed_index': [50] * 100,
        'rsi': [50] * 100,
        'macd': [0] * 100
    })
    df_range = create_enhanced_features(df_range)
    
    detector = MarketRegimeDetector()
    regime_range = detector.detect_regime(df_range)
    print(f"Scenario RANGE: {regime_range}")
    
    # 2. CRISIS Scenario (Fast drop, high volatility)
    prices_crisis = [1000] * 90 + [950, 900, 850, 800, 750, 700, 650, 600, 550, 500]
    df_crisis = pd.DataFrame({
        'date': dates,
        'close': prices_crisis,
        'volume': [100] * 100,
        'fear_greed_index': [50] * 100,
        'rsi': [50] * 100,
        'macd': [0] * 100
    })
    df_crisis = create_enhanced_features(df_crisis)
    regime_crisis = detector.detect_regime(df_crisis)
    print(f"Scenario CRISIS: {regime_crisis}")
    
    # 3. TENDENCY Scenario (Strong trend)
    prices_trend = [1000 + i*10 for i in range(100)]
    df_trend = pd.DataFrame({
        'date': dates,
        'close': prices_trend,
        'volume': [100] * 100,
        'fear_greed_index': [50] * 100,
        'rsi': [50] * 100,
        'macd': [0] * 100
    })
    df_trend = create_enhanced_features(df_trend)
    regime_trend = detector.detect_regime(df_trend)
    print(f"Scenario TENDENCY: {regime_trend}")

if __name__ == "__main__":
    test_regime_detection()
