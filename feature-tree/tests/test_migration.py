# tests/test_migration.py
"""Test v2→v3 migration."""
import json
import os
import sqlite3
import tempfile
from feature_tree.db import FeatureDB


def test_migrate_status_in_progress():
    """in_progress → active + being_modified=building"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")

        # Create v2 database manually
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planned',
                code_symbols TEXT,
                files TEXT,
                technical_notes TEXT,
                commit_ids TEXT,
                uses TEXT,
                confidence TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO features (id, name, status)
            VALUES ('test', 'Test Feature', 'in_progress')
        """)
        conn.commit()
        conn.close()

        # Open with FeatureDB (triggers migration)
        db = FeatureDB(db_path)
        feature = db.get_feature('test')

        assert feature['status'] == 'active'
        assert feature['being_modified'] == 'building'
        db.close()


def test_migrate_status_done():
    """done → active (being_modified stays none)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planned',
                code_symbols TEXT,
                files TEXT,
                technical_notes TEXT,
                commit_ids TEXT,
                uses TEXT,
                confidence TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO features (id, name, status)
            VALUES ('test', 'Test Feature', 'done')
        """)
        conn.commit()
        conn.close()

        db = FeatureDB(db_path)
        feature = db.get_feature('test')

        assert feature['status'] == 'active'
        assert feature['being_modified'] == 'none'
        db.close()


def test_migrate_status_deleted():
    """deleted → archived"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planned',
                code_symbols TEXT,
                files TEXT,
                technical_notes TEXT,
                commit_ids TEXT,
                uses TEXT,
                confidence TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO features (id, name, status)
            VALUES ('test', 'Test Feature', 'deleted')
        """)
        conn.commit()
        conn.close()

        db = FeatureDB(db_path)
        feature = db.get_feature('test')

        assert feature['status'] == 'archived'
        assert feature['archived_at'] is not None
        db.close()


def test_migrate_code_symbols_string_array():
    """code_symbols: ["fn1", "fn2"] → [{"name": "fn1", ...}, {"name": "fn2", ...}]"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")

        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planned',
                code_symbols TEXT,
                files TEXT,
                technical_notes TEXT,
                commit_ids TEXT,
                uses TEXT,
                confidence TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        # Insert with old format
        old_symbols = json.dumps(["handleLogin", "validateCredentials"])
        conn.execute("""
            INSERT INTO features (id, name, code_symbols)
            VALUES ('test', 'Test Feature', ?)
        """, [old_symbols])
        conn.commit()
        conn.close()

        db = FeatureDB(db_path)
        feature = db.get_feature('test')

        symbols = json.loads(feature['code_symbols'])
        assert len(symbols) == 2
        assert symbols[0]['name'] == 'handleLogin'
        assert symbols[0]['valid'] is True
        assert symbols[1]['name'] == 'validateCredentials'
        db.close()


def test_new_columns_added():
    """Existing v2 database gets new columns added."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")

        # Create minimal v2 database
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'planned'
            )
        """)
        conn.execute("INSERT INTO features (id, name) VALUES ('test', 'Test')")
        conn.commit()
        conn.close()

        # Open with FeatureDB
        db = FeatureDB(db_path)
        feature = db.get_feature('test')

        # Should have new columns with defaults
        assert 'being_modified' in feature
        assert 'important_message' in feature
        assert 'archived_at' in feature
        db.close()
