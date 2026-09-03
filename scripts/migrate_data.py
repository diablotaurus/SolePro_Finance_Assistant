#!/usr/bin/env python
"""Migrate data from a legacy SQLite database into the configured database."""
from __future__ import annotations

import argparse
import sqlite3
import sys
import traceback
from contextlib import closing
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, NAMESPACE_URL, uuid5

project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from solepro.infrastructure.database.migrations import upgrade_database_to_head
from solepro.infrastructure.database.models import CounterpartyModel, TransactionModel
from solepro.infrastructure.database.session_manager import get_session_manager


def _legacy_uuid(entity_type: str, value: Any) -> UUID:
    """Keep valid UUIDs and map legacy identifiers to deterministic UUIDs."""
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return uuid5(NAMESPACE_URL, f"solepro-legacy:{entity_type}:{value}")


def _parse_datetime(value: Any, default: datetime | None = None) -> datetime:
    if value is None:
        return default or datetime.now()
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    return datetime.fromisoformat(str(value))


def migrate_counterparties(old_connection, session) -> tuple[int, dict[str, UUID]]:
    """Add legacy counterparties to the target unit of work."""
    rows = old_connection.execute("SELECT * FROM counterparties").fetchall()
    id_map: dict[str, UUID] = {}

    for row in rows:
        keys = set(row.keys())
        old_id = row["id"]
        new_id = _legacy_uuid("counterparty", old_id)
        id_map[str(old_id)] = new_id
        created_at = _parse_datetime(row["created_at"] if "created_at" in keys else None)
        session.add(
            CounterpartyModel(
                id=new_id,
                name=row["name"],
                description=row["description"] if "description" in keys else None,
                contact_info=row["contact_info"] if "contact_info" in keys else None,
                created_at=created_at,
                updated_at=_parse_datetime(
                    row["updated_at"] if "updated_at" in keys else None,
                    default=created_at,
                ),
            )
        )

    return len(rows), id_map


def migrate_transactions(old_connection, session, counterparty_ids: dict[str, UUID]) -> int:
    """Add legacy transactions to the same target unit of work."""
    rows = old_connection.execute("SELECT * FROM transactions").fetchall()

    for row in rows:
        keys = set(row.keys())
        old_counterparty_id = row["counterparty_id"] if "counterparty_id" in keys else None
        created_at = _parse_datetime(row["created_at"] if "created_at" in keys else None)
        session.add(
            TransactionModel(
                id=_legacy_uuid("transaction", row["id"]),
                date=_parse_datetime(row["date"]),
                income=Decimal(str(row["income"] or 0)),
                expense=Decimal(str(row["expense"] or 0)),
                tax=Decimal(str(row["tax"] or 0)),
                note=row["note"] if "note" in keys else None,
                counterparty_id=counterparty_ids.get(str(old_counterparty_id)),
                created_at=created_at,
                updated_at=_parse_datetime(
                    row["updated_at"] if "updated_at" in keys else None,
                    default=created_at,
                ),
            )
        )

    return len(rows)


def migrate_from_old_database(old_db_path: Path) -> tuple[int, int]:
    """Migrate all records atomically and return imported row counts."""
    old_db_path = old_db_path.resolve()
    print(f"Migrating data from {old_db_path}")
    if not old_db_path.is_file():
        raise FileNotFoundError(f"Legacy database not found: {old_db_path}")

    session_manager = get_session_manager()
    if not upgrade_database_to_head(session_manager.database_url):
        session_manager.create_tables()

    with closing(sqlite3.connect(old_db_path)) as old_connection:
        old_connection.row_factory = sqlite3.Row
        with session_manager.session() as session:
            counterparty_count, counterparty_ids = migrate_counterparties(
                old_connection, session
            )
            transaction_count = migrate_transactions(
                old_connection, session, counterparty_ids
            )

    print(f"Counterparties migrated: {counterparty_count}")
    print(f"Transactions migrated: {transaction_count}")
    return counterparty_count, transaction_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--old-db",
        type=Path,
        default=Path("database/finances.db"),
        help="Path to the legacy SQLite database",
    )
    args = parser.parse_args()

    try:
        migrate_from_old_database(args.old_db)
    except Exception as exc:
        print(f"Data migration failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
