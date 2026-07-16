"""
Конфигурация приложения.
"""
import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла в корне проекта
project_root = Path(__file__).resolve().parents[4]
env_path = project_root / ".env"
load_dotenv(env_path)


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных."""
    url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL", "sqlite:///./data/finances.db"
    ))
    pool_size: int = field(default_factory=lambda: int(os.getenv(
        "DB_POOL_SIZE", "5"
    )))
    max_overflow: int = field(default_factory=lambda: int(os.getenv(
        "DB_MAX_OVERFLOW", "10"
    )))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv(
        "DB_POOL_RECYCLE", "3600"
    )))
    echo: bool = field(default_factory=lambda: os.getenv(
        "DB_ECHO", "False"
    ).lower() == "true")
    use_migrations: bool = field(default_factory=lambda: os.getenv(
        "USE_MIGRATIONS", "True"
    ).lower() == "true")


@dataclass
class TelegramConfig:
    """Конфигурация телеграм бота."""
    bot_token: str = field(default_factory=lambda: os.getenv(
        "TELEGRAM_BOT_TOKEN", ""
    ))
    allowed_users: list[int] = field(default_factory=lambda: [
        int(user_id.strip()) 
        for user_id in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
        if user_id.strip().isdigit()
    ])
    log_level: str = field(default_factory=lambda: os.getenv(
        "TELEGRAM_LOG_LEVEL", "INFO"
    ))
    admin_chat_id: Optional[int] = field(default_factory=lambda: (
        int(os.getenv("TELEGRAM_ADMIN_CHAT_ID"))
        if os.getenv("TELEGRAM_ADMIN_CHAT_ID") and os.getenv("TELEGRAM_ADMIN_CHAT_ID").isdigit()
        else None
    ))
    # Прокси для Telegram (напр. локальный порт Happ/xray). Пусто = напрямую.
    # При недоступности прокси бот автоматически подключается напрямую.
    proxy_url: Optional[str] = field(default_factory=lambda: (
        os.getenv("TELEGRAM_PROXY", "").strip() or None
    ))
    # Явное разрешение доступа всем при пустом TELEGRAM_ALLOWED_USERS
    # (только для разработки). По умолчанию пустой список = доступ закрыт.
    allow_all_users: bool = field(default_factory=lambda: os.getenv(
        "TELEGRAM_ALLOW_ALL", "False"
    ).lower() == "true")


@dataclass
class AppConfig:
    """Основная конфигурация приложения."""
    env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv(
        "APP_DEBUG", "True"
    ).lower() == "true")
    secret_key: str = field(default_factory=lambda: os.getenv(
        "APP_SECRET_KEY", "your-secret-key-change-in-production"
    ))
    currency: str = field(default_factory=lambda: os.getenv("CURRENCY", "RUB"))
    date_format: str = field(default_factory=lambda: os.getenv("DATE_FORMAT", "%d.%m.%Y"))
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Europe/Moscow"))
    
    # Настройки бэкапа
    enable_auto_backup: bool = field(default_factory=lambda: os.getenv(
        "ENABLE_AUTO_BACKUP", "True"
    ).lower() == "true")
    backup_path: str = field(default_factory=lambda: os.getenv(
        "BACKUP_PATH", "./backups"
    ))
    backup_retention_days: int = field(default_factory=lambda: int(os.getenv(
        "BACKUP_RETENTION_DAYS", "30"
    )))
    
    # Настройки экспорта
    export_path: str = field(default_factory=lambda: os.getenv(
        "EXPORT_PATH", "./exports"
    ))
    export_max_rows: int = field(default_factory=lambda: int(os.getenv(
        "EXPORT_MAX_ROWS", "10000"
    )))
    
    # Безопасность
    encryption_key: str = field(default_factory=lambda: os.getenv(
        "ENCRYPTION_KEY", "your-encryption-key-change-in-production"
    ))
    enable_data_encryption: bool = field(default_factory=lambda: os.getenv(
        "ENABLE_DATA_ENCRYPTION", "False"
    ).lower() == "true")
    
    # Логирование
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/app.log"))


def get_database_config() -> DatabaseConfig:
    """Получить конфигурацию БД."""
    config = DatabaseConfig()
    if config.url.startswith("sqlite:///./"):
        relative_path = config.url[len("sqlite:///./"):]
        absolute_path = (project_root / relative_path).resolve()
        config.url = f"sqlite:///{absolute_path.as_posix()}"
    return config


def get_telegram_config() -> TelegramConfig:
    """Получить конфигурацию телеграм бота."""
    return TelegramConfig()


def get_app_config() -> AppConfig:
    """Получить конфигурацию приложения."""
    return AppConfig()
