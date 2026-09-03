"""Quality gates for Windows maintenance scripts."""
from __future__ import annotations

import json
import sqlite3
import tomllib
from contextlib import closing
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
POWERSHELL_SCRIPTS = (
    SCRIPTS_DIR / "common.ps1",
    SCRIPTS_DIR / "setup.ps1",
    SCRIPTS_DIR / "update_prod.ps1",
    SCRIPTS_DIR / "backup_db.ps1",
)


def test_powershell_scripts_are_utf8_without_bom_and_ascii_source() -> None:
    for script_path in POWERSHELL_SCRIPTS:
        content = script_path.read_bytes()
        assert not content.startswith(b"\xef\xbb\xbf"), script_path.name
        decoded = content.decode("utf-8")
        assert decoded.isascii(), script_path.name


def test_russian_messages_catalog_is_valid_utf8_without_bom() -> None:
    catalog_path = SCRIPTS_DIR / "locales" / "messages.ru.json"
    content = catalog_path.read_bytes()
    assert not content.startswith(b"\xef\xbb\xbf")

    catalog = json.loads(content.decode("utf-8"))
    assert catalog["setup_title"].startswith("=== SolePro")
    assert "обновление" in catalog["update_title"]
    assert "резервная копия" in catalog["backup_done"].lower()


def test_sqlite_backup_is_consistent(tmp_path) -> None:
    from scripts.backup_sqlite import backup_database

    source = tmp_path / "source.db"
    destination = tmp_path / "backup" / "copy.db"
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("CREATE TABLE entries (value TEXT NOT NULL)")
        connection.execute("INSERT INTO entries VALUES ('saved')")
        connection.commit()

    backup_database(source, destination)

    with closing(sqlite3.connect(destination)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("SELECT value FROM entries").fetchone() == ("saved",)


def test_setup_script_preserves_existing_environment_file() -> None:
    setup_script = (SCRIPTS_DIR / "setup.ps1").read_text(encoding="utf-8")
    assert 'if (-not (Test-Path -LiteralPath $envPath))' in setup_script
    assert 'Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.example")' in setup_script
    assert '"--no-deps", "-e", $ProjectRoot' in setup_script


def test_ci_uses_node24_actions_and_read_only_permissions() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    assert "actions/checkout@v6" in workflow
    assert "actions/setup-python@v6" in workflow
    assert "contents: read" in workflow


def test_runtime_entrypoints_match_src_layout() -> None:
    dockerfile = (PROJECT_ROOT / "docker" / "app" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    debug_batch = (PROJECT_ROOT / "DebugDesktopApp.bat").read_text(encoding="utf-8")

    assert "FROM python:3.13-slim" in dockerfile
    assert "PYTHONPATH=/app/src" in dockerfile
    assert "scripts/init_db.py" in dockerfile
    assert "scripts\\run_desktop.py" in debug_batch
    assert "desktop/main.py" not in debug_batch
    assert (PROJECT_ROOT / "RunBot.pyw").is_file()


def test_runtime_requirements_match_pyproject() -> None:
    requirements = {
        line.strip().lower()
        for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    pyproject = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    project_dependencies = {
        dependency.lower() for dependency in pyproject["project"]["dependencies"]
    }

    assert requirements == project_dependencies
