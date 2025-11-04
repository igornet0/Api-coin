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
        log_level=settings.logging.level.lower(),
        workers=settings.app.workers,
        limit_concurrency=settings.app.limit_concurrency,
    )

