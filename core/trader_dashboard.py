#!/usr/bin/env python3
import json
import requests
from datetime import datetime
import os

def get_latest_signals():
    """Get the latest signals from the bot"""
    
    # Get a fresh token
    token_response = requests.post(
        "http://localhost:8000/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data="username=testuser&password=testpass"
    )
    
    if token_response.status_code != 200:
        print("Error getting authentication token")
        return []
    
    token = token_response.json()["access_token"]
    
    # Get predictions for BTC and ETH
    signals = []
    
    for ticker in ["BTC", "ETH"]:
        response = requests.post(
            f"http://localhost:8000/predict/{ticker}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            signals.append({
                "ticker": data["ticker"],
                "signal": data["signal"],
                "price": data["last_close"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return signals

def display_trader_dashboard():
    """Display a simple dashboard for the trader"""
    
    print("\n" + "="*60)
    print("         TRADER DASHBOARD")
    print("="*60)
    
    # Get latest signals
    signals = get_latest_signals()
    
    if not signals:
        print("No signals available at the moment.")
        return
    
    print("\nLATEST SIGNALS:")
    for signal in signals:
        print(f"\n{signal['ticker']}: {signal['signal']} at ${signal['price']}")
        print(f"Time: {signal['time']}")
        
        # Add space for trader notes
        print("\nTrader Notes:")
        print("-" * 40)
        print("(Market context, news, technical analysis, etc.)")
        print("-" * 40)
    
    print("\n" + "="*60)
    print("TRADING DECISIONS:")
    print("1. Follow signal exactly")
    print("2. Modify signal (different entry/exit)")
    print("3. Ignore signal")
    print("4. Wait for more confirmation")
    print("="*60)

def log_trader_decision():
    """Log the trader's decision and reasoning"""
    
    print("\nLog your trading decision:")
    ticker = input("Ticker (BTC/ETH): ")
    signal = input("Bot signal (BUY/SELL/HOLD): ")
    decision = input("Your decision (follow/modify/ignore/wait): ")
    reasoning = input("Your reasoning: ")
    
    # Load existing log
    try:
        with open("collaborative_trading_log.json", "r") as f:
            data = json.load(f)
    except:
        data = {"signals": [], "decisions": [], "outcomes": [], "insights": []}
    
    # Add decision
    decision_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "bot_signal": signal,
        "trader_decision": decision,
        "reasoning": reasoning
    }
    
    data["decisions"].append(decision_data)
    
    # Save updated log
    with open("collaborative_trading_log.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print("\nDecision logged successfully!")

if __name__ == "__main__":
    display_trader_dashboard()
    log_trader_decision()
