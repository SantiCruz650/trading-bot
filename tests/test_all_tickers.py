import requests
import json
import sys

BASE_URL_ML = "http://localhost:8001"
TICKERS = ["BTC", "ETH", "ADA", "SOL", "DOGE"]

def get_prediction(ticker):
    try:
        response = requests.get(f"{BASE_URL_ML}/predict/{ticker}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}", "details": response.text}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🚀 Running Predictions for ALL Tickers...\n")
    
    results = {}
    
    for ticker in TICKERS:
        print(f"Analyzing {ticker}...", end="", flush=True)
        data = get_prediction(ticker)
        results[ticker] = data
        
        if "error" in data:
            print(f" ❌ ERROR: {data['error']}")
        else:
            signal = data.get('signal', 'UNKNOWN')
            conf = data.get('confidence', 'UNKNOWN')
            price = data.get('last_close', 0)
            print(f" ✅ {signal} ({conf}) @ ${price}")

    print("\n--- Detailed Results ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
