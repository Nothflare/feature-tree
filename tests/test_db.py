# tests/test_db.py
import json
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


def test_add_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        feature = db.add_feature(
            id="auth-login",
            name="User Login",
            description="Login with email/password"
        )

        assert feature["id"] == "auth-login"
        assert feature["name"] == "User Login"
        assert feature["status"] == "planned"
        db.close()


def test_update_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth", name="Auth")
        updated = db.update_feature(
            id="auth",
            status="in-progress",
            code_symbols=["AuthService", "loginUser"]
        )

        assert updated["status"] == "in-progress"
        assert json.loads(updated["code_symbols"]) == ["AuthService", "loginUser"]
        db.close()


def test_delete_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="temp", name="Temporary")
        deleted = db.delete_feature("temp")

        assert deleted["status"] == "deleted"
        db.close()


def test_search_features():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth-login", name="User Login", description="Login with email")
        db.add_feature(id="auth-signup", name="User Signup", description="Register new users")
        db.add_feature(id="payments", name="Payments", description="Stripe integration")

        results = db.search_features("user")

        assert len(results) == 2
        ids = [r["id"] for r in results]
        assert "auth-login" in ids
        assert "auth-signup" in ids
        db.close()
