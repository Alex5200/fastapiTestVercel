# middleware/rate_limiter.py
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import threading
import redis
from config import settings


class InMemoryRateLimiter:
    """Простой rate limiter в памяти (для разработки)"""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_id: str, max_requests: int, window_seconds: int) -> bool:
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        with self.lock:
            # Очистить старые запросы
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            # Проверить лимит
            if len(self.requests[client_id]) >= max_requests:
                return False

            # Добавить текущий запрос
            self.requests[client_id].append(now)
            return True

    def get_remaining(self, client_id: str, max_requests: int, window_seconds: int) -> int:
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        with self.lock:
            current_count = len([
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ])
            return max(0, max_requests - current_count)


class RedisRateLimiter:
    """Rate limiter с Redis (для продакшена)"""

    def __init__(self, host: str, port: int):
        self.redis = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_connect_timeout=5
        )

    def is_allowed(self, client_id: str, max_requests: int, window_seconds: int) -> bool:
        key = f"rate_limit:{client_id}"

        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()

            current_count = results[0]
            return current_count <= max_requests
        except redis.ConnectionError:
            # Если Redis недоступен, разрешаем запрос (fail-open)
            return True

    def get_remaining(self, client_id: str, max_requests: int, window_seconds: int) -> int:
        key = f"rate_limit:{client_id}"
        try:
            current_count = int(self.redis.get(key) or 0)
            return max(0, max_requests - current_count)
        except redis.ConnectionError:
            return max_requests


# Глобальный лимитер
if settings.use_redis:
    rate_limiter = RedisRateLimiter(settings.redis_host, settings.redis_port)
else:
    rate_limiter = InMemoryRateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """Middleware для rate limiting"""

    if not settings.rate_limit_enabled:
        return await call_next(request)

    # Получаем идентификатор клиента (IP или API ключ)
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        client_id = f"key:{api_key[:16]}"
    else:
        client_id = f"ip:{request.client.host if request.client else 'unknown'}"

    # Проверка лимита
    if not rate_limiter.is_allowed(
            client_id,
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window
    ):
        remaining = rate_limiter.get_remaining(
            client_id,
            settings.rate_limit_requests,
            settings.rate_limit_window
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too Many Requests",
                "message": "Вы превысили лимит запросов. Попробуйте позже.",
                "retry_after": settings.rate_limit_window
            },
            headers={
                "Retry-After": str(settings.rate_limit_window),
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(settings.rate_limit_window)
            }
        )

    # Продолжаем запрос
    response = await call_next(request)

    # Добавляем заголовки о лимитах
    remaining = rate_limiter.get_remaining(
        client_id,
        settings.rate_limit_requests,
        settings.rate_limit_window
    )
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(settings.rate_limit_window)

    return response