import sys
import os
import traceback

# Add ml_service to path
sys.path.append(os.path.join(os.getcwd(), "ml_service"))

try:
    from app.main import run_full_backtest
    print("Running backtest for DOGE...")
    result = run_full_backtest("DOGE", 100)
    print("Result:", result)
except Exception:
    traceback.print_exc()
