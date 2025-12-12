#!/usr/bin/env python3
import json
from datetime import datetime
import os

PROFIT_FILE = "profit_log.json"

def init_profit_file():
    """Initialize the profit tracking file"""
    if not os.path.exists(PROFIT_FILE):
        with open(PROFIT_FILE, "w") as f:
            json.dump({"trades": [], "total_profit": 0, "win_rate": 0, "profit_factor": 0}, f)

def log_trade(ticker, action, entry_price, exit_price, quantity, signal_accuracy):
    """Log a trade and calculate profit with accuracy consideration"""
    init_profit_file()
    
    with open(PROFIT_FILE, "r") as f:
        data = json.load(f)
    
    # Calculate profit
    if action == "BUY":
        profit = (exit_price - entry_price) * quantity
    else:  # SELL
        profit = (entry_price - exit_price) * quantity
    
    # Calculate risk/reward ratio
    risk = abs(entry_price - exit_price) * quantity
    reward = abs(profit)
    risk_reward = reward / risk if risk > 0 else 0
    
    trade = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "action": action,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "quantity": quantity,
        "profit": profit,
        "risk_reward": risk_reward,
        "signal_accuracy": signal_accuracy
    }
    
    data["trades"].append(trade)
    data["total_profit"] += profit
    
    # Calculate win rate and profit factor
    winning_trades = [t for t in data["trades"] if t["profit"] > 0]
    losing_trades = [t for t in data["trades"] if t["profit"] < 0]
    
    data["win_rate"] = len(winning_trades) / len(data["trades"]) if data["trades"] else 0
    
    total_wins = sum(t["profit"] for t in winning_trades)
    total_losses = abs(sum(t["profit"] for t in losing_trades))
    data["profit_factor"] = total_wins / total_losses if total_losses > 0 else float('inf')
    
    with open(PROFIT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Logged {action} trade for {ticker}: Profit ${profit:.2f} (Risk/Reward: {risk_reward:.2f})")
    print(f"Win Rate: {data['win_rate']*100:.1f}%, Profit Factor: {data['profit_factor']:.2f}")
    print(f"Total profit: ${data['total_profit']:.2f}")

def calculate_position_size(account_balance, risk_percent, stop_loss_percent):
    """Calculate optimal position size based on risk management"""
    risk_amount = account_balance * (risk_percent / 100)
    position_size = risk_amount / (stop_loss_percent / 100)
    return position_size

def show_profit_summary():
    """Show profit summary with accuracy considerations"""
    init_profit_file()
    
    with open(PROFIT_FILE, "r") as f:
        data = json.load(f)
    
    print("\n" + "="*60)
    print("         ADVANCED PROFIT TRACKING SUMMARY")
    print("="*60)
    print(f"Total Profit: ${data['total_profit']:.2f}")
    print(f"Number of Trades: {len(data['trades'])}")
    print(f"Win Rate: {data['win_rate']*100:.1f}%")
    print(f"Profit Factor: {data['profit_factor']:.2f}")
    
    # Separate by ticker
    btc_trades = [t for t in data["trades"] if t["ticker"] == "BTC"]
    eth_trades = [t for t in data["trades"] if t["ticker"] == "ETH"]
    
    btc_profit = sum(t["profit"] for t in btc_trades)
    eth_profit = sum(t["profit"] for t in eth_trades)
    
    print(f"BTC Profit: ${btc_profit:.2f} ({len(btc_trades)} trades)")
    print(f"ETH Profit: ${eth_profit:.2f} ({len(eth_trades)} trades)")
    
    # Average risk/reward
    avg_risk_reward = sum(t["risk_reward"] for t in data["trades"]) / len(data["trades"]) if data["trades"] else 0
    print(f"Average Risk/Reward: {avg_risk_reward:.2f}")
    
    print("\nRecent Trades:")
    for trade in data["trades"][-5:]:
        print(f"{trade['date']} - {trade['ticker']} {trade['action']} at ${trade['entry_price']}, sold at ${trade['exit_price']}, profit: ${trade['profit']:.2f} (R/R: {trade['risk_reward']:.2f})")
    
    print("="*60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 advanced_profit_tracker.py [log|show|position] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "log":
        if len(sys.argv) < 7:
            print("Usage: python3 advanced_profit_tracker.py log [ticker] [action] [entry_price] [exit_price] [quantity] [signal_accuracy]")
            sys.exit(1)
        log_trade(sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]))
    elif command == "show":
        show_profit_summary()
    elif command == "position":
        if len(sys.argv) < 5:
            print("Usage: python3 advanced_profit_tracker.py position [account_balance] [risk_percent] [stop_loss_percent]")
            sys.exit(1)
        position = calculate_position_size(float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
        print(f"Recommended position size: ${position:.2f}")
    else:
        print("Unknown command")
