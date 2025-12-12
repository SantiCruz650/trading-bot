from .auth import router as auth_router
from .predictions import router as predictions_router
from .proxy import router as proxy_router

__all__ = ['auth_router', 'predictions_router', 'proxy_router']
