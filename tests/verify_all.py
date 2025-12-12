import requests
import time
import json

BASE_URL = "http://localhost:8000/api"
TICKERS = ["BTC", "ETH", "ADA", "SOL", "DOGE"]

def verify_system():
    print("=== Starting System Verification ===")
    
    # 1. Authenticate
    print("\n1. Authenticating...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={"username": "demo_user", "password": "password123"})
        if resp.status_code != 200:
            print(f"❌ Authentication failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authenticated")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # 2. Verify Predictions for all tickers
    print("\n2. Verifying Predictions...")
    for ticker in TICKERS:
        print(f"  Testing {ticker}...", end=" ", flush=True)
        try:
            start = time.time()
            resp = requests.post(f"{BASE_URL}/predictions/predict/{ticker}", headers=headers)
            duration = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Success ({duration:.2f}s) - Signal: {data['signal']}, Price: {data['last_close']}")
            else:
                print(f"❌ Failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # 3. Verify Backtesting Trigger
    print("\n3. Verifying Backtest Triggers...")
    for ticker in TICKERS:
        print(f"  Triggering backtest for {ticker}...", end=" ", flush=True)
        try:
            resp = requests.post(f"{BASE_URL}/predictions/trigger-backtest/{ticker}", headers=headers)
            if resp.status_code == 200:
                print(f"✅ Started (Task ID: {resp.json()['task_id']})")
            else:
                print(f"❌ Failed: {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # 4. Verify Market Data (Chart)
    print("\n4. Verifying Market Data (Chart)...")
    for ticker in TICKERS:
        print(f"  Fetching history for {ticker}...", end=" ", flush=True)
        try:
            resp = requests.get(f"{BASE_URL}/predictions/market-data/{ticker}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Success ({len(data)} candles)")
                else:
                    print(f"⚠️ Empty data returned")
            else:
                print(f"❌ Failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # 4. Verify Market Data (Chart)
    print("\n4. Verifying Market Data (Chart)...")
    for ticker in TICKERS:
        print(f"  Fetching history for {ticker}...", end=" ", flush=True)
        try:
            resp = requests.get(f"{BASE_URL}/predictions/market-data/{ticker}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ Success ({len(data)} candles)")
                else:
                    print(f"⚠️ Empty data returned")
            else:
                print(f"❌ Failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_system()
