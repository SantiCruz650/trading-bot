#!/usr/bin/env python3
import json
from datetime import datetime
import os

PROFIT_FILE = "data/profit_log.json"

def init_profit_file():
    """Initialize the profit tracking file"""
    if not os.path.exists(PROFIT_FILE):
        with open(PROFIT_FILE, "w") as f:
            json.dump({"trades": [], "total_profit": 0}, f)

def log_trade(ticker, action, entry_price, exit_price, quantity):
    """Log a trade and calculate profit"""
    init_profit_file()
    
    with open(PROFIT_FILE, "r") as f:
        data = json.load(f)
    
    # Calculate profit
    if action == "BUY":
        profit = (exit_price - entry_price) * quantity
    else:  # SELL
        profit = (entry_price - exit_price) * quantity
    
    trade = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "action": action,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "profit": profit
    }
    
    data["trades"].append(trade)
    data["total_profit"] += profit
    
    with open(PROFIT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Logged {action} trade for {ticker}: Profit ${profit:.2f}")
    print(f"Total profit: ${data['total_profit']:.2f}")

def show_profit_summary():
    """Show profit summary"""
    init_profit_file()
    
    with open(PROFIT_FILE, "r") as f:
        data = json.load(f)
    
    print("\n" + "="*50)
    print("         PROFIT TRACKING SUMMARY")
    print("="*50)
    print(f"Total Profit: ${data['total_profit']:.2f}")
    print(f"Number of Trades: {len(data['trades'])}")
    
    # Separate by ticker
    btc_trades = [t for t in data["trades"] if t["ticker"] == "BTC"]
    eth_trades = [t for t in data["trades"] if t["ticker"] == "ETH"]
    
    btc_profit = sum(t["profit"] for t in btc_trades)
    eth_profit = sum(t["profit"] for t in eth_trades)
    
    print(f"BTC Profit: ${btc_profit:.2f} ({len(btc_trades)} trades)")
    print(f"ETH Profit: ${eth_profit:.2f} ({len(eth_trades)} trades)")
    
    print("\nRecent Trades:")
    for trade in data["trades"][-5:]:
        print(f"{trade['date']} - {trade['ticker']} {trade['action']} at ${trade['entry_price']}, sold at ${trade['exit_price']}, profit: ${trade['profit']:.2f}")
    
    print("="*50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 profit_tracker.py [log|show] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "log":
        if len(sys.argv) < 6:
            print("Usage: python3 profit_tracker.py log [ticker] [action] [entry_price] [exit_price] [quantity]")
            sys.exit(1)
        log_trade(sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]))
    elif command == "show":
        show_profit_summary()
    else:
        print("Unknown command")
