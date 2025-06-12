import logging
import time
from typing import Callable

import psutil
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик производительности."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Начальные метрики
        start_time = time.perf_counter()
        process = psutil.Process()

        # Память и CPU до запроса
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()

        # Обработка запроса
        response = await call_next(request)

        # Финальные метрики
        end_time = time.perf_counter()
        process_time = end_time - start_time

        # Память и CPU после запроса
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        cpu_after = process.cpu_percent()

        # Логирование метрик
        logger.info(
            f"🚀 PERFORMANCE METRICS - "
            f"Method: {request.method} | "
            f"Path: {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.4f}s | "
            f"Memory: {memory_before:.1f}→{memory_after:.1f}MB "
            f"(Δ{memory_after - memory_before:+.1f}) | "
            f"CPU: {cpu_before:.1f}%→{cpu_after:.1f}%"
        )

        # Добавление метрик в заголовки ответа
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["X-Memory-Used"] = str(round(memory_after, 1))
        response.headers["X-Memory-Delta"] = str(round(memory_after - memory_before, 1))

        return response
