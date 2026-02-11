import requests
import json
import os
from datetime import datetime

def run_daily_report():
    url = "http://localhost:8000/report"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Error: API returned status {response.status_code}")
            return
        
        report = response.json()
        
        # 1. Save JSON Snapshot
        reports_dir = "/home/santiagomiguelcruz/trading-bot/reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            
        filename = f"report_{report['date']}.json"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=4)
        
        print(f"✅ Snapshot saved to {filepath}")
        
        # 2. Print Summary
        print(f"\n--- Daily Report for {report['date']} ---")
        print(f"Bot Status: {report['bot_status']}")
        print(f"Total Trades Today: {report['total_trades_today']}")
        print(f"Daily PnL: {report['daily_pnl']:.2f} USDT")
        print(f"Daily Max Drawdown: {report['daily_max_drawdown_pct']}%")
        print(f"ETH Accumulated: {report['eth_accumulated']:.6f}")
        print(f"Balance Start of Day: ${report['balance_start_of_day']:.2f}")
        print(f"Current Balance: ${report['current_balance']:.2f}")
        print(f"Daily Cash Flow: {report['daily_cash_flow']:.2f} USDT")
        
        print("\n--- Portfolio ---")
        for ticker, data in report["portfolio"].items():
            print(f"{ticker}: {data['amount']:.6f} (${data['value_usdt']:.2f})")
            
        print(f"\nTotal Portfolio Value: ${report['total_portfolio_value']:.2f}")
        print(f"Total PnL: ${report['total_pnl_usdt']:.2f} ({report['total_pnl_pct']:.2f}%)")
        
    except Exception as e:
        print(f"❌ Error fetching report: {e}")

if __name__ == "__main__":
    run_daily_report()
