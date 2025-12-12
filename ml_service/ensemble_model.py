import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
import joblib

def create_ensemble_model():
    """Create an ensemble of different models"""
    # Define individual models
    rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
    lr = LogisticRegression(random_state=42, max_iter=1000)
    svc = SVC(probability=True, random_state=42)
    
    # Create voting classifier
    ensemble = VotingClassifier(
        estimators=[
            ('random_forest', rf),
            ('gradient_boosting', gb),
            ('logistic_regression', lr),
            ('svc', svc)
        ],
        voting='soft'  # Use probability averages
    )
    
    return ensemble

def train_ensemble(X_train, y_train):
    """Train the ensemble model"""
    ensemble = create_ensemble_model()
    ensemble.fit(X_train, y_train)
    return ensemble

def evaluate_ensemble(model, X_test, y_test):
    """Evaluate ensemble performance"""
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Ensemble test accuracy: {accuracy:.4f}")
    
    # Compare with individual models
    for name, estimator in model.estimators:
        estimator.fit(X_train, y_train)
        y_pred_individual = estimator.predict(X_test)
        accuracy_individual = accuracy_score(y_test, y_pred_individual)
        print(f"{name} accuracy: {accuracy_individual:.4f}")
    
    return accuracy

if __name__ == "__main__":
    # Load your data
    # df = pd.read_csv('your_data.csv')
    # X = df.drop(['target'], axis=1)
    # y = df['target']
    
    # Split data
    # split_idx = int(len(X) * 0.8)
    # X_train, X_test = X[:split_idx], X[split_idx:]
    # y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Train ensemble
    # ensemble_model = train_ensemble(X_train, y_train)
    
    # Evaluate ensemble
    # accuracy = evaluate_ensemble(ensemble_model, X_test, y_test)
    
    # Save model
    # joblib.dump(ensemble_model, 'ensemble_model.joblib')
    
    print("Ensemble model training complete!")
