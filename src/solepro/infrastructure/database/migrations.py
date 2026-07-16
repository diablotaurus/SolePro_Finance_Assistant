"""
Utilities for running Alembic migrations.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, inspect

from ..config import get_database_config


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
        command.upgrade(config, "head")
        return True
    except Exception as exc:
        # Legacy databases may already have tables created via create_all()
        # without an Alembic version row. In that case, mark schema as current.
        message = str(exc).lower()
        table_exists_error = any(
            token in message
            for token in ("already exists", "duplicate table", "relation")
        )
        if not table_exists_error:
            return False

        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            has_counterparties = inspector.has_table("counterparties")
            has_transactions = inspector.has_table("transactions")
            engine.dispose()
            if has_counterparties and has_transactions:
                command.stamp(config, "head")
                return True
        except Exception:
            return False

        return False
