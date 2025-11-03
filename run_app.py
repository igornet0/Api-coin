#!/usr/bin/env python
"""
Скрипт для запуска FastAPI приложения
"""
import uvicorn

from src.core import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.reload,
        log_level=settings.logging.level,
        workers=settings.app.workers,
        timeout=settings.app.timeout,
        limit_concurrency=settings.app.limit_concurrency,
        limit_max_requests=settings.app.limit_max_requests,
        limit_max_requests_jitter=settings.app.limit_max_requests_jitter,
        limit_max_requests_jitter_backoff=settings.app.limit_max_requests_jitter_backoff,
        limit_max_requests_jitter_backoff_factor=settings.app.limit_max_requests_jitter_backoff_factor,
    )

