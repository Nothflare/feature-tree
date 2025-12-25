# feature_tree/db.py
import sqlite3
import json
from datetime import datetime
from typing import Optional
from pathlib import Path


class FeatureDB:
    def __init__(self, db_path: str = "features.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS features (
                id            TEXT PRIMARY KEY,
                parent_id     TEXT REFERENCES features(id),
                name          TEXT NOT NULL,
                description   TEXT,
                status        TEXT DEFAULT 'planned',
                code_symbols  TEXT,
                files         TEXT,
                technical_notes TEXT,
                commit_ids    TEXT,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS features_fts USING fts5(
                id, name, description, technical_notes,
                content='features',
                content_rowid='rowid'
            );

            CREATE TRIGGER IF NOT EXISTS features_ai AFTER INSERT ON features BEGIN
                INSERT INTO features_fts(id, name, description, technical_notes)
                VALUES (new.id, new.name, new.description, new.technical_notes);
            END;

            CREATE TRIGGER IF NOT EXISTS features_ad AFTER DELETE ON features BEGIN
                INSERT INTO features_fts(features_fts, id, name, description, technical_notes)
                VALUES ('delete', old.id, old.name, old.description, old.technical_notes);
            END;

            CREATE TRIGGER IF NOT EXISTS features_au AFTER UPDATE ON features BEGIN
                INSERT INTO features_fts(features_fts, id, name, description, technical_notes)
                VALUES ('delete', old.id, old.name, old.description, old.technical_notes);
                INSERT INTO features_fts(id, name, description, technical_notes)
                VALUES (new.id, new.name, new.description, new.technical_notes);
            END;
        """)
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()):
        return self.conn.execute(sql, params)

    def close(self):
        self.conn.close()
