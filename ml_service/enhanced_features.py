import pandas as pd
import numpy as np

def create_enhanced_features(df, look_back_days=30):
    """Create enhanced features for better prediction accuracy"""
    # Original features
    for i in range(1, min(6, look_back_days)):
        df[f'close_lag_{i}'] = df['close'].shift(i)
    
    df['volume_lag_1'] = df['volume'].shift(1)
    df['ma_5'] = df['close'].rolling(window=5).mean()
    df['fear_greed_lag_1'] = df['fear_greed_index'].shift(1)
    df['rsi_lag_1'] = df['rsi'].shift(1)
    df['macd_lag_1'] = df['macd'].shift(1)
    
    # Enhanced features
    # Price momentum
    df['price_change_1d'] = df['close'].pct_change(1)
    df['price_change_3d'] = df['close'].pct_change(3)
    df['price_change_7d'] = df['close'].pct_change(7)
    
    # Volatility
    df['volatility_5d'] = df['close'].rolling(window=5).std()
    df['volatility_10d'] = df['close'].rolling(window=10).std()
    
    # Moving averages
    df['ma_10'] = df['close'].rolling(window=10).mean()
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['ma_50'] = df['close'].rolling(window=50).mean()
    
    # Moving average crossovers
    df['ma_5_10_cross'] = (df['ma_5'] > df['ma_10']).astype(int)
    df['ma_10_20_cross'] = (df['ma_10'] > df['ma_20']).astype(int)
    
    # Bollinger Bands
    df['bb_upper'] = df['ma_20'] + 2 * df['close'].rolling(window=20).std()
    df['bb_lower'] = df['ma_20'] - 2 * df['close'].rolling(window=20).std()
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # RSI enhancements
    df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
    df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
    
    # Volume indicators
    df['volume_ma_5'] = df['volume'].rolling(window=5).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma_5']
    
    # Fear & Greed enhancements
    df['fear_greed_ma_5'] = df['fear_greed_index'].rolling(window=5).mean()
    df['fear_greed_change'] = df['fear_greed_index'].pct_change(1)
    
    # MACD enhancements
    df['macd_signal'] = df['macd'].rolling(window=9).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    # ATR (Average True Range) for Volatility Regime
    high_low = df['close'].rolling(window=2).max() - df['close'].rolling(window=2).min() # Simplified for daily
    df['atr_14'] = high_low.rolling(window=14).mean()
    
    # ADX (Average Directional Index) for Trend Strength
    # Simplified ADX implementation
    plus_dm = df['close'].diff().clip(lower=0)
    minus_dm = (-df['close'].diff()).clip(lower=0)
    tr = df['close'].rolling(window=14).max() - df['close'].rolling(window=14).min()
    
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / tr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    df['adx_14'] = dx.rolling(window=14).mean()

    # Day of week effect
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    df['is_monday'] = (df['day_of_week'] == 0).astype(int)
    df['is_friday'] = (df['day_of_week'] == 4).astype(int)
    
    return df
