from fastapi import APIRouter, HTTPException, Request, Response, status
import httpx
from ..core.config import settings
from ..services.ml_service import ml_service
import json

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ml_service_proxy(path: str, request: Request):
    """Reverse proxy for ML service requests with resiliency fallback"""
    
    # List of endpoints that expect a sanitized ticker (e.g., 'ETH' instead of 'ETH/USDT')
    sanitized_endpoints = ["metrics", "predict", "backtest", "retrain"]
    
    parts = path.strip("/").split("/")
    if parts and parts[0] in sanitized_endpoints:
        base_endpoint = parts[0]
        # Ticker is usually the second part: 'predict/ETH/USDT' -> parts[1] is 'ETH'
        ticker = parts[1] if len(parts) > 1 else "ETH"
        # Aggressive cleaning: split by any common separator and take the first part
        clean_ticker = ticker.replace("-", "/").split("/")[0].upper()
        
        # Rewrite the URL for the request
        url = f"/{base_endpoint}/{clean_ticker}"
        print(f"[Proxy] Sanitizing request: {path} -> {url}")
        
    # Direct integration logic for Reverse Proxy
    try:
        if base_endpoint == "metrics" and request.method == "GET":
            return await ml_service.get_metrics_async(clean_ticker)
        
        if base_endpoint == "predict" and request.method == "GET":
            return await ml_service.get_prediction_async(clean_ticker)

        # For backtest, retrain, and history, try direct import from ml_service.app.main
        from ml_service.app.main import run_full_backtest, retrain_model, get_history
        
        if base_endpoint == "backtest":
             days = int(request.query_params.get("days", 100))
             return await run_full_backtest(clean_ticker, days=days)
        
        if base_endpoint == "retrain":
             return await retrain_model(clean_ticker)
             
        if base_endpoint == "history":
             days = int(request.query_params.get("days", 365))
             return await get_history(clean_ticker, days=days)

        # Default fallback for unknown endpoints handled by proxy
        return {"status": "offline_fallback", "message": f"Endpoint {path} not natively supported in direct mode."}

    except Exception as exc:
        print(f"[Proxy] Direct integration failed for {path}: {exc}")
        if "predict" in path:
            return {"signal": "HOLD", "confidence": 0.5, "status": "proxy_fallback"}
        return {"status": "offline", "detail": "ML Logic currently unavailable. System operating in safety mode."}