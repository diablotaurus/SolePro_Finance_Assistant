"""
Основной класс Telegram бота.
"""
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

from telegram import Update, ReplyKeyboardMarkup
from telegram.error import NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

from ...infrastructure.di import container
from ...infrastructure.config import get_telegram_config
from ...shared.logging_config import setup_logging as configure_logging
from .handlers import setup_handlers, HandlerDependencies
from .middlewares import AccessMiddleware


# Порты прокси по умолчанию, если в URL порт не указан явно.
_DEFAULT_PROXY_PORTS = {
    "socks5": 1080,
    "socks5h": 1080,
    "socks4": 1080,
    "http": 8080,
    "https": 8080,
}


def is_proxy_reachable(proxy_url: str, timeout: float = 2.0) -> bool:
    """
    Проверить, доступен ли прокси (слушается ли его host:port).

    Используется для «мягкого» прокси: если локальный прокси (например,
    порт Happ/xray) выключен, порт не слушается — тогда бот подключается
    к Telegram напрямую, а не падает.

    Args:
        proxy_url: URL прокси, напр. "socks5://192.168.0.8:10808".
        timeout: Таймаут TCP-подключения в секундах.

    Returns:
        True, если TCP-соединение с прокси установилось; иначе False.
    """
    if not proxy_url:
        return False
    try:
        parsed = urlparse(proxy_url)
    except (ValueError, AttributeError):
        return False
    host = parsed.hostname
    if not host:
        return False
    port = parsed.port or _DEFAULT_PROXY_PORTS.get((parsed.scheme or "").lower())
    if not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _proxy_log_target(proxy_url: str) -> str:
    """Return a proxy endpoint safe for logs (without credentials)."""
    try:
        parsed = urlparse(proxy_url)
        host = parsed.hostname or "unknown-host"
        port = parsed.port or _DEFAULT_PROXY_PORTS.get((parsed.scheme or "").lower())
        endpoint = f"{parsed.scheme or 'proxy'}://{host}"
        return f"{endpoint}:{port}" if port else endpoint
    except (ValueError, AttributeError):
        return "invalid-proxy-url"


class TelegramBot:
    """
    Telegram бот для учета финансов.
    
    Отвечает за:
    - Инициализацию бота
    - Настройку обработчиков
    - Управление жизненным циклом бота
    """
    
    def __init__(self):
        """Инициализировать бота."""
        self.config = get_telegram_config()
        self.application: Optional[Application] = None
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Проверяем конфигурацию
        if not self.config.bot_token:
            raise ValueError("Токен бота не указан в конфигурации")
    
    def setup_logging(self) -> None:
        """Настроить логирование."""
        configure_logging(level=self.config.log_level, log_file=self.config.log_file)
    
    async def post_init(self, application: Application) -> None:
        """
        Функция, вызываемая после инициализации бота.
        
        Args:
            application: Приложение бота
        """
        self.logger.info("✅ Бот запущен и готов к работе!")
        
        # Выводим информацию о настройках
        self.logger.info("=" * 50)
        self.logger.info("SolePro Finance Assistant (Telegram Bot) запущен!")
        self.logger.info("👤 Разрешенные пользователи: %s", self.config.allowed_users)

        if self.config.admin_chat_id:
            self.logger.info("👑 Администратор: %s", self.config.admin_chat_id)

        self.logger.info("=" * 50)
        
        # Отправляем сообщение администратору
        keyboard = ReplyKeyboardMarkup([["Добавить", "Статистика"]], resize_keyboard=True)
        recipients = []
        if self.config.admin_chat_id:
            recipients.append(self.config.admin_chat_id)
        recipients.extend(self.config.allowed_users or [])

        for chat_id in set(recipients):
            try:
                await application.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Бот запущен и готов к работе!",
                    reply_markup=keyboard
                )
            except Exception as e:
                self.logger.exception(
                    "Не удалось отправить сообщение пользователю %s: %s", chat_id, e
                )
    
    def setup_application(self) -> None:
        """Настроить приложение бота."""
        # Создаем приложение
        builder = (
            Application.builder()
            .token(self.config.bot_token)
            .post_init(self.post_init)
        )

        # Прокси (например, локальный порт Happ/xray). Если прокси задан, но
        # недоступен, — подключаемся напрямую, чтобы бот не падал.
        proxy_url = self.config.proxy_url
        if proxy_url:
            proxy_target = _proxy_log_target(proxy_url)
            if is_proxy_reachable(proxy_url):
                builder = builder.proxy(proxy_url).get_updates_proxy(proxy_url)
                self.logger.info("🌐 Telegram через прокси: %s", proxy_target)
            else:
                self.logger.warning(
                    "⚠️ Прокси %s недоступен — подключение напрямую", proxy_target
                )

        self.application = builder.build()
        
        # Добавляем middleware для проверки доступа
        if not self.config.allowed_users:
            if self.config.allow_all_users:
                self.logger.warning(
                    "⚠️ TELEGRAM_ALLOW_ALL=True — бот доступен ВСЕМ пользователям!"
                )
            else:
                self.logger.warning(
                    "⚠️ TELEGRAM_ALLOWED_USERS пуст — доступ к боту закрыт для всех. "
                    "Укажите ID пользователей или TELEGRAM_ALLOW_ALL=True (для разработки)."
                )
        self.application.add_handler(
            AccessMiddleware(
                allowed_users=self.config.allowed_users,
                allow_all=self.config.allow_all_users,
            )
        )
        
        # Настраиваем обработчики
        dependencies = HandlerDependencies(
            get_transaction_statistics_use_case=container.get_transaction_statistics_use_case,
            list_counterparties_use_case=container.list_counterparties_use_case,
            add_transaction_use_case=container.add_transaction_use_case,
            list_transactions_use_case=container.list_transactions_use_case,
            search_transactions_use_case=container.search_transactions_use_case,
            get_counterparty_statistics_use_case=container.get_counterparty_statistics_use_case,
        )
        setup_handlers(self.application, dependencies=dependencies)
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Optional[Update], context) -> None:
        """
        Обработчик ошибок бота.
        
        Args:
            update: Обновление
            context: Контекст
        """
        error = context.error
        if update is None and isinstance(error, NetworkError):
            self.logger.warning(
                "Временная сетевая ошибка Telegram polling; "
                "библиотека повторит запрос автоматически: %s",
                error,
            )
            return

        self.logger.error(
            "Ошибка при обработке обновления: %s",
            error,
            exc_info=(type(error), error, error.__traceback__) if error else None,
        )
        
        # Отправляем сообщение об ошибке пользователю
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Произошла ошибка при обработке вашего запроса. "
                         "Попробуйте позже или обратитесь к администратору."
                )
            except Exception as e:
                self.logger.exception("Не удалось отправить сообщение об ошибке: %s", e)
        
        # Отправляем сообщение администратору
        if self.config.admin_chat_id:
            try:
                error_message = (
                    f"🚨 Ошибка в боте:\n\n"
                    f"Ошибка: {context.error}\n"
                )
                
                if update and update.effective_user:
                    error_message += f"Пользователь: {update.effective_user.username} ({update.effective_user.id})\n"
                
                if update and update.effective_message:
                    error_message += f"Сообщение: {update.effective_message.text}\n"
                
                await context.bot.send_message(
                    chat_id=self.config.admin_chat_id,
                    text=error_message[:4000]  # Ограничение Telegram
                )
            except Exception as e:
                self.logger.exception(
                    "Не удалось отправить сообщение администратору об ошибке: %s", e
                )
    
    def run(self) -> None:
        """Запустить бота."""
        try:
            self.logger.info("Запуск бота...")
            
            # Настраиваем приложение
            self.setup_application()
            
            # Запускаем бота. Подписываемся только на message: обработчиков
            # callback_query/inline_query нет — при их появлении расширить.
            self.application.run_polling(
                allowed_updates=['message'],
                drop_pending_updates=True,
                timeout=30,
            )
            
        except Exception as e:
            self.logger.exception("Ошибка запуска бота: %s", e)
            raise
    
    def stop(self) -> None:
        """Остановить бота."""
        if self.application:
            self.application.stop()
            self.logger.info("Бот остановлен")


def main() -> None:
    """Точка входа для Telegram бота."""
    bot = TelegramBot()
    bot.run()


if __name__ == '__main__':
    main()
