# tests/test_markdown.py
import os
import tempfile
from feature_tree.db import FeatureDB
from feature_tree.markdown import generate_markdown


def test_generate_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "features.db")
        db = FeatureDB(db_path)

        db.add_feature(id="auth", name="Authentication", description="Auth system")
        db.add_feature(id="auth-login", name="Login", parent_id="auth", status="done")

        md = generate_markdown(db)

        assert "# Feature Tree" in md
        assert "## auth" in md
        assert "Authentication" in md
        assert "### auth-login" in md
        assert "**Status:** done" in md
        db.close()
