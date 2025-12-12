#!/usr/bin/env python3
import json
from datetime import datetime
import os

def load_predictions():
    """Load predictions from JSON file"""
    try:
        with open("data/predictions_log.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def calculate_crypto_stats(predictions):
    """Calculate statistics for BTC and ETH only"""
    # Filter for BTC and ETH only
    crypto_predictions = [p for p in predictions if p.get("ticker") in ["BTC", "ETH"]]
    
    if not crypto_predictions:
        return {}
    
    total = len(crypto_predictions)
    correct = sum(1 for p in crypto_predictions if p.get("outcome") == "CORRECT")
    incorrect = sum(1 for p in crypto_predictions if p.get("outcome") == "INCORRECT")
    pending = sum(1 for p in crypto_predictions if p.get("outcome") == "PENDING")
    
    accuracy = correct / (correct + incorrect) if (correct + incorrect) > 0 else 0
    
    # Separate by ticker
    btc_predictions = [p for p in crypto_predictions if p.get("ticker") == "BTC"]
    eth_predictions = [p for p in crypto_predictions if p.get("ticker") == "ETH"]
    
    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "pending": pending,
        "accuracy": accuracy,
        "btc_count": len(btc_predictions),
        "eth_count": len(eth_predictions),
        "btc_predictions": btc_predictions[-3:],  # Last 3 BTC predictions
        "eth_predictions": eth_predictions[-3:]   # Last 3 ETH predictions
    }

def display_crypto_dashboard():
    """Display a specialized dashboard for BTC and ETH"""
    predictions = load_predictions()
    stats = calculate_crypto_stats(predictions)
    
    print("\n" + "="*60)
    print("      BTC & ETH TRADING BOT PERFORMANCE DASHBOARD")
    print("="*60)
    
    if not stats:
        print("No BTC/ETH predictions yet.")
        return
    
    print(f"Total BTC/ETH Predictions: {stats['total']}")
    print(f"Correct: {stats['correct']} ({stats['correct']/stats['total']*100:.1f}%)")
    print(f"Incorrect: {stats['incorrect']} ({stats['incorrect']/stats['total']*100:.1f}%)")
    print(f"Pending: {stats['pending']} ({stats['pending']/stats['total']*100:.1f}%)")
    
    if stats['correct'] + stats['incorrect'] > 0:
        print(f"Overall Accuracy: {stats['accuracy']*100:.1f}%")
    
    print(f"\nBTC Predictions: {stats['btc_count']}")
    for p in stats['btc_predictions']:
        date = p.get("date", "")
        signal = p.get("signal", "")
        price = p.get("price_at_signal", "")
        outcome = p.get("outcome", "")
        print(f"  {date} - {signal} at ${price} - {outcome}")
    
    print(f"\nETH Predictions: {stats['eth_count']}")
    for p in stats['eth_predictions']:
        date = p.get("date", "")
        signal = p.get("signal", "")
        price = p.get("price_at_signal", "")
        outcome = p.get("outcome", "")
        print(f"  {date} - {signal} at ${price} - {outcome}")
    
    print("="*60)

if __name__ == "__main__":
    display_crypto_dashboard()
