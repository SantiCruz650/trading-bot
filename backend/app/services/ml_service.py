import logging
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings

# Add the project root to sys.path to reach ml_service and shared
root_path = str(Path(__file__).resolve().parents[3])
if root_path not in sys.path:
    sys.path.append(root_path)

logger = logging.getLogger(__name__)

class MLService:
    """
    Direct Python integration for ML Service.
    Eliminates internal HTTP calls (404/Connection Refused) on Render.
    """
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        
        # Lazy imports to avoid circular dependencies and overhead
        self._predict_func = None
        self._get_metrics_func = None
        
        # Safety Mocks (Fallback Data)
        self.DEFAULT_METRICS = {
            "ticker": "ETH",
            "regime": "N/A",
            "volatility": 0.0,
            "accuracy": 0.59,
            "win_rate": 0.55,
            "trend_strength": 0.0,
            "shs": 0,
            "status": "direct_import"
        }
        
        self.DEFAULT_PREDICTION = {
            "signal": "HOLD",
            "confidence": 0.5,
            "regime": "N/A",
            "status": "direct_import"
        }

    def _ensure_imported(self):
        if self._predict_func is None:
            try:
                from ml_service.app.main import predict, get_metrics
                self._predict_func = predict
                self._get_metrics_func = get_metrics
                logger.info("✅ ML Logic fused directly into Backend Service.")
            except ImportError as e:
                logger.error(f"❌ Failed to import ML logic: {e}")

    def _sanitize_ticker(self, ticker: str) -> str:
        """Extract base ticker from pair (e.g., 'ETH/USDT' -> 'ETH')"""
        if not ticker:
            return "ETH"
        return ticker.split("/")[0].upper()

    async def get_metrics_async(self, ticker: str) -> Dict[str, Any]:
        """Direct call to ML logic"""
        self._ensure_imported()
        if not self._get_metrics_func:
            return self.DEFAULT_METRICS
        
        try:
            clean_ticker = self._sanitize_ticker(ticker)
            return await self._get_metrics_func(clean_ticker)
        except Exception as e:
            logger.error(f"ML Metrics Logic Error: {e}")
            return self.DEFAULT_METRICS

    async def get_prediction_async(self, ticker: str) -> Dict[str, Any]:
        """Direct call to ML logic"""
        self._ensure_imported()
        if not self._predict_func:
            return self.DEFAULT_PREDICTION
        
        try:
            clean_ticker = self._sanitize_ticker(ticker)
            return await self._predict_func(clean_ticker)
        except Exception as e:
            logger.error(f"ML Prediction Logic Error: {e}")
            return self.DEFAULT_PREDICTION

    def get_metrics_sync(self, ticker: str) -> Dict[str, Any]:
        """Wrapper for sync contexts if needed"""
        return asyncio.run(self.get_metrics_async(ticker))

    def get_prediction_sync(self, ticker: str) -> Dict[str, Any]:
        """Wrapper for sync contexts if needed"""
        return asyncio.run(self.get_prediction_async(ticker))

# Singleton instance
ml_service = MLService()

# Singleton instance
ml_service = MLService()
