#!/usr/bin/env python3
import json
from datetime import datetime
import os

METRICS_FILE = "data/performance_metrics.json"

def init_metrics_file():
    """Initialize the metrics tracking file"""
    if not os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, "w") as f:
            json.dump({
                "metrics": [],
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "profit_factor": 0
            }, f)

def calculate_performance_metrics(trades):
    """Calculate key performance metrics beyond accuracy"""
    if not trades:
        return {}
    
    # Calculate daily returns
    daily_returns = []
    cumulative_return = 1
    
    for trade in trades:
        trade_return = trade["profit"] / (trade["entry_price"] * trade["quantity"])
        cumulative_return *= (1 + trade_return)
        daily_returns.append(trade_return)
    
    # Calculate Sharpe Ratio (simplified)
    if daily_returns:
        avg_return = sum(daily_returns) / len(daily_returns)
        std_dev = (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Calculate Maximum Drawdown
    peak = cumulative_return
    max_drawdown = 0
    
    for trade in trades:
        trade_return = trade["profit"] / (trade["entry_price"] * trade["quantity"])
        cumulative_return *= (1 + trade_return)
        
        if cumulative_return > peak:
            peak = cumulative_return
        
        drawdown = (peak - cumulative_return) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate Profit Factor
    winning_trades = [t for t in trades if t["profit"] > 0]
    losing_trades = [t for t in trades if t["profit"] < 0]
    
    total_wins = sum(t["profit"] for t in winning_trades)
    total_losses = abs(sum(t["profit"] for t in losing_trades))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    return {
        "total_return": (cumulative_return - 1) * 100,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown * 100,
        "profit_factor": profit_factor,
        "win_rate": len(winning_trades) / len(trades) if trades else 0
    }

def show_performance_summary():
    """Show performance metrics summary"""
    init_metrics_file()
    
    # Load trades from profit tracker
    try:
        with open("profit_log.json", "r") as f:
            profit_data = json.load(f)
            trades = profit_data.get("trades", [])
    except:
        trades = []
    
    if not trades:
        print("No trades to analyze.")
        return
    
    metrics = calculate_performance_metrics(trades)
    
    print("\n" + "="*60)
    print("         PERFORMANCE METRICS (Beyond Accuracy)")
    print("="*60)
    print(f"Total Return: {metrics['total_return']:.2f}%")
    print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    
    print("\nWhat these metrics mean:")
    print("- Total Return: Overall profitability")
    print("- Win Rate: Percentage of profitable trades")
    print("- Sharpe Ratio: Risk-adjusted returns (higher is better)")
    print("- Max Drawdown: Largest peak-to-trough decline")
    print("- Profit Factor: Total wins divided by total losses")
    
    print("="*60)

if __name__ == "__main__":
    show_performance_summary()
