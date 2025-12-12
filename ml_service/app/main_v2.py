"""
Enhanced ML Service with improved accuracy targeting 80%+
Uses ensemble methods and advanced technical indicators
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add parent directory to path to import enhanced_ml_model
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_ml_model import EnhancedMLModel
import os

app = FastAPI(
    title="MCrypto - Enhanced Signal Prediction Service"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Global model cache
MODELS_CACHE = {}

def get_or_train_model(ticker: str) -> EnhancedMLModel:
    """Load model from cache or disk, or train new one"""
    # Check cache first
    if ticker in MODELS_CACHE:
        print(f"Using cached model for {ticker}")
        return MODELS_CACHE[ticker]
    
    # Try to load from disk
    model_path = MODELS_DIR / f"{ticker}_enhanced_model.pkl"
    if model_path.exists():
        try:
            print(f"Loading enhanced model for {ticker} from disk")
            model = EnhancedMLModel()
            model.load_model(str(model_path))
            MODELS_CACHE[ticker] = model
            return model
        except Exception as e:
            print(f"Error loading model: {e}. Training new model...")
    
    # Train new model
    print(f"Training new enhanced model for {ticker}")
    model = EnhancedMLModel(look_back_days=60, future_days=3, threshold=0.02)
    
    df = model.fetch_data(ticker, days=500)
    if df is None or len(df) < 200:
        print(f"Not enough data for {ticker}")
        return model
    
    accuracy, stats = model.train(df)
    print(f"Model trained for {ticker}: Accuracy={accuracy:.2%}")
    print(f"Stats: {stats}")
    
    # Save model
    model.save_model(str(model_path))
    MODELS_CACHE[ticker] = model
    return model

@app.get("/predict/{ticker}")
async def predict(ticker: str):
    """Get prediction for a ticker using enhanced ML model"""
    try:
        model = get_or_train_model(ticker.upper())
        
        # Fetch latest data
        df = model.fetch_data(ticker.upper(), days=300)
        if df is None or len(df) < 100:
            return {"error": f"Not enough data for {ticker}"}
        
        # Make prediction
        signal = model.predict(df)
        last_close = float(df['close'].iloc[-1])
        
        return {
            "ticker": ticker.upper(),
            "last_close": round(last_close, 2),
            "signal": signal,
            "model_type": "Enhanced Ensemble (RF + GB)",
            "features_count": len(model.get_feature_columns()) if model.model else 0
        }
    except Exception as e:
        print(f"Error in predict: {e}")
        return {"error": str(e)}

@app.post("/retrain/{ticker}")
async def retrain_model(ticker: str):
    """Force retrain model for a ticker"""
    try:
        ticker = ticker.upper()
        model = EnhancedMLModel(look_back_days=60, future_days=3, threshold=0.02)
        
        df = model.fetch_data(ticker, days=500)
        if df is None or len(df) < 200:
            return {"error": f"Not enough data for {ticker}"}
        
        accuracy, stats = model.train(df)
        
        # Save model
        model_path = MODELS_DIR / f"{ticker}_enhanced_model.pkl"
        model.save_model(str(model_path))
        
        # Update cache
        MODELS_CACHE[ticker] = model
        
        return {
            "message": f"Model for {ticker} retrained successfully",
            "accuracy": f"{accuracy:.2%}",
            "stats": stats
        }
    except Exception as e:
        print(f"Error in retrain: {e}")
        return {"error": str(e)}

@app.get("/backtest/{ticker}")
async def backtest(ticker: str, days: int = Query(200, ge=50, le=1000)):
    """Run backtest for a ticker"""
    try:
        model = EnhancedMLModel(look_back_days=60, future_days=3, threshold=0.02)
        
        # Fetch data
        df = model.fetch_data(ticker.upper(), days=days + 200)
        if df is None or len(df) < 100:
            return {"error": f"Not enough data for {ticker}"}
        
        # Engineer features and create labels
        df_featured = model.engineer_features(df)
        df_labeled = model.create_labels(df_featured)
        
        if len(df_labeled) < 50:
            return {"error": "Not enough labeled data for backtest"}
        
        # Split data
        train_size = int(len(df_labeled) * 0.8)
        train_data = df_labeled[:train_size]
        test_data = df_labeled[train_size:]
        
        # Train model
        feature_cols = model.get_feature_columns()
        X_train = train_data[feature_cols]
        y_train = train_data['signal']
        X_test = test_data[feature_cols]
        y_test = test_data['signal']
        
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from collections import Counter
        import numpy as np
        
        rf_model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        gb_model = GradientBoostingClassifier(n_estimators=150, max_depth=7, learning_rate=0.1, random_state=42)
        
        rf_model.fit(X_train, y_train)
        gb_model.fit(X_train, y_train)
        
        # Ensemble predictions
        rf_pred = rf_model.predict(X_test)
        gb_pred = gb_model.predict(X_test)
        
        ensemble_pred = []
        for i in range(len(rf_pred)):
            votes = [rf_pred[i], gb_pred[i]]
            vote_count = Counter(votes)
            ensemble_pred.append(vote_count.most_common(1)[0][0])
        
        accuracy = np.mean(np.array(ensemble_pred) == y_test.values)
        
        # Get recent predictions
        recent_predictions = []
        y_test_array = y_test.values
        for i in range(min(10, len(ensemble_pred))):
            recent_predictions.append({
                "date": y_test.index[i].strftime('%Y-%m-%d'),
                "actual": y_test_array[i],
                "predicted": ensemble_pred[i],
                "correct": y_test_array[i] == ensemble_pred[i]
            })
        
        return {
            "ticker": ticker.upper(),
            "backtest_days": days,
            "accuracy": round(accuracy, 4),
            "accuracy_percentage": f"{accuracy * 100:.1f}%",
            "test_set_size": len(X_test),
            "training_set_size": len(X_train),
            "model_type": "Ensemble (Random Forest + Gradient Boosting)",
            "feature_count": len(feature_cols),
            "last_predicted_signal": ensemble_pred[-1] if ensemble_pred else "HOLD",
            "last_actual_signal": y_test_array[-1] if len(y_test_array) > 0 else "HOLD",
            "recent_predictions": recent_predictions,
            "signal_distribution": dict(y_test.value_counts())
        }
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "MCrypto Enhanced ML Service"}
