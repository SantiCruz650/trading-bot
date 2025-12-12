import requests
import sys
import time
import json

BASE_URL_BACKEND = "http://localhost:8000"
BASE_URL_ML = "http://localhost:8001"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_endpoint(url, description):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            log(f"{description}: OK ({response.status_code})", "PASS")
            return True, response.json()
        else:
            log(f"{description}: FAILED ({response.status_code}) - {response.text}", "FAIL")
            return False, None
    except Exception as e:
        log(f"{description}: ERROR - {e}", "FAIL")
        return False, None

def run_tests():
    log("Waiting for services to warm up...", "INFO")
    time.sleep(5)
    
    # 1. Health Checks
    log("\n--- Health Checks ---")
    test_endpoint(f"{BASE_URL_BACKEND}/health", "Backend Health")
    test_endpoint(f"{BASE_URL_ML}/health", "ML Service Health")

    # 2. Portfolio
    log("\n--- Portfolio ---")
    # Assuming /api/trading/portfolio exists based on router tags
    test_endpoint(f"{BASE_URL_BACKEND}/api/trading/portfolio", "Get Portfolio")

    # 3. Strategies
    log("\n--- Strategies ---")
    test_endpoint(f"{BASE_URL_BACKEND}/api/strategies", "Get Active Strategies")

    # 4. Predictions
    log("\n--- Predictions ---")
    # Test a specific ticker
    success, data = test_endpoint(f"{BASE_URL_ML}/predict/BTC", "Predict BTC (ML Service)")
    if success:
        log(f"BTC Prediction: {json.dumps(data, indent=2)}")
    
    # Test backend proxy if it exists
    test_endpoint(f"{BASE_URL_BACKEND}/api/predictions/latest", "Get Latest Predictions (Backend)")

    # 5. Backtest
    log("\n--- Backtest ---")
    # Use a small number of days for speed
    test_endpoint(f"{BASE_URL_ML}/backtest/BTC?days=50", "Backtest BTC (50 days)")

if __name__ == "__main__":
    run_tests()
