#!/usr/bin/env python3
"""Shared helpers for TARDIS deterministic tools."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config" / "tardis_settings.json"
DEFAULT_SCHEMA_PATH = ROOT / "db" / "schema.sql"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_settings(config_path: Path | None = None) -> dict[str, Any]:
    path = config_path or DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_database_path(settings: dict[str, Any]) -> Path:
    db_path = Path(settings["database_path"])
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def connect_database(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def ensure_schema(connection: sqlite3.Connection, schema_path: Path | None = None) -> None:
    path = schema_path or DEFAULT_SCHEMA_PATH
    script = path.read_text(encoding="utf-8")
    connection.executescript(script)
    connection.commit()
