"""
SERENIA ACCOUNTING — config/settings/database.py
====================================================
Standalone database configuration module.

For DEMO purposes: if DATABASE_URL is not set, falls back to a local
SQLite database (db.sqlite3 in the backend/ directory). This lets you
deploy on Render WITHOUT provisioning a separate PostgreSQL instance.

⚠️ SQLite on Render's web service disk is EPHEMERAL — all data
(companies, ledgers, transactions, users) is WIPED on every redeploy
or restart. This is fine for demos but NOT for real usage. For
production, set the DATABASE_URL env var to a real PostgreSQL
connection string and this module will use it automatically.

Usage in production.py:
    from .database import DATABASES
"""

import dj_database_url
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    'default': dj_database_url.config(
        default=config(
            'DATABASE_URL',
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
