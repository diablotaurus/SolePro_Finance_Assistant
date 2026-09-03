#!/usr/bin/env python
"""Create a consistent SQLite backup and verify its integrity."""
from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def backup_database(source: Path, destination: Path) -> None:
    """Back up an SQLite database using SQLite's online backup API."""
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Database not found: {source}")
    if source == destination:
        raise ValueError("Backup destination must differ from source database")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    with closing(sqlite3.connect(source)) as source_connection:
        with closing(sqlite3.connect(destination)) as destination_connection:
            source_connection.backup(destination_connection)
            result = destination_connection.execute("PRAGMA integrity_check").fetchone()

    if not result or result[0] != "ok":
        destination.unlink(missing_ok=True)
        detail = result[0] if result else "no result"
        raise RuntimeError(f"SQLite backup integrity check failed: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    backup_database(args.source, args.destination)
    print(args.destination.resolve())


if __name__ == "__main__":
    main()
