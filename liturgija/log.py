"""Datoteka zapisa za modul Liturgija (`liturgija/logs/liturgija.log`)."""
from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / 'logs'
LOG_FILE = LOG_DIR / 'liturgija.log'

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Logger koji piše u `liturgija/logs/liturgija.log` (direktorij se stvara po potrebi)."""
    global _logger
    if _logger is not None:
        return _logger
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('liturgija')
    logger.setLevel(logging.INFO)
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, 'baseFilename', '')) == LOG_FILE
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s',
        ))
        logger.addHandler(handler)
    _logger = logger
    return logger
