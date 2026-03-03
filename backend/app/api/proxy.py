from fastapi import APIRouter, HTTPException, Request, Response, status
import httpx
from ..core.config import settings
from ..services.ml_service import ml_service
import json

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ml_service_proxy(path: str, request: Request):
    """Reverse proxy for ML service requests with resiliency fallback"""
    
    # Special handling for metrics to provide mock fallback
    if "metrics" in path and request.method == "GET":
        parts = path.split("/")
        ticker = parts[-1] if parts else "ETH"
        data = await ml_service.get_metrics_async(ticker)
        return data

    # Generic proxy for other paths (retrain, backtest, etc.)
    url = f"/{path}".replace("//", "/")
    full_url = f"{settings.ML_SERVICE_URL}{url}"
    print(f"[Proxy] Llamando al servicio de ML en: {full_url}")
    
    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()
    
    try:
        async with httpx.AsyncClient(base_url=settings.ML_SERVICE_URL, timeout=60.0) as client:
            response = await client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                params=request.query_params,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except Exception as exc:
        # Fallback for ANY ML proxy failure: return HOLD prediction or empty metrics
        logger_warn = f"Proxy to ML failed for {path}: {str(exc)}. Returning safety mock."
        print(logger_warn) # Simple logging for now
        
        if "predict" in path:
            return {"signal": "HOLD", "confidence": 0.5, "status": "proxy_fallback"}
        
        return {"status": "offline", "detail": "ML Service currently unavailable. System operating in safety mode."}