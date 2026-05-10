import aiosqlite
import os
from contextlib import asynccontextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", "./iron_oracle.db")

CREATE_TABLES_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS machine_cache (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    image_hash    TEXT UNIQUE NOT NULL,
    make          TEXT,
    model         TEXT,
    serial_number TEXT,
    year          INTEGER,
    capacity      TEXT,
    voltage       TEXT,
    other_ids     TEXT,
    confidence    REAL,
    notes         TEXT,
    raw_response  TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS manual_cache (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key     TEXT UNIQUE NOT NULL,
    results_json  TEXT NOT NULL,
    result_count  INTEGER,
    search_status TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    expires_at    TEXT DEFAULT (datetime('now', '+30 days'))
);

CREATE TABLE IF NOT EXISTS torque_cache (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    manual_url         TEXT UNIQUE NOT NULL,
    make               TEXT,
    model              TEXT,
    specs_json         TEXT NOT NULL,
    spec_count         INTEGER,
    pdf_page_count     INTEGER,
    extraction_method  TEXT,
    created_at         TEXT DEFAULT (datetime('now')),
    expires_at         TEXT DEFAULT (datetime('now', '+90 days'))
);

CREATE TABLE IF NOT EXISTS scan_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_ocr       TEXT NOT NULL,
    make          TEXT,
    model         TEXT,
    serial_number TEXT,
    year          INTEGER,
    confidence    REAL,
    cached        INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_machine_hash  ON machine_cache(image_hash);
CREATE INDEX IF NOT EXISTS idx_manual_key    ON manual_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_torque_url    ON torque_cache(manual_url);
CREATE INDEX IF NOT EXISTS idx_scan_log_time ON scan_log(created_at);
"""


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
