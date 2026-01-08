# tests/test_embeddings.py
"""Test embeddings module (without API key - FTS fallback only)."""
import json
import os
import tempfile
from pathlib import Path

from feature_tree import embeddings


def test_feature_to_text():
    """Convert feature to searchable text."""
    feature = {
        "id": "AUTH.login",
        "name": "User Login",
        "description": "Handle user authentication",
        "technical_notes": "Uses bcrypt",
        "files": json.dumps(["src/auth/login.ts"]),
        "code_symbols": json.dumps([{"name": "handleLogin", "location": "src/auth/login.ts", "valid": True}])
    }

    text = embeddings.feature_to_text(feature)

    assert "AUTH.login" in text
    assert "User Login" in text
    assert "authentication" in text
    assert "bcrypt" in text
    assert "src/auth/login.ts" in text
    assert "handleLogin" in text


def test_workflow_to_text():
    """Convert workflow to searchable text."""
    workflow = {
        "id": "USER.login_flow",
        "name": "Login Flow",
        "description": "User signs in with credentials",
        "purpose": "Authenticate users",
        "depends_on": json.dumps(["AUTH.login", "AUTH.session"])
    }

    text = embeddings.workflow_to_text(workflow)

    assert "USER.login_flow" in text
    assert "Login Flow" in text
    assert "credentials" in text
    assert "AUTH.login" in text


def test_get_embedding_no_api_key():
    """Without API key, get_embedding returns None."""
    # Clear any existing API key
    old_key = os.environ.pop("FT_EMBEDDING_API_KEY", None)
    try:
        result = embeddings.get_embedding("test text")
        assert result is None
    finally:
        if old_key:
            os.environ["FT_EMBEDDING_API_KEY"] = old_key


def test_semantic_search_fallback():
    """Semantic search returns empty list when no API key (FTS fallback handles it)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)

        # Clear any existing API key
        old_key = os.environ.pop("FT_EMBEDDING_API_KEY", None)
        try:
            result = embeddings.search_features_semantic("test", db_path)
            assert result == []  # Empty because no embeddings available
        finally:
            if old_key:
                os.environ["FT_EMBEDDING_API_KEY"] = old_key


def test_embed_feature_no_api_key():
    """embed_feature returns False when no API key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir)
        feature = {"id": "TEST", "name": "Test", "status": "planned"}

        old_key = os.environ.pop("FT_EMBEDDING_API_KEY", None)
        try:
            result = embeddings.embed_feature(feature, db_path)
            assert result is False
        finally:
            if old_key:
                os.environ["FT_EMBEDDING_API_KEY"] = old_key


def test_get_embedding_config():
    """Config reads from environment with defaults."""
    # Clear env vars
    old_endpoint = os.environ.pop("FT_EMBEDDING_ENDPOINT", None)
    old_model = os.environ.pop("FT_EMBEDDING_MODEL", None)
    old_key = os.environ.pop("FT_EMBEDDING_API_KEY", None)

    try:
        config = embeddings.get_embedding_config()

        assert config["endpoint"] == "https://openrouter.ai/api/v1/embeddings"
        assert config["model"] == "openai/text-embedding-3-small"
        assert config["api_key"] == ""

        # Test with custom values
        os.environ["FT_EMBEDDING_ENDPOINT"] = "https://custom.api/embeddings"
        os.environ["FT_EMBEDDING_MODEL"] = "custom-model"
        os.environ["FT_EMBEDDING_API_KEY"] = "test-key"

        config = embeddings.get_embedding_config()

        assert config["endpoint"] == "https://custom.api/embeddings"
        assert config["model"] == "custom-model"
        assert config["api_key"] == "test-key"
    finally:
        # Restore
        if old_endpoint:
            os.environ["FT_EMBEDDING_ENDPOINT"] = old_endpoint
        if old_model:
            os.environ["FT_EMBEDDING_MODEL"] = old_model
        if old_key:
            os.environ["FT_EMBEDDING_API_KEY"] = old_key
