"""Настройка логгирования для приложения."""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Настройка логгирования приложения.

    Args:
        level: Уровень логгирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    # Настройка форматирования
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Настройка handler для stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Уменьшаем verbosity для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
