"""
Менеджер сессий базы данных.
"""
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy import event

from ..config import get_database_config


class DatabaseSessionManager:
    """
    Менеджер для управления сессиями базы данных.
    
    Реализует паттерн Unit of Work и обеспечивает правильное
    управление жизненным циклом сессий.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Инициализировать менеджер сессий.
        
        Args:
            database_url: URL базы данных (если None, берется из конфига)
        """
        config = get_database_config()
        self.database_url = database_url or config.url
        
        # Ensure SQLite directory exists to avoid "unable to open database file".
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url[len("sqlite:///"):]
            if db_path and db_path != ":memory:":
                Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

        # Создаем движок
        is_sqlite = "sqlite" in self.database_url
        connect_args = {}
        engine_kwargs = {"echo": config.echo}
        if is_sqlite:
            connect_args["check_same_thread"] = False
            connect_args["timeout"] = 30
        else:
            # Параметры пула применимы только к сетевым СУБД: пул SQLite
            # (в частности, для :memory:) их не принимает.
            engine_kwargs.update(
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_recycle=config.pool_recycle,
            )

        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            **engine_kwargs,
        )

        if "sqlite" in self.database_url:
            @event.listens_for(self.engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                # SQLite по умолчанию не проверяет внешние ключи — без этого
                # ondelete="SET NULL" в схеме не работает.
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.close()
        
        # Создаем фабрику сессий
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Scoped session для использования в разных потоках
        self.scoped_session = scoped_session(self.session_factory)
    
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Контекстный менеджер для работы с сессией.
        
        Гарантирует правильное закрытие сессии и откат транзакции при ошибке.
        
        Yields:
            SQLAlchemy сессия
        """
        session = self.scoped_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self.scoped_session.remove()
    
    def create_tables(self) -> None:
        """Создать все таблицы в базе данных."""
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Удалить все таблицы из базы данных."""
        from .models import Base
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Получить новую сессию.
        
        Внимание: Сессию нужно закрывать вручную!
        Лучше использовать contextmanager session().
        
        Returns:
            SQLAlchemy сессия
        """
        return self.scoped_session()
    
    def close(self) -> None:
        """Закрыть все соединения с базой данных."""
        self.engine.dispose()


# Глобальный экземпляр менеджера сессий
_session_manager: Optional[DatabaseSessionManager] = None


def get_session_manager() -> DatabaseSessionManager:
    """
    Получить глобальный менеджер сессий.
    
    Returns:
        Менеджер сессий базы данных
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager


def create_session_factory(database_url: Optional[str] = None) -> DatabaseSessionManager:
    """
    Создать фабрику сессий.
    
    Args:
        database_url: URL базы данных
        
    Returns:
        Менеджер сессий базы данных
    """
    return DatabaseSessionManager(database_url)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Получить сессию базы данных через контекстный менеджер.
    
    Yields:
        SQLAlchemy сессия
    """
    manager = get_session_manager()
    with manager.session() as session:
        yield session
