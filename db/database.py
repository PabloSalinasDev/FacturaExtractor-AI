import sqlite3
import os
from pathlib import Path

DB_DIR  = Path(os.environ.get("LOCALAPPDATA", ".")) / "PyBloSoft"
DB_PATH = DB_DIR / "facturas.db"


def get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor   TEXT NOT NULL,
                fecha       TEXT NOT NULL,
                monto       REAL NOT NULL,
                moneda      TEXT NOT NULL DEFAULT 'ARS',
                estado      TEXT NOT NULL DEFAULT 'pendiente',
                fuente      TEXT NOT NULL DEFAULT 'PDF',
                archivo     TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()