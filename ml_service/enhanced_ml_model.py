"""
Enhanced ML Model with 80%+ accuracy targeting features:
- Advanced technical indicators (Bollinger Bands, ATR, Stochastic)
- Multiple timeframe analysis
- Volatility-based features
- Momentum indicators
- Ensemble methods (Random Forest + Gradient Boosting)
"""

import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pickle
from pathlib import Path

class EnhancedMLModel:
    def __init__(self, look_back_days: int = 60, future_days: int = 3, threshold: float = 0.02):
        self.look_back_days = look_back_days
        self.future_days = future_days
        self.threshold = threshold
        self.scaler = StandardScaler()
        self.model = None
        
    def fetch_data(self, ticker: str, days: int = 500) -> pd.DataFrame:
        """Fetch cryptocurrency data from Alpha Vantage"""
        try:
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
            market = "USD"
            
            if ticker.upper() in {"BTC", "ETH", "ADA", "SOL", "DOGE"}:
                url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={ticker}&market={market}&apikey={api_key}"
                ts_key = "Time Series (Digital Currency Daily)"
            else:
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={api_key}"
                ts_key = "Time Series (Daily)"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data or ts_key not in data:
                return None
            
            ts = data[ts_key]
            df = pd.DataFrame.from_dict(ts, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.sort_index(inplace=True)
            df.rename(columns={'4. close': 'close', '5. volume': 'volume'}, inplace=True)
            
            return df.tail(days).copy()
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df['bb_middle'] = df['close'].rolling(window=window).mean()
        std = df['close'].rolling(window=window).std()
        df['bb_upper'] = df['bb_middle'] + (std * num_std)
        df['bb_lower'] = df['bb_middle'] - (std * num_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        return df
    
    def calculate_atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        df['tr1'] = df['close'].shift(1) - df['close']
        df['tr2'] = abs(df['close'].shift(1) - df['volume'])
        df['tr'] = df[['tr1', 'tr2']].max(axis=1)
        atr = df['tr'].rolling(window=window).mean()
        return atr
    
    def calculate_stochastic(self, df: pd.DataFrame, window: int = 14, smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        low_min = df['close'].rolling(window=window).min()
        high_max = df['close'].rolling(window=window).max()
        k_percent = 100 * (df['close'] - low_min) / (high_max - low_min)
        d_percent = k_percent.rolling(window=smooth).mean()
        return k_percent, d_percent
    
    def calculate_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}
    
    def calculate_adx(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        high_diff = df['close'].diff()
        low_diff = -df['close'].shift(1).diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        tr = df['close'].rolling(window=window).max() - df['close'].rolling(window=window).min()
        
        plus_di = 100 * pd.Series(plus_dm).rolling(window=window).mean() / tr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=window).mean() / tr
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=window).mean()
        return adx
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer comprehensive feature set"""
        feature_df = df.copy()
        
        # Price-based features
        feature_df['price_change_pct'] = feature_df['close'].pct_change()
        feature_df['log_return'] = np.log(feature_df['close'] / feature_df['close'].shift(1))
        feature_df['volatility'] = feature_df['log_return'].rolling(window=20).std()
        
        # Volume features
        feature_df['volume_change'] = feature_df['volume'].pct_change()
        feature_df['volume_ma_ratio'] = feature_df['volume'] / feature_df['volume'].rolling(window=20).mean()
        
        # Moving averages (multiple timeframes)
        for window in [5, 10, 20, 50]:
            feature_df[f'ma_{window}'] = feature_df['close'].rolling(window=window).mean()
            feature_df[f'price_to_ma_{window}'] = feature_df['close'] / feature_df[f'ma_{window}']
        
        # Momentum indicators
        feature_df['rsi_14'] = self.calculate_rsi(feature_df, window=14)
        feature_df['rsi_30'] = self.calculate_rsi(feature_df, window=30)
        
        # MACD
        macd_dict = self.calculate_macd(feature_df)
        feature_df['macd'] = macd_dict['macd']
        feature_df['macd_signal'] = macd_dict['signal']
        feature_df['macd_histogram'] = macd_dict['histogram']
        
        # Bollinger Bands
        feature_df = self.calculate_bollinger_bands(feature_df, window=20)
        
        # Stochastic
        k_percent, d_percent = self.calculate_stochastic(feature_df, window=14)
        feature_df['stoch_k'] = k_percent
        feature_df['stoch_d'] = d_percent
        
        # ATR
        feature_df['atr'] = self.calculate_atr(feature_df, window=14)
        feature_df['atr_ratio'] = feature_df['atr'] / feature_df['close']
        
        # ADX
        feature_df['adx'] = self.calculate_adx(feature_df, window=14)
        
        # Rate of Change (ROC)
        for window in [5, 10, 20]:
            feature_df[f'roc_{window}'] = feature_df['close'].pct_change(periods=window)
        
        # Williams %R
        window = 14
        high_14 = feature_df['close'].rolling(window=window).max()
        low_14 = feature_df['close'].rolling(window=window).min()
        feature_df['williams_r'] = -100 * (high_14 - feature_df['close']) / (high_14 - low_14)
        
        # Lagged features (for temporal context)
        for lag in [1, 2, 3, 5]:
            feature_df[f'close_lag_{lag}'] = feature_df['close'].shift(lag)
            feature_df[f'rsi_lag_{lag}'] = feature_df['rsi_14'].shift(lag)
        
        return feature_df.dropna()
    
    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create trading signals based on future price movement"""
        df['future_close'] = df['close'].shift(-self.future_days)
        df['price_change'] = (df['future_close'] - df['close']) / df['close']
        
        # More nuanced signal generation
        conditions = [
            (df['price_change'] > self.threshold),
            (df['price_change'] < -self.threshold),
        ]
        choices = ['BUY', 'SELL']
        df['signal'] = np.select(conditions, choices, default='HOLD')
        
        df.drop(['future_close', 'price_change'], axis=1, inplace=True)
        return df
    
    def get_feature_columns(self) -> list:
        """Return list of feature columns"""
        features = [
            'price_change_pct', 'log_return', 'volatility',
            'volume_change', 'volume_ma_ratio',
            'ma_5', 'ma_10', 'ma_20', 'ma_50',
            'price_to_ma_5', 'price_to_ma_10', 'price_to_ma_20', 'price_to_ma_50',
            'rsi_14', 'rsi_30',
            'macd', 'macd_signal', 'macd_histogram',
            'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position',
            'stoch_k', 'stoch_d',
            'atr', 'atr_ratio',
            'adx',
            'roc_5', 'roc_10', 'roc_20',
            'williams_r',
            'close_lag_1', 'close_lag_2', 'close_lag_3', 'close_lag_5',
            'rsi_lag_1', 'rsi_lag_2', 'rsi_lag_3', 'rsi_lag_5',
        ]
        return features
    
    def train(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """Train ensemble model on historical data"""
        # Create features and labels
        df_featured = self.engineer_features(df)
        df_labeled = self.create_labels(df_featured)
        
        feature_cols = self.get_feature_columns()
        X = df_labeled[feature_cols]
        y = df_labeled['signal']
        
        # Split data
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Build ensemble model
        rf_model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        gb_model = GradientBoostingClassifier(n_estimators=150, max_depth=7, learning_rate=0.1, random_state=42)
        
        # Train both models
        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)
        
        # Get predictions from both models
        rf_pred = rf_model.predict(X_test)
        gb_pred = gb_model.predict(X_test)
        
        # Ensemble: vote-based predictions
        from collections import Counter
        ensemble_pred = []
        for i in range(len(rf_pred)):
            votes = [rf_pred[i], gb_pred[i]]
            vote_count = Counter(votes)
            ensemble_pred.append(vote_count.most_common(1)[0][0])
        
        # Calculate accuracy
        accuracy = np.mean(np.array(ensemble_pred) == y_test.values)
        
        # Store for predictions
        self.model = {
            'rf': rf_model,
            'gb': gb_model,
            'feature_cols': feature_cols,
            'scaler': self.scaler
        }
        
        return accuracy, {
            'accuracy': accuracy,
            'test_size': len(X_test),
            'signal_distribution': dict(y_test.value_counts())
        }
    
    def predict(self, df: pd.DataFrame) -> str:
        """Make prediction on latest data"""
        if self.model is None:
            return "HOLD"
        
        df_featured = self.engineer_features(df)
        feature_cols = self.model['feature_cols']
        
        X = df_featured[feature_cols].tail(1)
        
        rf_pred = self.model['rf'].predict(X)[0]
        gb_pred = self.model['gb'].predict(X)[0]
        
        # Ensemble vote
        votes = [rf_pred, gb_pred]
        vote_count = Counter(votes)
        prediction = vote_count.most_common(1)[0][0]
        
        return prediction
    
    def save_model(self, filepath: str):
        """Save trained model"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
    
    def load_model(self, filepath: str):
        """Load trained model"""
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
