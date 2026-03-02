# middleware/logging.py
import time
import logging
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from config import settings

logger = logging.getLogger("api")


def mask_sensitive_data(data: str) -> str:
    if not data:
        return ""
    if len(data) > 8:
        return f"{data[:4]}...{data[-4:]}"
    return "***"


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        api_key = request.headers.get("X-API-Key", "")
        masked_key = mask_sensitive_data(api_key) if api_key else "None"

        log_info = {
            "event": "request_started",
            "method": request.method,
            "path": request.url.path,
            "api_key_prefix": masked_key,
        }

        if settings.log_json:
            logger.info(json.dumps(log_info))
        else:
            logger.info(f"{log_info['event']} - {log_info['method']} - {log_info['path']}")

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response