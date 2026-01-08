# tests/test_markdown.py
import os
import tempfile
from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_features_markdown


def test_generate_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth", name="Authentication", description="Auth system")
        db.add_feature(id="auth-login", name="Login", parent_id="auth", status="active")

        md = generate_features_markdown(db)

        assert "# Features" in md
        assert "## auth" in md
        assert "Authentication" in md
        assert "### auth-login" in md
        assert "**Status:** active" in md
        db.close()
