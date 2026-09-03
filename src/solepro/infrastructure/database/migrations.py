"""
Utilities for running Alembic migrations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, inspect

from ...shared.exceptions import MigrationException
from ..config import get_database_config


_INITIAL_SCHEMA_REVISION = "20260213_0001"
_DOMAIN_TABLES = frozenset({"counterparties", "transactions"})


def _prepare_legacy_database(config, command, database_url: str) -> None:
    """Stamp a complete pre-Alembic schema at its real baseline revision."""
    engine = create_engine(database_url)
    try:
        table_names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    if "alembic_version" in table_names:
        return

    existing_domain_tables = table_names & _DOMAIN_TABLES
    if not existing_domain_tables:
        return
    if existing_domain_tables != _DOMAIN_TABLES:
        missing = ", ".join(sorted(_DOMAIN_TABLES - existing_domain_tables))
        raise MigrationException(
            f"Обнаружена неполная схема БД без Alembic. Отсутствуют таблицы: {missing}"
        )

    command.stamp(config, _INITIAL_SCHEMA_REVISION)


def upgrade_database_to_head(database_url: Optional[str] = None) -> bool:
    """
    Upgrade database schema to the latest Alembic revision.

    Returns True when migrations were executed successfully, otherwise False.
    """
    try:
        from alembic import command
        from alembic.config import Config
    except Exception:
        return False

    project_root = Path(__file__).resolve().parents[4]
    alembic_ini = project_root / "alembic.ini"
    if not alembic_ini.exists():
        return False

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(project_root / "alembic"))
    db_url = database_url or get_database_config().url
    config.set_main_option("sqlalchemy.url", db_url)
    # env.py сам определяет URL из конфига приложения; передаём явный URL
    # через attributes, иначе параметр database_url игнорировался бы.
    config.attributes["sqlalchemy_url_override"] = db_url

    try:
        _prepare_legacy_database(config, command, db_url)
        command.upgrade(config, "head")
        return True
    except MigrationException:
        raise
    except Exception as exc:
        raise MigrationException(f"Не удалось применить миграции БД: {exc}") from exc
