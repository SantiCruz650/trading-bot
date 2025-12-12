#!/usr/bin/env python3
import json
from datetime import datetime
import os

def generate_trading_strategy():
    """Generate a personalized trading strategy based on your data"""
    
    # Load your data
    try:
        with open("data/predictions_log.json", "r") as f:
            predictions = json.load(f)
    except:
        predictions = []
    
    try:
        with open("profit_log.json", "r") as f:
            profit_data = json.load(f)
            trades = profit_data.get("trades", [])
    except:
        trades = []
    
    print("\n" + "="*60)
    print("         PERSONALIZED TRADING STRATEGY")
    print("="*60)
    
    print("\nBased on your trading history, here's your personalized strategy:")
    
    # Analyze best performing asset
    btc_trades = [t for t in trades if t["ticker"] == "BTC"]
    eth_trades = [t for t in trades if t["ticker"] == "ETH"]
    
    btc_profit = sum(t["profit"] for t in btc_trades)
    eth_profit = sum(t["profit"] for t in eth_trades)
    
    if btc_profit > eth_profit:
        print("\n1. ASSET FOCUS:")
        print("   - Focus more on BTC (your better performing asset)")
        print("   - Consider 70% BTC, 30% ETH allocation")
    else:
        print("\n1. ASSET FOCUS:")
        print("   - Focus more on ETH (your better performing asset)")
        print("   - Consider 70% ETH, 30% BTC allocation")
    
    # Analyze best signal type
    buy_trades = [t for t in trades if t["action"] == "BUY"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    
    buy_profit = sum(t["profit"] for t in buy_trades)
    sell_profit = sum(t["profit"] for t in sell_trades)
    
    if buy_profit > sell_profit:
        print("\n2. SIGNAL FOCUS:")
        print("   - Focus on BUY signals (your more profitable signal type)")
        print("   - Consider ignoring SELL signals or requiring additional confirmation")
    else:
        print("\n2. SIGNAL FOCUS:")
        print("   - Focus on SELL signals (your more profitable signal type)")
        print("   - Consider ignoring BUY signals or requiring additional confirmation")
    
    # Calculate recommended position size
    if trades:
        avg_trade_size = sum(t["quantity"] * t["entry_price"] for t in trades) / len(trades)
        print(f"\n3. POSITION SIZING:")
        print(f"   - Your average trade size is ${avg_trade_size:.2f}")
        print("   - Consider risking only 1-2% of your portfolio per trade")
        print("   - Use smaller positions for lower-confidence signals")
    
    # Risk management recommendations
    print("\n4. RISK MANAGEMENT:")
    print("   - Set stop-losses at 2-3% below entry for BUY signals")
    print("   - Set stop-losses at 2-3% above entry for SELL signals")
    print("   - Take partial profits at 2x your risk")
    print("   - Consider a daily loss limit of 5% of your portfolio")
    
    # Trading schedule recommendations
    print("\n5. TRADING SCHEDULE:")
    print("   - Check for signals at the same time each day")
    print("   - Avoid trading during high-volatility periods unless you have a high-risk tolerance")
    print("   - Review your performance weekly and adjust your strategy")
    
    # Record-keeping recommendations
    print("\n6. RECORD-KEEPING:")
    print("   - Continue logging all trades and predictions")
    print("   - Note the reasons for following or ignoring signals")
    print("   - Review your performance monthly to identify patterns")
    
    print("\n" + "="*60)
    print("Remember: This strategy is based on your limited trading history.")
    print("As you accumulate more data, these recommendations will become more accurate.")
    print("="*60)

if __name__ == "__main__":
    generate_trading_strategy()
