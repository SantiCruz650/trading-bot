import sys
import os
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

import yfinance as yf
import pandas as pd
from backend.backtester_logic import run_backtest
import json
from datetime import datetime, timedelta

def main():
    ticker = "ETH-USD"
    print(f"🚀 Starting Backtest for {ticker}...")
    
    # Fetch 5m data for the last 5 days (yfinance 1m limit is 7 days)
    # We'll use 5m to have a decent range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    data = yf.download(ticker, start=start_date, end=end_date, interval="5m", progress=False)
    
    if data.empty:
        print("❌ No data found!")
        return

    # Standardize columns
    data.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in data.columns]
    
    print(f"📊 Loaded {len(data)} candles.")
    
    results = run_backtest(data)
    
    print("\n" + "="*30)
    print("📈 BACKTEST RESULTS")
    print("="*30)
    print(f"Final Equity: ${results['final_equity']:,.2f}")
    print(f"Total PnL:    ${results['total_pnl']:,.2f}")
    print(f"Max Drawdown: {results['max_drawdown']*100:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print("="*30)
    
    # Save results
    output_path = Path("/home/santiagomiguelcruz/trading-bot/backtest_results.json")
    with open(output_path, "w") as f:
        # Don't save the full equity curve to keep file small
        summary = {k: v for k, v in results.items() if k != 'equity_curve'}
        summary['equity_curve_sample'] = results['equity_curve'][-20:]
        json.dump(summary, f, indent=2)
    
    print(f"✅ Results saved to {output_path}")

if __name__ == "__main__":
    main()
