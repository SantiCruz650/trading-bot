import sys
import os
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.ml_evaluator import MLEvaluator

def generate_report():
    evaluator = MLEvaluator()
    metrics = evaluator.calculate_metrics()
    
    print("\n" + "="*60)
    print("         ML QUANTITATIVE PERFORMANCE REPORT")
    print("="*60)
    
    if not metrics:
        print("No data available for evaluation yet.")
        return

    print(f"Total Evaluation Events: {metrics['total_events']}")
    print(f"Trades Executed (ML Approved): {metrics['executed']}")
    print(f"Trades Blocked by ML: {metrics['blocked_by_ml']}")
    
    print("\n--- Market Regime Distribution ---")
    for regime, count in metrics['regime_distribution'].items():
        print(f"{regime}: {count} events")
        
    print("\n--- Quantitative Impact (Projected) ---")
    # Note: These require more historical data to be accurate
    print("Avoided Drawdown: [Pending more data]")
    print("ML Alpha: [Pending more data]")
    print("DCA Efficiency: [Pending more data]")
    
    print("\n" + "="*60)
    print("This report measures the real value added by ML to the DCA strategy.")
    print("="*60)

if __name__ == "__main__":
    generate_report()
