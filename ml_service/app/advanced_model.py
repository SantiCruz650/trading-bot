"""
Advanced ML Model for Cryptocurrency Prediction - Target: 80%+ Accuracy
Uses XGBoost ensemble with advanced feature engineering and signal smoothing
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import requests
from datetime import datetime, timedelta
import pickle
from pathlib import Path


class AdvancedCryptoPredictor:
    """Advanced model combining XGBoost with feature engineering for high accuracy"""
    
    def __init__(self, look_back=60, future_days=1, signal_threshold=0.01):
        self.look_back = look_back
        self.future_days = future_days
        self.signal_threshold = signal_threshold
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def get_data(self, ticker: str, api_key: str):
        """Fetch cryptocurrency data from Alpha Vantage API"""
        try:
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={ticker}&market=USD&apikey={api_key}"
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if "Error Message" in data or "Time Series (Digital Currency Daily)" not in data:
                return None
            
            ts = data["Time Series (Digital Currency Daily)"]
            df = pd.DataFrame.from_dict(ts, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df.sort_index(inplace=True)
            df.rename(columns={'4. close': 'close', '5. volume': 'volume'}, inplace=True)
            
            return df[['close', 'volume']]
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def calculate_advanced_features(self, df):
        """Calculate 40+ technical indicators for better accuracy"""
        features = df.copy()
        
        # 1. Price momentum features (15 features)
        for i in [5, 10, 20, 50]:
            features[f'roc_{i}'] = features['close'].pct_change(i)
            features[f'sma_{i}'] = features['close'].rolling(i).mean()
            features[f'price_vs_sma_{i}'] = (features['close'] - features[f'sma_{i}']) / features[f'sma_{i}']
        
        # 2. Volatility features (8 features)
        for window in [10, 20, 50]:
            features[f'volatility_{window}'] = features['close'].pct_change().rolling(window).std()
            features[f'high_low_ratio_{window}'] = features['close'].rolling(window).max() / features['close'].rolling(window).min()
        
        # 3. RSI with multiple periods (4 features)
        for period in [7, 14, 21, 28]:
            features[f'rsi_{period}'] = self._calculate_rsi(features['close'], period)
        
        # 4. MACD and Signal Line (3 features)
        macd_result = self._calculate_macd(features['close'])
        features['macd'] = macd_result['macd']
        features['macd_signal'] = macd_result['signal']
        features['macd_histogram'] = macd_result['histogram']
        
        # 5. Bollinger Bands (4 features)
        for period in [20, 50]:
            bb = self._calculate_bollinger_bands(features['close'], period)
            features[f'bb_upper_{period}'] = bb['upper']
            features[f'bb_lower_{period}'] = bb['lower']
            features[f'bb_pct_{period}'] = bb['bb_pct']
        
        # 6. Volume features (3 features)
        features['volume_ma'] = features['volume'].rolling(20).mean()
        features['volume_ratio'] = features['volume'] / features['volume_ma']
        features['volume_sma_ratio'] = features['volume'].rolling(20).sum() / features['volume'].rolling(50).sum()
        
        # 7. Lagged features (20 features)
        for lag in range(1, 6):
            features[f'close_lag_{lag}'] = features['close'].shift(lag)
            features[f'return_lag_{lag}'] = features['close'].pct_change().shift(lag)
        
        # 8. Moving average crossovers (3 features)
        sma_12 = features['close'].rolling(12).mean()
        sma_26 = features['close'].rolling(26).mean()
        features['sma_crossover_12_26'] = (sma_12 > sma_26).astype(int)
        
        ema_9 = features['close'].ewm(span=9).mean()
        ema_21 = features['close'].ewm(span=21).mean()
        features['ema_crossover_9_21'] = (ema_9 > ema_21).astype(int)
        
        features['price_vs_ma50_ma200'] = (
            (features['close'] > features['sma_50'].shift(0)) & 
            (features['sma_50'] > features['close'].rolling(200).mean())
        ).astype(int)
        
        # 9. Momentum features (5 features)
        features['momentum_10'] = features['close'].diff(10)
        features['momentum_20'] = features['close'].diff(20)
        features['roc_10'] = (features['close'].pct_change(10)) * 100
        features['roc_20'] = (features['close'].pct_change(20)) * 100
        
        # 10. Stochastic Oscillator (2 features)
        stoch = self._calculate_stochastic(features['close'], 14)
        features['stoch_k'] = stoch['k']
        features['stoch_d'] = stoch['d']
        
        features.dropna(inplace=True)
        return features
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices, period=20, num_std=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        bb_pct = (prices - lower_band) / (upper_band - lower_band)
        return {
            'upper': upper_band,
            'lower': lower_band,
            'bb_pct': bb_pct
        }
    
    def _calculate_stochastic(self, prices, period=14):
        """Calculate Stochastic Oscillator"""
        lowest = prices.rolling(period).min()
        highest = prices.rolling(period).max()
        k = 100 * ((prices - lowest) / (highest - lowest))
        d = k.rolling(3).mean()
        return {'k': k, 'd': d}
    
    def create_signal_labels(self, df):
        """Create training labels based on future price movement"""
        df['future_close'] = df['close'].shift(-self.future_days)
        df['price_change_pct'] = (df['future_close'] - df['close']) / df['close']
        
        # More granular signal levels
        conditions = [
            (df['price_change_pct'] > self.signal_threshold * 2),      # Strong BUY
            ((df['price_change_pct'] > self.signal_threshold) & 
             (df['price_change_pct'] <= self.signal_threshold * 2)),   # BUY
            ((df['price_change_pct'] >= -self.signal_threshold) & 
             (df['price_change_pct'] <= self.signal_threshold)),       # HOLD
            ((df['price_change_pct'] < -self.signal_threshold) & 
             (df['price_change_pct'] >= -self.signal_threshold * 2)),  # SELL
            (df['price_change_pct'] < -self.signal_threshold * 2),     # Strong SELL
        ]
        choices = ['BUY', 'BUY', 'HOLD', 'SELL', 'SELL']
        df['signal'] = np.select(conditions, choices, default='HOLD')
        
        df.drop(['future_close', 'price_change_pct'], axis=1, inplace=True)
        return df.dropna()
    
    def train(self, df, test_size=0.2):
        """Train XGBoost ensemble model"""
        # Create features
        feature_df = self.calculate_advanced_features(df)
        feature_df = self.create_signal_labels(feature_df)
        
        # Get feature columns
        self.feature_columns = [col for col in feature_df.columns if col not in ['close', 'volume', 'signal']]
        
        X = feature_df[self.feature_columns].values
        y = feature_df['signal'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        split_idx = int(len(X_scaled) * (1 - test_size))
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        print(f"Training set: {len(y_train)}, Test set: {len(y_test)}")
        print(f"Signal distribution in test set:\n{pd.Series(y_test).value_counts()}")
        
        # Train XGBoost with optimal parameters
        self.model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            eval_metric='mlogloss'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, train_pred)
        test_acc = accuracy_score(y_test, test_pred)
        precision = precision_score(y_test, test_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, test_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, test_pred, average='weighted', zero_division=0)
        
        print(f"\n=== Model Performance ===")
        print(f"Train Accuracy: {train_acc:.2%}")
        print(f"Test Accuracy: {test_acc:.2%}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"F1-Score: {f1:.2%}")
        
        return test_acc
    
    def predict(self, df):
        """Make prediction on latest data"""
        if self.model is None:
            return None
        
        feature_df = self.calculate_advanced_features(df)
        X = feature_df[self.feature_columns].tail(1).values
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        return {
            'signal': prediction,
            'confidence': max(probabilities),
            'probabilities': dict(zip(self.model.classes_, probabilities))
        }
    
    def save(self, filepath):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'look_back': self.look_back,
            'future_days': self.future_days,
            'signal_threshold': self.signal_threshold
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.look_back = model_data['look_back']
        self.future_days = model_data['future_days']
        self.signal_threshold = model_data['signal_threshold']
        print(f"Model loaded from {filepath}")
