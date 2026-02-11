#!/usr/bin/env python3
import requests
import json
import subprocess
import sys

def get_latest_prediction(token):
    """Get the latest prediction from the backend"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8000/my-predictions", headers=headers)
    
    if response.status_code == 200:
        predictions = response.json()
        if predictions:
            return predictions[0]  # Return the latest prediction
    return None

def log_prediction(ticker, signal, price):
    """Log a prediction using the track_predictions.py script"""
    result = subprocess.run([
        "python3", "track_predictions.py", "log", ticker, signal, price, "Would follow"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_and_log_prediction.py [access_token]")
        sys.exit(1)
    
    token = sys.argv[1]
    prediction = get_latest_prediction(token)
    
    if prediction:
        ticker = prediction.get("ticker", "")
        signal = prediction.get("signal", "")
        price = prediction.get("last_close", 0)
        
        print(f"Latest prediction: {ticker} {signal} at ${price}")
        log_prediction(ticker, signal, price)
    else:
        print("No predictions found or error fetching predictions")
