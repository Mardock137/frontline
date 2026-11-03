"""Tests for the centralized logging configuration."""

import logging
from pathlib import Path

from utils.logging_config import setup_logging


def test_setup_logging_creates_file_and_handlers(tmp_path: Path):
    log_file = tmp_path / "backend.log"

    logger = setup_logging(log_level="DEBUG", log_file=log_file)

    try:
        assert logger.level == logging.DEBUG
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert log_file.parent.exists()

        logger.info("hello world")
        for handler in logger.handlers:
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "hello world" in content
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_setup_logging_is_idempotent(tmp_path: Path):
    log_file = tmp_path / "backend.log"

    logger = setup_logging(log_level="INFO", log_file=log_file)
    handlers_after_first = len(logger.handlers)
    logger = setup_logging(log_level="INFO", log_file=log_file)
    handlers_after_second = len(logger.handlers)

    try:
        assert handlers_after_first == handlers_after_second
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_setup_logging_caps_noisy_third_party_loggers_even_at_debug(tmp_path: Path):
    """httpx/httpcore/hpack log raw HTTP headers (incl. secrets) at DEBUG.

    They must stay at WARNING even when the app's own LOG_LEVEL is DEBUG, so
    enabling DEBUG for troubleshooting never writes the Supabase service role
    key or bearer tokens to the log file.
    """
    log_file = tmp_path / "backend.log"

    logger = setup_logging(log_level="DEBUG", log_file=log_file)

    try:
        assert logger.level == logging.DEBUG
        for logger_name in ("httpx", "httpcore", "hpack"):
            assert logging.getLogger(logger_name).level == logging.WARNING
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
