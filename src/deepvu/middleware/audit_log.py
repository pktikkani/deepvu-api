import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("deepvu.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_id": getattr(request.state, "user_id", None),
            "tenant_id": getattr(request.state, "tenant_id", None),
            "client_ip": request.client.host if request.client else None,
        }

        logger.info(json.dumps(log_data))
        return response
