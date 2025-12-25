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

    def add_feature(
        self,
        id: str,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "planned"
    ) -> dict:
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO features (id, parent_id, name, description, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, parent_id, name, description, status, now, now)
        )
        self.conn.commit()
        return self.get_feature(id)

    def get_feature(self, id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM features WHERE id = ?", (id,)
        ).fetchone()
        return dict(row) if row else None

    def update_feature(self, id: str, **fields) -> Optional[dict]:
        if not fields:
            return self.get_feature(id)

        # Convert lists to JSON
        for key in ["code_symbols", "files", "commit_ids"]:
            if key in fields and isinstance(fields[key], list):
                fields[key] = json.dumps(fields[key])

        fields["updated_at"] = datetime.utcnow().isoformat()

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [id]

        self.conn.execute(
            f"UPDATE features SET {set_clause} WHERE id = ?",
            values
        )
        self.conn.commit()
        return self.get_feature(id)

    def delete_feature(self, id: str) -> Optional[dict]:
        return self.update_feature(id, status="deleted")
