# services/api/app/db/mysql.py
"""
Database connection utilities.

The original specification mandates MySQL with connection pooling. To ease local
development and automated testing, we also support SQLite by switching the
`DB_DIALECT` environment variable (defaults to `mysql`). This module exposes a
single `get_connection()` helper consumed by all repositories.
"""

from __future__ import annotations

import csv
import shutil
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from services.api.app.config import (
    DB_DIALECT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    SQLITE_PATH as CONFIG_SQLITE_PATH,
)

_pool = None  # type: ignore[assignment]
_SQLITE_PATH = CONFIG_SQLITE_PATH
ROOT_DIR = Path(__file__).resolve().parents[4]
_SQLITE_TEMPLATE_CANDIDATES = [
    ROOT_DIR / "infra" / "mysql_init" / "work_allocation.db",
    ROOT_DIR / "infra" / "mysql_init" / "demo_work_allocation.db",
    ROOT_DIR / "notebooks" / "demo_work_allocation.db",
]
SCHEMA_PATH = ROOT_DIR / "infra" / "mysql_init" / "schema.sql"
CSV_SOURCES = {
    "resources": ROOT_DIR / "infra" / "mysql_init" / "resources.csv",
    "resource_calendar": ROOT_DIR / "infra" / "mysql_init" / "resource_calendar.csv",
    "specialty_mapping": ROOT_DIR / "infra" / "mysql_init" / "specialty_mapping.csv",
    "work_requests": ROOT_DIR / "infra" / "mysql_init" / "work_requests.csv",
}

if DB_DIALECT == "mysql":
    import mysql.connector  # type: ignore
    from mysql.connector import pooling  # type: ignore

    # Create a reusable connection pool for the API+agents
    _pool = pooling.MySQLConnectionPool(
        pool_name="work_pool",
        pool_size=6,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        autocommit=False,
    )
else:
    # Lazy import only when needed to avoid sqlite dependency for strict MySQL environments
    import os

    if not _SQLITE_PATH:
        _SQLITE_PATH = os.path.join("infra", "mysql_init", "work_allocation.db")


def _ensure_sqlite_db():
    path = Path(_SQLITE_PATH)
    if path.exists():
        if _sqlite_schema_current(path):
            return
        path.unlink()  # remove outdated db
    path.parent.mkdir(parents=True, exist_ok=True)
    for candidate in _SQLITE_TEMPLATE_CANDIDATES:
        if candidate.exists() and _sqlite_schema_current(candidate):
            shutil.copy2(candidate, path)
            return
    _bootstrap_sqlite_db(path)


def _sqlite_schema_current(path: Path) -> bool:
    """
    Minimal schema validation to detect outdated ad-hoc SQLite files.
    Ensures critical columns such as work_requests.scheduled_timestamp exist.
    """
    try:
        conn = sqlite3.connect(path)
        cur = conn.execute("PRAGMA table_info(work_requests)")
        columns = {row[1] for row in cur.fetchall()}
        cur.close()
        conn.close()
        return "scheduled_timestamp" in columns
    except Exception:
        return False


def _bootstrap_sqlite_db(path: Path):
    """
    Create a SQLite database from schema + CSV fixtures when a template DB is missing.
    Ensures tests/dev setups always have a consistent dataset.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    conn = sqlite3.connect(path)
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = "\n".join(
                line
                for line in f.readlines()
                if not line.strip().upper().startswith("USE ")
            )
            conn.executescript(schema_sql)

        def load_csv(table: str, columns: Iterable[str]):
            csv_path = CSV_SOURCES.get(table)
            if not csv_path or not csv_path.exists():
                return
            with open(csv_path, "r", encoding="utf-8") as cf:
                reader = csv.DictReader(cf)
                rows = [
                    tuple(row[col] if row[col] != "" else None for col in columns)
                    for row in reader
                ]
                if not rows:
                    return
                placeholders = ",".join(["?"] * len(columns))
                conn.executemany(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    rows,
                )

        load_csv(
            "resources",
            ["resource_id", "name", "specialty", "skill_level", "total_cases_handled"],
        )
        load_csv(
            "resource_calendar",
            [
                "calendar_id",
                "resource_id",
                "date",
                "available_from",
                "available_to",
                "current_workload",
            ],
        )
        load_csv(
            "specialty_mapping",
            ["work_type", "required_specialty", "alternate_specialty"],
        )
        load_csv(
            "work_requests",
            [
                "work_id",
                "work_type",
                "description",
                "priority",
                "scheduled_timestamp",
                "status",
                "assigned_to",
            ],
        )

        conn.commit()
    finally:
        conn.close()


def get_connection():
    """
    Returns a database connection object.
    """
    if DB_DIALECT == "mysql":
        if _pool is None:
            raise RuntimeError("MySQL pool not initialized")
        return _pool.get_connection()

    # SQLite fallback (mostly for development/unit tests). We open a new
    # connection per call and rely on sqlite's lightweight nature.
    _ensure_sqlite_db()
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
