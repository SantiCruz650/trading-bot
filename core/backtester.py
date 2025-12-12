import pandas as pd
import numpy as np
import os
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# --- Configuration ---
TICKER = 'NVDA'
LOOK_BACK_DAYS = 60
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def get_historical_data(ticker):
    print(f"Fetching data for {ticker}...")
    if not API_KEY:
        print("Error: ALPHA_VANTAGE_API_KEY not found.")
        return pd.DataFrame()
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data or "Time Series (Daily)" not in data:
            print("Error: Could not retrieve data from API.")
            return pd.DataFrame()
        ts = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts, orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        df.sort_index(inplace=True)
        df.rename(columns={'4. close': 'close', '5. volume': 'volume'}, inplace=True)
        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

def run_backtest():
    print("--- Starting Backtest ---")
    all_data = get_historical_data(TICKER)

    if all_data.empty:
        print("--- Backtest Failed: No data ---")
        return

    # Use the last 100 days for a quick test
    test_data = all_data.tail(100).copy()
    print(f"Successfully loaded {len(test_data)} days of data.")

    # --- Feature Engineering ---
    # Create a feature for the 'LOOK_BACK_DAYS' previous closing prices
    for i in range(1, LOOK_BACK_DAYS + 1):
        test_data[f'close_lag_{i}'] = test_data['close'].shift(i)
    
    # Add the 'volume' for the day we are predicting
    test_data['volume_lag_1'] = test_data['volume'].shift(1)

    # --- NEW FEATURE: 5-day Moving Average ---
    # We shift it by 1 so we use yesterday's trend to predict today's price
    test_data['ma_5'] = test_data['close'].rolling(window=5).mean().shift(1)

    # Drop rows with NaN values created by shifting/rolling
    test_data.dropna(inplace=True)

    # --- Prepare Data for Model ---
    feature_columns = [f'close_lag_{i}' for i in range(1, LOOK_BACK_DAYS + 1)]
    feature_columns.append('volume_lag_1')
    feature_columns.append('ma_5') # <-- Add the new feature to the list
    
    X = test_data[feature_columns]
    y = test_data['close']

    # Split data (e.g., 80% train, 20% test)
    split_index = int(len(X) * 0.8)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    print(f"--- DEBUG: Splitting data ---")
    print(f"Training on {len(X_train)} days, testing on {len(X_test)} days.")
    print(f"Using {len(feature_columns)} features.")

    # --- Model Training ---
    print("--- Training RandomForest Model ---")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # --- Prediction & Evaluation ---
    print("--- Making Predictions ---")
    predictions = model.predict(X_test)
    
    mse = mean_squared_error(y_test, predictions)
    print(f"--- Backtest Finished ---")
    print(f"Mean Squared Error on test data: {mse:.4f}")
    
    # Show the last prediction vs actual
    last_prediction = predictions[-1]
    last_actual = y_test.iloc[-1]
    print(f"Last Predicted Price: {last_prediction:.2f}")
    print(f"Last Actual Price: {last_actual:.2f}")


if __name__ == "__main__":
    run_backtest()
