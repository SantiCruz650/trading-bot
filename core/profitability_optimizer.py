#!/usr/bin/env python3
import json
from datetime import datetime
import os

def analyze_profitability_factors():
    """Analyze factors that impact profitability"""
    
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
    
    # Analyze by ticker
    btc_trades = [t for t in trades if t["ticker"] == "BTC"]
    eth_trades = [t for t in trades if t["ticker"] == "ETH"]
    
    print("\n" + "="*60)
    print("         PROFITABILITY ANALYSIS BY ASSET")
    print("="*60)
    
    for ticker, asset_trades in [("BTC", btc_trades), ("ETH", eth_trades)]:
        if not asset_trades:
            print(f"\n{ticker}: No trades yet")
            continue
            
        total_profit = sum(t["profit"] for t in asset_trades)
        winning_trades = [t for t in asset_trades if t["profit"] > 0]
        losing_trades = [t for t in asset_trades if t["profit"] < 0]
        
        avg_win = sum(t["profit"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["profit"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        print(f"\n{ticker} Performance:")
        print(f"  Total Profit: ${total_profit:.2f}")
        print(f"  Number of Trades: {len(asset_trades)}")
        print(f"  Win Rate: {len(winning_trades)/len(asset_trades)*100:.1f}%")
        print(f"  Average Win: ${avg_win:.2f}")
        print(f"  Average Loss: ${avg_loss:.2f}")
        print(f"  Profit Factor: {abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "  Profit Factor: N/A")
    
    # Analyze by signal type
    buy_trades = [t for t in trades if t["action"] == "BUY"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    
    print("\n" + "="*60)
    print("         PROFITABILITY ANALYSIS BY SIGNAL")
    print("="*60)
    
    for signal_type, signal_trades in [("BUY", buy_trades), ("SELL", sell_trades)]:
        if not signal_trades:
            print(f"\n{signal_type} signals: No trades yet")
            continue
            
        total_profit = sum(t["profit"] for t in signal_trades)
        winning_trades = [t for t in signal_trades if t["profit"] > 0]
        
        print(f"\n{signal_type} Signal Performance:")
        print(f"  Total Profit: ${total_profit:.2f}")
        print(f"  Number of Trades: {len(signal_trades)}")
        print(f"  Win Rate: {len(winning_trades)/len(signal_trades)*100:.1f}%")
    
    # Analyze by time of day
    print("\n" + "="*60)
    print("         PROFITABILITY ANALYSIS BY TIME")
    print("="*60)
    
    morning_trades = []  # 6AM-12PM
    afternoon_trades = []  # 12PM-6PM
    evening_trades = []  # 6PM-12AM
    night_trades = []  # 12AM-6AM
    
    for trade in trades:
        hour = datetime.strptime(trade["date"], "%Y-%m-%d %H:%M:%S").hour
        
        if 6 <= hour < 12:
            morning_trades.append(trade)
        elif 12 <= hour < 18:
            afternoon_trades.append(trade)
        elif 18 <= hour < 24:
            evening_trades.append(trade)
        else:
            night_trades.append(trade)
    
    time_periods = [
        ("Morning (6AM-12PM)", morning_trades),
        ("Afternoon (12PM-6PM)", afternoon_trades),
        ("Evening (6PM-12AM)", evening_trades),
        ("Night (12AM-6AM)", night_trades)
    ]
    
    for period_name, period_trades in time_periods:
        if not period_trades:
            print(f"\n{period_name}: No trades yet")
            continue
            
        total_profit = sum(t["profit"] for t in period_trades)
        winning_trades = [t for t in period_trades if t["profit"] > 0]
        
        print(f"\n{period_name} Performance:")
        print(f"  Total Profit: ${total_profit:.2f}")
        print(f"  Number of Trades: {len(period_trades)}")
        print(f"  Win Rate: {len(winning_trades)/len(period_trades)*100:.1f}%")
    
    print("="*60)

def suggest_optimization_strategies():
    """Suggest strategies based on the analysis"""
    
    print("\n" + "="*60)
    print("         PROFITABILITY OPTIMIZATION STRATEGIES")
    print("="*60)
    
    print("\n1. POSITION SIZING STRATEGIES:")
    print("   - Use smaller positions for lower-confidence signals")
    print("   - Increase position size during your most profitable time periods")
    print("   - Consider fixed fractional position sizing (e.g., 2% per trade)")
    
    print("\n2. RISK MANAGEMENT STRATEGIES:")
    print("   - Set tighter stop-losses for volatile assets")
    print("   - Use trailing stops to protect profits")
    print("   - Consider a maximum daily loss limit")
    
    print("\n3. SIGNAL FILTERING STRATEGIES:")
    print("   - Only trade signals during your most profitable time periods")
    print("   - Require additional confirmation for lower-confidence signals")
    print("   - Avoid trading during high-impact news events")
    
    print("\n4. PROFIT TAKING STRATEGIES:")
    print("   - Set realistic profit targets based on historical performance")
    print("   - Consider scaling out of positions at different levels")
    print("   - Use time-based exits if price targets aren't hit")
    
    print("\n5. PORTFOLIO MANAGEMENT STRATEGIES:")
    print("   - Consider rebalancing between BTC and ETH based on performance")
    print("   - Keep some cash in reserve for high-confidence opportunities")
    print("   - Review and adjust your strategy monthly")
    
    print("="*60)

if __name__ == "__main__":
    analyze_profitability_factors()
    suggest_optimization_strategies()
