"""
Desktop приложение SolePro Finance Assistant.
"""
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QLibraryInfo, QTranslator
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ...infrastructure.di import container
from ...infrastructure.config import get_database_config, get_app_config
from ...infrastructure.database.migrations import upgrade_database_to_head
from ...shared.logging_config import setup_logging
from .contracts import (
    DesktopContainerProtocol,
    MainWindowProtocol,
    QtApplicationProtocol,
    SessionManagerProtocol,
    TimerProtocol,
)
from .main_window import MainWindow
from .controllers import MainController, TransactionCoordinator, CounterpartyCoordinator
from .services import TransactionExportService, TransactionExportServiceProtocol
from .styles import apply_style


logger = logging.getLogger(__name__)


class DesktopApplication:
    """
    Основной класс десктопного приложения.
    
    Отвечает за:
    - Инициализацию приложения
    - Настройку Dependency Injection
    - Создание и управление главным окном
    - Управление жизненным циклом приложения
    """
    APP_NAME = "SolePro Finance Assistant"
    ORG_NAME = "SolePro"
    ORG_DOMAIN = "solepro.local"
    ICON_FILENAMES = ("solepro.ico", "solepro.png", "solepro.svg")
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1
    MIGRATION_START_MSG = "🔁 Применение миграций Alembic..."
    MIGRATION_SUCCESS_MSG = "✅ Миграции применены успешно"
    MIGRATION_FALLBACK_MSG = "⚠️ Миграции недоступны, используем create_tables()"
    DB_INIT_MSG = "✅ База данных инициализирована"
    RUN_ERROR_PREFIX = "❌ Ошибка запуска приложения"
    
    def __init__(
        self,
        di_container: DesktopContainerProtocol = container,
        log_writer: Callable[[str], None] = logger.info,
    ):
        """Инициализировать приложение."""
        self.container = di_container
        self.log_writer = log_writer
        self.app: Optional[QtApplicationProtocol] = None
        self.main_window: Optional[MainWindowProtocol] = None
        self.controller: Optional[MainController] = None
        self.session_manager: Optional[SessionManagerProtocol] = None
        self.refresh_timer: Optional[TimerProtocol] = None
        # Ссылка на переводчик Qt: без неё его соберёт сборщик мусора.
        self._qt_translator: Optional[QTranslator] = None
        
    def setup_database(self) -> None:
        """Настроить базу данных."""
        db_config = get_database_config()
        self.session_manager = self.container.session_manager()
        migrated = self._try_run_migrations(
            use_migrations=db_config.use_migrations,
            database_url=getattr(self.session_manager, "database_url", None),
        )

        if not migrated:
            # Fallback для локальной разработки/восстановления.
            self.session_manager.create_tables()
            self._log(self.DB_INIT_MSG)

    def _try_run_migrations(self, use_migrations: bool, database_url: Optional[str]) -> bool:
        """Try to apply Alembic migrations and return True on success."""
        if not use_migrations or not database_url:
            return False
        self._log(self.MIGRATION_START_MSG)
        migrated = upgrade_database_to_head(database_url)
        if migrated:
            self._log(self.MIGRATION_SUCCESS_MSG)
        else:
            self._log(self.MIGRATION_FALLBACK_MSG)
        return migrated
    
    def create_controller(self) -> MainController:
        """Создать контроллер с внедренными зависимостями."""
        return MainController(
            transaction_coordinator=self._build_transaction_coordinator(),
            counterparty_coordinator=self._build_counterparty_coordinator(),
            transaction_export_service=self._build_transaction_export_service(),
        )

    def _build_transaction_coordinator(self) -> TransactionCoordinator:
        """Собрать coordinator для операций с транзакциями."""
        return TransactionCoordinator(
            add_transaction_use_case=self.container.add_transaction_use_case(),
            update_transaction_use_case=self.container.update_transaction_use_case(),
            delete_transaction_use_case=self.container.delete_transaction_use_case(),
            get_transaction_use_case=self.container.get_transaction_use_case(),
            list_transactions_use_case=self.container.list_transactions_use_case(),
            search_transactions_use_case=self.container.search_transactions_use_case(),
            get_transaction_statistics_use_case=self.container.get_transaction_statistics_use_case(),
        )

    def _build_counterparty_coordinator(self) -> CounterpartyCoordinator:
        """Собрать coordinator для операций с контрагентами."""
        return CounterpartyCoordinator(
            add_counterparty_use_case=self.container.add_counterparty_use_case(),
            update_counterparty_use_case=self.container.update_counterparty_use_case(),
            delete_counterparty_use_case=self.container.delete_counterparty_use_case(),
            list_counterparties_use_case=self.container.list_counterparties_use_case(),
            search_counterparties_use_case=self.container.search_counterparties_use_case(),
            get_counterparty_statistics_use_case=self.container.get_counterparty_statistics_use_case(),
        )

    def _build_transaction_export_service(self) -> TransactionExportServiceProtocol:
        """Собрать сервис экспорта транзакций."""
        return TransactionExportService()
    
    def setup_application(self) -> None:
        """Настроить приложение Qt."""
        self.app = self._build_qt_application()
        self._configure_application_metadata(self.app)
        self._install_qt_translations()
        self._apply_app_icon()
        
        # Применяем стили
        apply_style(self.app)
        
        # Создаем контроллер
        self.controller = self.create_controller()
        
        # Создаем главное окно
        self.main_window = self._build_main_window(self.controller)

    def _build_qt_application(self) -> QtApplicationProtocol:
        """Create Qt application instance."""
        return QApplication(sys.argv)

    def _configure_application_metadata(self, app: QtApplicationProtocol) -> None:
        """Configure Qt application metadata."""
        app.setApplicationName(self.APP_NAME)
        app.setOrganizationName(self.ORG_NAME)
        app.setOrganizationDomain(self.ORG_DOMAIN)

    def _build_main_window(self, controller: MainController) -> MainWindow:
        """Create desktop main window."""
        return MainWindow(controller)

    def _install_qt_translations(self) -> None:
        """Русские подписи стандартных кнопок Qt (Да/Нет, Отмена и т.п.).

        Перевод qtbase_ru.qm поставляется вместе с PyQt6. Установка —
        best-effort: если перевод не загрузился, приложение работает
        с английскими подписями стандартных кнопок.
        """
        if self.app is None:
            return
        translator = QTranslator()
        translations_path = QLibraryInfo.path(
            QLibraryInfo.LibraryPath.TranslationsPath
        )
        if translator.load("qtbase_ru", translations_path):
            self.app.installTranslator(translator)
            self._qt_translator = translator
        else:
            logger.warning("Перевод Qt (qtbase_ru) не найден — кнопки останутся английскими")

    def _apply_app_icon(self) -> None:
        """Установить иконку приложения, если файл доступен."""
        if self.app is None:
            return
        for icon_path in self._iter_icon_candidates():
            if icon_path.exists():
                self.app.setWindowIcon(QIcon(str(icon_path)))
                return

    def _iter_icon_candidates(self) -> list[Path]:
        """Return ordered icon candidates for desktop application."""
        project_root = Path(__file__).resolve().parents[4]
        icons_dir = project_root / "icons"
        return [icons_dir / name for name in self.ICON_FILENAMES]
    
    def run(self) -> int:
        """
        Запустить приложение.
        
        Returns:
            Код завершения приложения
        """
        try:
            # Настраиваем базу данных
            self.setup_database()
            
            # Настраиваем приложение
            self.setup_application()
            
            # Показываем главное окно
            self.main_window.show()
            
            # Запускаем главный цикл
            return self.app.exec()
            
        except Exception as e:
            return self._handle_run_error(e)

    def _handle_run_error(self, error: Exception) -> int:
        """Handle startup failure and return process exit code."""
        self._log(f"{self.RUN_ERROR_PREFIX}: {error}")
        self._print_traceback()
        return self.EXIT_FAILURE

    def _log(self, message: str) -> None:
        """Write bootstrap message."""
        self.log_writer(message)

    def _print_traceback(self) -> None:
        """Log traceback for bootstrap errors."""
        logger.exception(self.RUN_ERROR_PREFIX)

    def refresh_data(self) -> None:
        """Обновить данные в главном окне."""
        if self.main_window:
            self.main_window.refresh_data()
    
    def cleanup(self) -> None:
        """Очистка ресурсов при завершении."""
        if self.session_manager:
            self.session_manager.close()
        
        if self.refresh_timer:
            self.refresh_timer.stop()


def main() -> None:
    """Точка входа для десктопного приложения."""
    app_config = get_app_config()
    setup_logging(level=app_config.log_level, log_file=app_config.log_file)
    app = DesktopApplication()
    exit_code = app.run()
    app.cleanup()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
