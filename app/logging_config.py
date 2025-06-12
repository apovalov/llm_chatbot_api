"""Logging configuration for the application."""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    """Setup application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    # Setup formatting
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce verbosity for external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
