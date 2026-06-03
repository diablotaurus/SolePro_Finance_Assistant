"""
Конфигурация pytest для тестов.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from solepro.infrastructure.database.models import Base
from solepro.infrastructure.database.session_manager import DatabaseSessionManager


@pytest.fixture(scope="session")
def test_database_url():
    """
    URL тестовой базы данных.
    
    Используем SQLite в памяти для тестов.
    """
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(test_database_url):
    """
    Движок тестовой базы данных.
    """
    engine = create_engine(test_database_url)
    
    # Создаем таблицы
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Удаляем таблицы после тестов
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    """
    Сессия базы данных для тестов.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    session_factory = sessionmaker(bind=connection)
    session = session_factory()
    
    yield session
    
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def db_manager(test_database_url):
    """
    Менеджер сессий для тестов.
    """
    manager = DatabaseSessionManager(test_database_url)
    manager.create_tables()
    
    yield manager
    
    manager.drop_tables()
    manager.close()


@pytest.fixture
def test_config():
    """
    Конфигурация для тестов.
    """
    class TestConfig:
        DATABASE_URL = "sqlite:///:memory:"
        DB_ECHO = False
        DB_POOL_SIZE = 5
        DB_MAX_OVERFLOW = 10
        DB_POOL_RECYCLE = 3600
    
    return TestConfig()


@pytest.fixture
def temp_dir():
    """
    Временная директория для тестов.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_transaction_data():
    """
    Пример данных транзакции для тестов.
    """
    from datetime import datetime
    from uuid import uuid4
    
    return {
        "id": uuid4(),
        "date": datetime.now(),
        "income": 1000.0,
        "expense": 500.0,
        "tax": 100.0,
        "counterparty_id": uuid4(),
        "note": "Тестовая транзакция",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def sample_counterparty_data():
    """
    Пример данных контрагента для тестов.
    """
    from uuid import uuid4
    from datetime import datetime
    
    return {
        "id": uuid4(),
        "name": "Тестовый контрагент",
        "description": "Описание тестового контрагента",
        "contact_info": "test@example.com",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
