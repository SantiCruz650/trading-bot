import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def find_optimal_threshold(y_true, y_prob):
    """Find the optimal threshold for signal generation"""
    thresholds = np.arange(0.005, 0.05, 0.005)  # Test thresholds from 0.5% to 5%
    
    best_threshold = 0.01  # Default to 1%
    best_f1 = 0
    
    for threshold in thresholds:
        # Generate signals based on threshold
        y_pred = np.zeros_like(y_true)
        
        # Buy signal (1) if predicted price increase > threshold
        y_pred[y_prob > 1 + threshold] = 1
        
        # Sell signal (-1) if predicted price decrease < -threshold
        y_pred[y_prob < 1 - threshold] = -1
        
        # Hold signal (0) for small changes
        y_pred[(y_prob >= 1 - threshold) & (y_prob <= 1 + threshold)] = 0
        
        # Calculate F1 score (weighted for multi-class)
        f1 = f1_score(y_true, y_pred, average='weighted')
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    print(f"Optimal threshold: {best_threshold:.3f} (F1: {best_f1:.4f})")
    return best_threshold

def evaluate_threshold_performance(y_true, y_prob, threshold):
    """Evaluate performance at a specific threshold"""
    # Generate signals based on threshold
    y_pred = np.zeros_like(y_true)
    
    # Buy signal (1) if predicted price increase > threshold
    y_pred[y_prob > 1 + threshold] = 1
    
    # Sell signal (-1) if predicted price decrease < -threshold
    y_pred[y_prob < 1 - threshold] = -1
    
    # Hold signal (0) for small changes
    y_pred[(y_prob >= 1 - threshold) & (y_prob <= 1 + threshold)] = 0
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    print(f"Threshold: {threshold:.3f}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    
    # Signal distribution
    signal_counts = pd.Series(y_pred).value_counts().sort_index()
    print(f"Signal distribution: {dict(signal_counts)}")
    
    return accuracy, precision, recall, f1

if __name__ == "__main__":
    # Load your data and model predictions
    # y_true = ...  # Actual signals
    # y_prob = ...  # Predicted price ratios
    
    # Find optimal threshold
    # optimal_threshold = find_optimal_threshold(y_true, y_prob)
    
    # Evaluate at optimal threshold
    # evaluate_threshold_performance(y_true, y_prob, optimal_threshold)
    
    print("Threshold optimization complete!")
