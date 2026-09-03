#!/usr/bin/env python
"""
Скрипт для инициализации базы данных.
"""
import os
import sys
from pathlib import Path

# Добавляем src в путь, чтобы импортировать пакет solepro
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from solepro.infrastructure.config import get_database_config
from solepro.infrastructure.di import container
from solepro.infrastructure.database.migrations import upgrade_database_to_head
from solepro.infrastructure.database.repositories import SQLAlchemyCounterpartyRepository
from solepro.core.domain.entities.counterparty import Counterparty


DEFAULT_COUNTERPARTIES: tuple[str, ...] = (
    "Прочее",
    "Налоги и сборы",
    "Банковские комиссии",
)


def _get_initial_counterparties() -> list[str]:
    raw = os.getenv("INITIAL_COUNTERPARTIES", "")
    if not raw.strip():
        return list(DEFAULT_COUNTERPARTIES)

    result: list[str] = []
    for name in raw.split(","):
        cleaned = name.strip()
        if cleaned:
            result.append(cleaned)
    return result or list(DEFAULT_COUNTERPARTIES)


def seed_initial_data() -> dict[str, int]:
    """
    Заполнить начальные данные в существующие таблицы.

    Сейчас проект содержит только counterparties/transactions, поэтому seed
    выполняется для контрагентов.
    """
    session_manager = container.session_manager()
    session = session_manager.get_session()
    created = 0
    skipped = 0
    try:
        repository = SQLAlchemyCounterpartyRepository(session)
        for name in _get_initial_counterparties():
            if repository.exists_by_name(name):
                skipped += 1
                continue
            repository.save(Counterparty(name=name))
            created += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        scoped_session = getattr(session_manager, "scoped_session", None)
        if scoped_session is not None:
            scoped_session.remove()

    return {"created": created, "skipped": skipped}


def init_database() -> None:
    """
    Инициализировать базу данных.
    
    Создает таблицы, добавляет начальные данные если нужно.
    """
    print("🔧 Инициализация базы данных...")
    
    db_config = get_database_config()

    # Получаем менеджер сессий из контейнера
    session_manager = container.session_manager()
    
    try:
        migrated = False
        if db_config.use_migrations:
            print("🔁 Применяем миграции Alembic...")
            migrated = upgrade_database_to_head(
                database_url=getattr(session_manager, "database_url", None)
            )
            if migrated:
                print("✅ Миграции применены успешно")
            else:
                print("⚠️ Миграции недоступны, используем create_tables()")

        if not migrated:
            # Fallback для локальной разработки и аварийного восстановления.
            session_manager.create_tables()
            print("✅ Таблицы созданы успешно")
        
        seed_result = seed_initial_data()
        print(
            "✅ Начальные данные добавлены: "
            f"создано {seed_result['created']}, пропущено {seed_result['skipped']}"
        )
        
        print("✅ База данных инициализирована успешно")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
