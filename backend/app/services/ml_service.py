import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class MLService:
    """
    Centralized client for ML Service interactions.
    Implements timeouts, retries, and safety mocks.
    """
    
    def __init__(self):
        self.base_url = settings.ML_SERVICE_URL
        self.timeout = 60.0
        self.max_retries = 3
        
        # Safety Mocks (Fallback Data)
        self.DEFAULT_METRICS = {
            "ticker": "ETH",
            "regime": "N/A",
            "volatility": 0.0,
            "accuracy": 0.59,
            "win_rate": 0.55,
            "trend_strength": 0.0,
            "shs": 0,
            "status": "offline_fallback"
        }
        
        self.DEFAULT_PREDICTION = {
            "signal": "HOLD",
            "confidence": 0.5,
            "regime": "N/A",
            "status": "offline_fallback"
        }

    def _sanitize_ticker(self, ticker: str) -> str:
        """Extract base ticker from pair (e.g., 'ETH/USDT' -> 'ETH')"""
        if not ticker:
            return "ETH"
        return ticker.split("/")[0].upper()

    async def get_metrics_async(self, ticker: str) -> Dict[str, Any]:
        """Async fetch for dashboard/proxy"""
        clean_ticker = self._sanitize_ticker(ticker)
        url = f"{self.base_url}/metrics/{clean_ticker}"
        return await self._request_with_retry_async("GET", url, fallback=self.DEFAULT_METRICS)

    async def get_prediction_async(self, ticker: str) -> Dict[str, Any]:
        """Async fetch for predictions API"""
        clean_ticker = self._sanitize_ticker(ticker)
        url = f"{self.base_url}/predict/{clean_ticker}"
        return await self._request_with_retry_async("GET", url, fallback=self.DEFAULT_PREDICTION)

    def get_metrics_sync(self, ticker: str) -> Dict[str, Any]:
        """Sync fetch for StrategyEngine"""
        clean_ticker = self._sanitize_ticker(ticker)
        url = f"{self.base_url}/metrics/{clean_ticker}"
        return self._request_with_retry_sync("GET", url, fallback=self.DEFAULT_METRICS)

    def get_prediction_sync(self, ticker: str) -> Dict[str, Any]:
        """Sync fetch for StrategyEngine logic if needed"""
        clean_ticker = self._sanitize_ticker(ticker)
        url = f"{self.base_url}/predict/{clean_ticker}"
        return self._request_with_retry_sync("GET", url, fallback=self.DEFAULT_PREDICTION)

    async def _request_with_retry_async(self, method: str, url: str, fallback: Any, **kwargs) -> Any:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)
                    if response.status_code == 200:
                        return response.json()
                    logger.warning(f"ML Service returned {response.status_code} for {url} (Attempt {attempt+1})")
            except (httpx.RequestError, asyncio.TimeoutError) as e:
                logger.warning(f"ML Service Request Failed: {str(e)} (Attempt {attempt+1})")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))
        
        logger.error(f"ML Service Unreachable after {self.max_retries} attempts. Returning fallback for {url}")
        return fallback

    def _request_with_retry_sync(self, method: str, url: str, fallback: Any, **kwargs) -> Any:
        import time
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, **kwargs)
                    if response.status_code == 200:
                        return response.json()
                    logger.warning(f"ML Service (Sync) returned {response.status_code} for {url} (Attempt {attempt+1})")
            except (httpx.RequestError) as e:
                logger.warning(f"ML Service (Sync) Request Failed: {str(e)} (Attempt {attempt+1})")
            
            if attempt < self.max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
        
        logger.error(f"ML Service (Sync) Unreachable. Returning fallback for {url}")
        return fallback

# Singleton instance
ml_service = MLService()
