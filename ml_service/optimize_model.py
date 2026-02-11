import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report
import joblib

def optimize_rf_model(X_train, y_train):
    """Optimize RandomForest model using GridSearchCV"""
    # Define parameter grid
    param_grid = {
        'n_estimators': [100, 300, 500, 700],
        'max_depth': [5, 10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None]
    }
    
    # Use TimeSeriesSplit for time series data
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Create RandomForest model
    rf = RandomForestClassifier(random_state=42)
    
    # Grid search with cross-validation
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=tscv,
        scoring='accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    # Fit the grid search
    grid_search.fit(X_train, y_train)
    
    # Get the best model
    best_model = grid_search.best_estimator_
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation accuracy: {grid_search.best_score_:.4f}")
    
    return best_model

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Test accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
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
    
    # Optimize model
    # best_model = optimize_rf_model(X_train, y_train)
    
    # Evaluate model
    # accuracy = evaluate_model(best_model, X_test, y_test)
    
    # Save model
    # joblib.dump(best_model, 'optimized_rf_model.joblib')
    
    print("Model optimization complete!")
