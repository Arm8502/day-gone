"""database/cache.py - แคชคำแปล (SQLite)"""
import sqlite3

import config


def init_db():
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(config.DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS translations (
                source TEXT PRIMARY KEY,
                translated TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_translation(source):
    with sqlite3.connect(config.DB_PATH) as db:
        row = db.execute(
            "SELECT translated FROM translations WHERE source = ?", (source,)
        ).fetchone()
    return row[0] if row else None


def put_translation(source, translated):
    with sqlite3.connect(config.DB_PATH) as db:
        db.execute(
            "INSERT OR REPLACE INTO translations(source, translated) VALUES(?, ?)",
            (source, translated),
        )
