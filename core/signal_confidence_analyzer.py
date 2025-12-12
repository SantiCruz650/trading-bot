#!/usr/bin/env python3
import json
from datetime import datetime
import os

def analyze_signal_accuracy():
    """Analyze when your bot's signals are most accurate"""
    
    # Load predictions and trades
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
    
    if not predictions or not trades:
        print("Not enough data to analyze signal accuracy.")
        return
    
    print("\n" + "="*60)
    print("         SIGNAL CONFIDENCE ANALYSIS")
    print("="*60)
    
    # Analyze by market conditions (simplified)
    # In a real implementation, you'd fetch market data for these periods
    
    # Analyze by day of week
    day_performance = {}
    
    for prediction in predictions:
        if prediction.get("outcome") not in ["CORRECT", "INCORRECT"]:
            continue
            
        date = datetime.strptime(prediction["date"], "%Y-%m-%d %H:%M:%S")
        day_name = date.strftime("%A")
        
        if day_name not in day_performance:
            day_performance[day_name] = {"correct": 0, "total": 0}
        
        day_performance[day_name]["total"] += 1
        if prediction["outcome"] == "CORRECT":
            day_performance[day_name]["correct"] += 1
    
    print("\nAccuracy by Day of Week:")
    for day, stats in day_performance.items():
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {day}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
    
    # Analyze by signal type
    signal_performance = {}
    
    for prediction in predictions:
        if prediction.get("outcome") not in ["CORRECT", "INCORRECT"]:
            continue
            
        signal = prediction["signal"]
        
        if signal not in signal_performance:
            signal_performance[signal] = {"correct": 0, "total": 0}
        
        signal_performance[signal]["total"] += 1
        if prediction["outcome"] == "CORRECT":
            signal_performance[signal]["correct"] += 1
    
    print("\nAccuracy by Signal Type:")
    for signal, stats in signal_performance.items():
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {signal}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
    
    # Analyze by time of day
    time_performance = {}
    
    for prediction in predictions:
        if prediction.get("outcome") not in ["CORRECT", "INCORRECT"]:
            continue
            
        hour = datetime.strptime(prediction["date"], "%Y-%m-%d %H:%M:%S").hour
        time_period = f"{hour}:00"
        
        if time_period not in time_performance:
            time_performance[time_period] = {"correct": 0, "total": 0}
        
        time_performance[time_period]["total"] += 1
        if prediction["outcome"] == "CORRECT":
            time_performance[time_period]["correct"] += 1
    
    print("\nAccuracy by Hour of Day:")
    for time, stats in sorted(time_performance.items()):
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {time}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
    
    print("="*60)

def suggest_confidence_strategies():
    """Suggest strategies based on confidence analysis"""
    
    print("\n" + "="*60)
    print("         SIGNAL CONFIDENCE STRATEGIES")
    print("="*60)
    
    print("\n1. TIME-BASED FILTERING:")
    print("   - Only trade during hours when your bot has highest accuracy")
    print("   - Avoid trading during low-confidence periods")
    print("   - Consider time zone effects on crypto markets")
    
    print("\n2. SIGNAL-TYPE FILTERING:")
    print("   - Focus on your most accurate signal types")
    print("   - Use additional confirmation for lower-confidence signals")
    print("   - Consider different position sizes based on signal confidence")
    
    print("\n3. MARKET CONDITION ANALYSIS:")
    print("   - Track performance during trending vs. ranging markets")
    print("   - Monitor volatility's impact on signal accuracy")
    print("   - Consider macroeconomic events that might affect crypto")
    
    print("\n4. CONSECUTIVE SIGNAL ANALYSIS:")
    print("   - Track accuracy after consecutive correct/incorrect signals")
    print("   - Consider reducing position size after a losing streak")
    print("   - Look for patterns in signal sequences")
    
    print("\n5. TECHNICAL INDICATOR CORRELATION:")
    print("   - Identify which technical indicators align with accurate signals")
    print("   - Develop a scoring system for signal confidence")
    print("   - Consider multi-timeframe analysis for confirmation")
    
    print("="*60)

if __name__ == "__main__":
    analyze_signal_accuracy()
    suggest_confidence_strategies()
