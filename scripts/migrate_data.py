#!/usr/bin/env python
"""
Скрипт для миграции данных из старой базы в новую.
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from solepro.infrastructure.di import container
from solepro.infrastructure.database.session_manager import get_session_manager


def migrate_from_old_database(old_db_path: Path) -> None:
    """
    Мигрировать данные из старой базы данных.
    
    Args:
        old_db_path: Путь к старой базе данных SQLite
    """
    print(f"🔄 Миграция данных из {old_db_path}")
    
    if not old_db_path.exists():
        print(f"❌ Старая база данных не найдена: {old_db_path}")
        sys.exit(1)
    
    # Подключаемся к старой базе
    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    
    # Подключаемся к новой базе
    session_manager = get_session_manager()
    
    try:
        # Мигрируем контрагентов
        migrate_counterparties(old_conn, session_manager)
        
        # Мигрируем транзакции
        migrate_transactions(old_conn, session_manager)
        
        print("✅ Миграция данных завершена успешно")
        
    except Exception as e:
        print(f"❌ Ошибка миграции данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        old_conn.close()


def migrate_counterparties(old_conn, session_manager) -> None:
    """Мигрировать контрагентов."""
    print("  📋 Миграция контрагентов...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM counterparties")
    
    with session_manager.session() as session:
        from solepro.infrastructure.database.models import CounterpartyModel
        
        for row in cursor.fetchall():
            counterparty = CounterpartyModel(
                id=row['id'] if 'id' in row.keys() else None,
                name=row['name'],
                created_at=datetime.fromisoformat(row['created_at']) if 'created_at' in row.keys() else datetime.now(),
                updated_at=datetime.fromisoformat(row['created_at']) if 'created_at' in row.keys() else datetime.now(),
            )
            
            session.add(counterparty)
        
        session.commit()
    
    print(f"  ✅ Контрагенты мигрированы: {cursor.rowcount} записей")


def migrate_transactions(old_conn, session_manager) -> None:
    """Мигрировать транзакции."""
    print("  📋 Миграция транзакций...")
    
    cursor = old_conn.cursor()
    
    # Старый запрос из database_manager.py
    query = """
    SELECT 
        t.id,
        t.date,
        t.income,
        t.expense,
        t.tax,
        t.note,
        t.created_at,
        c.id as counterparty_id
    FROM transactions t
    LEFT JOIN counterparties c ON t.counterparty_id = c.id
    """
    
    cursor.execute(query)
    
    with session_manager.session() as session:
        from solepro.infrastructure.database.models import TransactionModel
        
        for row in cursor.fetchall():
            # Преобразуем дату
            if isinstance(row['date'], str):
                date = datetime.fromisoformat(row['date'])
            else:
                date = datetime.fromtimestamp(row['date'])
            
            transaction = TransactionModel(
                id=row['id'],
                date=date,
                income=float(row['income']),
                expense=float(row['expense']),
                tax=float(row['tax']),
                note=row['note'],
                counterparty_id=row['counterparty_id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                updated_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            )
            
            session.add(transaction)
        
        session.commit()
    
    print(f"  ✅ Транзакции мигрированы: {cursor.rowcount} записей")


def main() -> None:
    """Основная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Миграция данных из старой базы")
    parser.add_argument(
        "--old-db",
        type=Path,
        default=Path("database/finances.db"),
        help="Путь к старой базе данных SQLite"
    )
    
    args = parser.parse_args()
    
    migrate_from_old_database(args.old_db)


if __name__ == "__main__":
    main()