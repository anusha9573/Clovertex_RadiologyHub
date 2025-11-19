from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def sqlite_database(tmp_path_factory, monkeypatch):
    """
    Configure the project to use a temporary SQLite database seeded from the
    standard infra/mysql_init fixtures. The runtime bootstrap in
    services.api.app.db.mysql will create and seed the DB when first accessed.
    """

    db_path = tmp_path_factory.mktemp("db") / "work_allocation.db"
    monkeypatch.setenv("DB_DIALECT", "sqlite")
    monkeypatch.setenv("SQLITE_PATH", str(db_path))

    from services.api.app import config as config_module
    from services.api.app.db import mysql as mysql_module
    from services.api.app.db import repositories as repositories_module

    importlib.reload(config_module)
    importlib.reload(mysql_module)
    importlib.reload(repositories_module)

    yield

