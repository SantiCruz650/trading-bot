#!/usr/bin/env python3
import subprocess
import sys

def update_outcome(index, outcome, price_at_outcome=None):
    """Update the outcome of a prediction"""
    cmd = ["python3", "track_predictions.py", "update", str(index), outcome]
    if price_at_outcome:
        cmd.append(str(price_at_outcome))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Error:", result.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 update_prediction_outcome.py [index] [outcome] [price_at_outcome]")
        sys.exit(1)
    
    index = sys.argv[1]
    outcome = sys.argv[2]
    price_at_outcome = sys.argv[3] if len(sys.argv) > 3 else None
    
    update_outcome(index, outcome, price_at_outcome)
