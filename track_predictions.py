#!/usr/bin/env python3
import json
from datetime import datetime

def log_prediction(ticker, signal, price, action="PENDING"):
    """Log a prediction to a JSON file"""
    log_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "signal": signal,
        "price_at_signal": price,
        "action": action,
        "outcome": "PENDING"
    }
    
    try:
        with open("predictions_log.json", "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    logs.append(log_entry)
    
    with open("predictions_log.json", "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Logged prediction: {ticker} {signal} at ${price}")

def update_outcome(index, outcome, price_at_outcome=None):
    """Update the outcome of a prediction"""
    try:
        with open("predictions_log.json", "r") as f:
            logs = json.load(f)
        
        if 0 <= index < len(logs):
            logs[index]["outcome"] = outcome
            if price_at_outcome:
                logs[index]["price_at_outcome"] = price_at_outcome
            
            with open("predictions_log.json", "w") as f:
                json.dump(logs, f, indent=2)
            
            print(f"Updated prediction {index} with outcome: {outcome}")
        else:
            print("Invalid prediction index")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No predictions log found")

def show_logs():
    """Display all logged predictions"""
    try:
        with open("predictions_log.json", "r") as f:
            logs = json.load(f)
        
        for i, log in enumerate(logs):
            print(f"[{i}] {log['date']} - {log['ticker']} {log['signal']} at ${log['price_at_signal']} - Action: {log['action']} - Outcome: {log['outcome']}")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No predictions log found")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 track_predictions.py [log|update|show] [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "log":
        if len(sys.argv) < 5:
            print("Usage: python3 track_predictions.py log [ticker] [signal] [price] [action]")
            sys.exit(1)
        log_prediction(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else "PENDING")
    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: python3 track_predictions.py update [index] [outcome] [price_at_outcome]")
            sys.exit(1)
        update_outcome(int(sys.argv[2]), sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else None)
    elif command == "show":
        show_logs()
    else:
        print("Unknown command")
