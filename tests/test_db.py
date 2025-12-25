# tests/test_db.py
import os
import tempfile
import pytest
from feature_tree.db import FeatureDB


def test_init_creates_tables():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        # Check tables exist
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "features" in table_names
        assert "features_fts" in table_names
        db.close()
