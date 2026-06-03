"""
Единая настройка логирования приложения.

Предоставляет общий механизм конфигурации стандартного ``logging`` для всех
точек входа (desktop, Telegram-бот): единый формат, вывод в консоль и,
опционально, в файл.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Настроить корневой логгер приложения.

    Args:
        level: Уровень логирования ("DEBUG", "INFO", "WARNING", ...).
        log_file: Путь к файлу лога. Если задан — добавляется файловый
            обработчик (каталог создаётся при необходимости).

    Функция идемпотентна: повторные вызовы не добавляют дублирующие
    обработчики одного и того же типа/назначения.
    """
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, str(level).upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(LOG_FORMAT)

    if not _has_console_handler(root_logger):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if log_file:
        _ensure_file_handler(root_logger, log_file, formatter)


def get_logger(name: str) -> logging.Logger:
    """Получить именованный логгер."""
    return logging.getLogger(name)


def _has_console_handler(logger: logging.Logger) -> bool:
    """Проверить наличие консольного обработчика (StreamHandler, не файлового)."""
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(
            handler, logging.FileHandler
        ):
            return True
    return False


def _ensure_file_handler(
    logger: logging.Logger, log_file: str, formatter: logging.Formatter
) -> None:
    """Добавить файловый обработчик, если такого ещё нет."""
    target = Path(log_file).resolve()

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            base_filename = getattr(handler, "baseFilename", None)
            if base_filename and Path(base_filename) == target:
                return

    target.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(target, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
