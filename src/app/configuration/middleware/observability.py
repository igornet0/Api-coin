import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.configuration.monitoring.metrics import request_counter, request_latency_seconds


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            endpoint = request.url.path
            method = request.method
            status = response.status_code if response is not None else 500
            request_counter.labels(method=method, endpoint=endpoint, status=status).inc()
            duration = time.perf_counter() - start
            request_latency_seconds.labels(endpoint=endpoint, method=method).observe(duration)


