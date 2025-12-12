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

def calculate_stats(predictions):
    """Calculate statistics from predictions"""
    if not predictions:
        return {}
    
    total = len(predictions)
    correct = sum(1 for p in predictions if p.get("outcome") == "CORRECT")
    incorrect = sum(1 for p in predictions if p.get("outcome") == "INCORRECT")
    pending = sum(1 for p in predictions if p.get("outcome") == "PENDING")
    
    accuracy = correct / (correct + incorrect) if (correct + incorrect) > 0 else 0
    
    # Signal distribution
    buy_signals = sum(1 for p in predictions if p.get("signal") == "BUY")
    sell_signals = sum(1 for p in predictions if p.get("signal") == "SELL")
    hold_signals = sum(1 for p in predictions if p.get("signal") == "HOLD")
    
    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "pending": pending,
        "accuracy": accuracy,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "hold_signals": hold_signals
    }

def display_dashboard():
    """Display a simple text dashboard"""
    predictions = load_predictions()
    stats = calculate_stats(predictions)
    
    print("\n" + "="*50)
    print("         TRADING BOT PREDICTION DASHBOARD")
    print("="*50)
    
    if not stats:
        print("No predictions yet.")
        return
    
    print(f"Total Predictions: {stats['total']}")
    print(f"Correct: {stats['correct']} ({stats['correct']/stats['total']*100:.1f}%)")
    print(f"Incorrect: {stats['incorrect']} ({stats['incorrect']/stats['total']*100:.1f}%)")
    print(f"Pending: {stats['pending']} ({stats['pending']/stats['total']*100:.1f}%)")
    
    if stats['correct'] + stats['incorrect'] > 0:
        print(f"Accuracy: {stats['accuracy']*100:.1f}%")
    
    print("\nSignal Distribution:")
    print(f"BUY: {stats['buy_signals']} ({stats['buy_signals']/stats['total']*100:.1f}%)")
    print(f"SELL: {stats['sell_signals']} ({stats['sell_signals']/stats['total']*100:.1f}%)")
    print(f"HOLD: {stats['hold_signals']} ({stats['hold_signals']/stats['total']*100:.1f}%)")
    
    print("\nRecent Predictions:")
    for p in predictions[-5:]:
        date = p.get("date", "")
        ticker = p.get("ticker", "")
        signal = p.get("signal", "")
        price = p.get("price_at_signal", "")
        outcome = p.get("outcome", "")
        print(f"{date} - {ticker} {signal} at ${price} - {outcome}")
    
    print("="*50)

def plot_accuracy():
    """Plot accuracy over time"""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is not installed. Install it with: pip install matplotlib")
        return
    
    predictions = load_predictions()
    
    if not predictions:
        print("Not enough data to plot.")
        return
    
    # Filter out pending predictions
    completed = [p for p in predictions if p.get("outcome") in ["CORRECT", "INCORRECT"]]
    
    if len(completed) < 2:
        print("Not enough completed predictions to plot.")
        return
    
    # Calculate rolling accuracy
    window_size = min(5, len(completed))
    dates = []
    accuracies = []
    
    for i in range(window_size, len(completed) + 1):
        window = completed[i-window_size:i]
        correct = sum(1 for p in window if p.get("outcome") == "CORRECT")
        accuracy = correct / window_size
        
        # Use the date of the last prediction in the window
        dates.append(datetime.strptime(window[-1].get("date", ""), "%Y-%m-%d %H:%M:%S"))
        accuracies.append(accuracy)
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(dates, accuracies, marker='o')
    plt.title("Prediction Accuracy Over Time")
    plt.xlabel("Date")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("data/accuracy_plot.png")
    print("Accuracy plot saved as data/accuracy_plot.png")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "plot":
        plot_accuracy()
    else:
        display_dashboard()
