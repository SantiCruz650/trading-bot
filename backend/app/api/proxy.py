from fastapi import APIRouter, HTTPException, Request, Response, status
import httpx
from ..core.config import settings

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def ml_service_proxy(path: str, request: Request):
    """Reverse proxy for ML service requests"""
    url = f"/{path}".replace("//", "/")
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header
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
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ML service unreachable: {exc}"
        )
    
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )