from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import requests
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(
    title="MCrypto - Signal Prediction Service"
)

# Global cache for models and data
MODELS_CACHE = {}
FEAR_GREED_CACHE = {"data": None, "timestamp": None}
MODELS_DIR = Path("/home/santiagomiguelcruz/trading-bot/ml_service/models")
MODELS_DIR.mkdir(exist_ok=True)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
LOOK_BACK_DAYS = 30
CRYPTO_TICKERS = {"ETH", "BTC", "ADA", "SOL", "DOGE"}
SIGNAL_FUTURE_DAYS = 3
SIGNAL_THRESHOLD = 0.015 # 1.5%

# --- Helper Functions ---
def calculate_rsi(df, window=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_histogram = macd_line - signal_line
    return pd.DataFrame({'macd': macd_line, 'signal': signal_line, 'histogram': macd_histogram})

def get_fear_and_greed_data():
    """Fetch Fear & Greed data with caching (cache for 1 hour)"""
    global FEAR_GREED_CACHE
    
    # Check if cache is valid (less than 1 hour old)
    if FEAR_GREED_CACHE["data"] is not None and FEAR_GREED_CACHE["timestamp"] is not None:
        if datetime.now() - FEAR_GREED_CACHE["timestamp"] < timedelta(hours=1):
            print("Using cached Fear & Greed data")
            return FEAR_GREED_CACHE["data"]
    
    try:
        print("Fetching fresh Fear & Greed data...")
        url = "https://api.alternative.me/fng/?limit=0"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='s')
        df.set_index('timestamp', inplace=True)
        df['value'] = pd.to_numeric(df['value'])
        
        # Update cache
        FEAR_GREED_CACHE["data"] = df['value']
        FEAR_GREED_CACHE["timestamp"] = datetime.now()
        
        return df['value']
    except Exception as e:
        print(f"Error fetching Fear & Greed data: {e}")
        return pd.Series()

def get_data(ticker: str):
    if not API_KEY:
        return None, {"error": "ALPHA_VANTAGE_API_KEY is not configured."}
    try:
        if ticker.upper() in CRYPTO_TICKERS:
            market = "USD"
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={ticker}&market={market}&apikey={API_KEY}"
            ts_key = "Time Series (Digital Currency Daily)"
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={API_KEY}"
            ts_key = "Time Series (Daily)"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data or ts_key not in data:
            return None, {"error": f"Could not retrieve data for '{ticker}'."}

        ts = data[ts_key]
        df = pd.DataFrame.from_dict(ts, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df.sort_index(inplace=True)
        df.rename(columns={'4. close': 'close', '5. volume': 'volume'}, inplace=True)

        fng_data = get_fear_and_greed_data()
        if not fng_data.empty:
            df = pd.merge(df, fng_data, left_index=True, right_index=True, how='left')
            df['value'] = df['value'].ffill()
            df.rename(columns={'value': 'fear_greed'}, inplace=True)
        else:
            df['fear_greed'] = 50
        
        return df, None
    except Exception as e:
        return None, {"error": f"An unexpected error occurred: {str(e)}"}

def create_signal_labels(df):
    """Create training labels based on future price movement"""
    df['future_close'] = df['close'].shift(-SIGNAL_FUTURE_DAYS)
    df['price_change'] = (df['future_close'] - df['close']) / df['close']
    
    conditions = [
        (df['price_change'] > SIGNAL_THRESHOLD),
        (df['price_change'] < -SIGNAL_THRESHOLD)
    ]
    choices = ['BUY', 'SELL']
    df['signal'] = np.select(conditions, choices, default='HOLD')
    
    df.drop(['future_close', 'price_change'], axis=1, inplace=True)
    return df.dropna()

def engineer_features(df):
    """Add technical indicators and lagged features - REUSABLE FUNCTION"""
    feature_data = df.copy()
    
    # Lagged close prices
    for i in range(1, LOOK_BACK_DAYS + 1):
        feature_data[f'close_lag_{i}'] = feature_data['close'].shift(i)
    
    # Volume lag
    feature_data['volume_lag_1'] = feature_data['volume'].shift(1)
    
    # Moving average
    feature_data['ma_5'] = feature_data['close'].rolling(window=5).mean().shift(1)
    
    # Fear & Greed lag
    feature_data['fear_greed_lag_1'] = feature_data['fear_greed'].shift(1)
    
    # RSI
    feature_data['rsi'] = calculate_rsi(feature_data)
    feature_data['rsi_lag_1'] = feature_data['rsi'].shift(1)
    
    # MACD
    macd_data = calculate_macd(feature_data)
    feature_data['macd'] = macd_data['macd']
    feature_data['macd_signal'] = macd_data['signal']
    feature_data['macd_histogram'] = macd_data['histogram']
    feature_data['macd_lag_1'] = feature_data['macd'].shift(1)
    
    feature_data.dropna(inplace=True)
    return feature_data

def get_feature_columns():
    """Return the list of feature column names"""
    feature_columns = [f'close_lag_{i}' for i in range(1, LOOK_BACK_DAYS + 1)]
    feature_columns.extend(['volume_lag_1', 'ma_5', 'fear_greed_lag_1', 'rsi_lag_1', 'macd_lag_1'])
    return feature_columns

def train_and_save_model(ticker: str):
    """Train a new model and save it to disk"""
    print(f"\n===== TRAINING NEW MODEL FOR {ticker} =====")
    df, error = get_data(ticker)
    if error:
        return None, error
    
    df = create_signal_labels(df)
    feature_data = engineer_features(df)
    
    if len(feature_data) < 100:
        return None, {"error": f"Not enough data to train model for {ticker}"}
    
    feature_columns = get_feature_columns()
    X = feature_data[feature_columns]
    y = feature_data['signal']
    
    print(f"Training on {len(X)} samples")
    print(f"Signal distribution: {y.value_counts().to_dict()}")
    
    model = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    # Save model
    model_path = MODELS_DIR / f"{ticker}_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model saved to {model_path}")
    MODELS_CACHE[ticker] = model
    
    return model, None

def load_or_train_model(ticker: str):
    """Load existing model or train a new one"""
    # Check cache first
    if ticker in MODELS_CACHE:
        print(f"Using cached model for {ticker}")
        return MODELS_CACHE[ticker], None
    
    # Try to load from disk
    model_path = MODELS_DIR / f"{ticker}_model.pkl"
    if model_path.exists():
        try:
            print(f"Loading model from {model_path}")
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            MODELS_CACHE[ticker] = model
            return model, None
        except Exception as e:
            print(f"Error loading model: {e}. Training new model...")
    
    # Train new model
    return train_and_save_model(ticker)

def run_full_backtest(ticker: str, days: int):
    """Run backtest using the reusable feature engineering function"""
    print(f"\n===== STARTING BACKTEST FOR {ticker} =====")
    df, error = get_data(ticker)
    if error:
        return error
    print(f"1. Raw data from API: {len(df)} rows")

    df = create_signal_labels(df)
    print(f"2. After creating signal labels: {len(df)} rows")
    
    test_data = df.tail(days + LOOK_BACK_DAYS).copy()
    print(f"3. After taking tail for backtest: {len(test_data)} rows")
    
    # Use the reusable feature engineering function
    test_data = engineer_features(test_data)
    print(f"4. After feature engineering: {len(test_data)} rows")

    if test_data.empty:
        return {"error": f"Not enough data to backtest '{ticker}' after feature engineering."}

    feature_columns = get_feature_columns()
    X = test_data[feature_columns]
    y = test_data['signal']

    split_index = int(len(X) * 0.9)
    X_array = X.values
    y_array = y.values
    X_train, X_test = X_array[:split_index], X_array[split_index:]
    y_train, y_test = y_array[:split_index], y_array[split_index:]
    y_test_series = y.iloc[split_index:]

    print(f"--- Signal Distribution for {ticker} ---")
    print(f"Test set size: {len(y_test)}")
    print(f"Test set signal counts:\n{y_test_series.value_counts()}")
    print("-----------------------------------------")

    if len(y_test) < 10:
        return {"error": f"Test set is too small ({len(y_test)} items) to evaluate."}

    print("--- Training RandomForest Model ---")
    model = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    last_prediction = predictions[-1]
    last_actual = y_test_series.iloc[-1]
    
    results = []
    for i in range(min(5, len(y_test))):
        results.append({
            "date": y_test_series.index[i].strftime('%Y-%m-%d'),
            "actual": y_test_series.iloc[i],
            "predicted": predictions[i]
        })

    return {
        "ticker": ticker,
        "backtest_days": days,
        "accuracy": round(accuracy, 4),
        "last_predicted_signal": last_prediction,
        "last_actual_signal": last_actual,
        "recent_predictions": results
    }

# --- API Endpoints ---
@app.get("/predict/{ticker}")
async def predict(ticker: str):
    """Get prediction using cached/persisted model"""
    # Load or train model
    model, error = load_or_train_model(ticker)
    if error:
        return error
    
    # Get fresh data for prediction
    df, error = get_data(ticker)
    if error:
        return error

    # Engineer features (no labels needed for prediction)
    feature_data = engineer_features(df)
    
    if feature_data.empty:
        return {"error": f"Not enough data to make prediction for {ticker}"}

    feature_columns = get_feature_columns()
    X = feature_data[feature_columns]

    # Make prediction using the last row of features
    last_features = X.iloc[[-1]]
    predicted_signal = model.predict(last_features)[0]
    last_close_price = df['close'].iloc[-1]

    return {
        "ticker": ticker,
        "last_close": round(last_close_price, 2),
        "signal": predicted_signal
    }

@app.post("/retrain/{ticker}")
async def retrain_model(ticker: str):
    """Force retrain the model for a ticker"""
    model, error = train_and_save_model(ticker)
    if error:
        return error
    return {"message": f"Model for {ticker} retrained successfully"}

@app.get("/backtest/{ticker}")
async def backtest(ticker: str, days: int = Query(500, ge=50, le=1000)):
    result = run_full_backtest(ticker, days)
    return result
