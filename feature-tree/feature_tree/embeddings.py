# feature_tree/embeddings.py
"""Semantic search using ChromaDB + OpenRouter API for embeddings."""

import json
import os
from pathlib import Path
from typing import Optional

import httpx

# Lazy imports for optional dependencies
_chroma_client = None
_chroma_available = None


def _check_chroma_available() -> bool:
    """Check if chromadb is available."""
    global _chroma_available
    if _chroma_available is None:
        try:
            import chromadb
            _chroma_available = True
        except ImportError:
            _chroma_available = False
    return _chroma_available


def get_embedding_config() -> dict:
    """Get embedding configuration from environment or defaults.

    Environment variables:
    - FT_EMBEDDING_ENDPOINT: OpenRouter API endpoint (default: https://openrouter.ai/api/v1/embeddings)
    - FT_EMBEDDING_MODEL: Model to use (default: openai/text-embedding-3-small)
    - OPENROUTER_API_KEY: API key for OpenRouter
    """
    return {
        "endpoint": os.environ.get("FT_EMBEDDING_ENDPOINT", "https://openrouter.ai/api/v1/embeddings"),
        "model": os.environ.get("FT_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
        "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
    }


def get_chroma_client(db_path: Path):
    """Get or create ChromaDB client for the given path."""
    global _chroma_client

    if not _check_chroma_available():
        return None

    import chromadb

    chroma_path = db_path / "chroma"
    chroma_path.mkdir(exist_ok=True)

    # Create new client if path changed or not initialized
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(chroma_path))

    return _chroma_client


def get_embedding(text: str, config: dict = None) -> Optional[list[float]]:
    """Get embedding vector for text using OpenRouter API.

    Returns None if API key not configured or request fails.
    """
    if config is None:
        config = get_embedding_config()

    api_key = config.get("api_key")
    if not api_key:
        return None

    try:
        response = httpx.post(
            config["endpoint"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model"],
                "input": text,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception:
        return None


def feature_to_text(feature: dict) -> str:
    """Convert feature to searchable text for embedding."""
    parts = [
        feature.get("id", ""),
        feature.get("name", ""),
        feature.get("description", "") or "",
        feature.get("technical_notes", "") or "",
    ]

    # Add files
    files = feature.get("files")
    if files:
        if isinstance(files, str):
            files = json.loads(files)
        parts.extend(files)

    # Add code symbols (handle both old and new format)
    symbols = feature.get("code_symbols")
    if symbols:
        if isinstance(symbols, str):
            symbols = json.loads(symbols)
        for sym in symbols:
            if isinstance(sym, dict):
                parts.append(sym.get("name", ""))
            else:
                parts.append(str(sym))

    return " ".join(filter(None, parts))


def workflow_to_text(workflow: dict) -> str:
    """Convert workflow to searchable text for embedding."""
    parts = [
        workflow.get("id", ""),
        workflow.get("name", ""),
        workflow.get("description", "") or "",
        workflow.get("purpose", "") or "",
    ]

    depends = workflow.get("depends_on")
    if depends:
        if isinstance(depends, str):
            depends = json.loads(depends)
        parts.extend(depends)

    return " ".join(filter(None, parts))


def embed_feature(feature: dict, db_path: Path) -> bool:
    """Add or update feature embedding in ChromaDB.

    Returns True if successful, False if embeddings not available.
    """
    client = get_chroma_client(db_path)
    if client is None:
        return False

    text = feature_to_text(feature)
    embedding = get_embedding(text)

    if embedding is None:
        # No API key or request failed - store without embedding for FTS fallback
        return False

    collection = client.get_or_create_collection("features")

    collection.upsert(
        ids=[feature["id"]],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "status": feature.get("status", "planned"),
            "being_modified": feature.get("being_modified", "none"),
        }],
    )

    return True


def embed_workflow(workflow: dict, db_path: Path) -> bool:
    """Add or update workflow embedding in ChromaDB."""
    client = get_chroma_client(db_path)
    if client is None:
        return False

    text = workflow_to_text(workflow)
    embedding = get_embedding(text)

    if embedding is None:
        return False

    collection = client.get_or_create_collection("workflows")

    collection.upsert(
        ids=[workflow["id"]],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "status": workflow.get("status", "planned"),
        }],
    )

    return True


def search_features_semantic(query: str, db_path: Path, n_results: int = 10) -> list[str]:
    """Semantic search for features. Returns list of feature IDs.

    Returns empty list if embeddings not available.
    """
    client = get_chroma_client(db_path)
    if client is None:
        return []

    embedding = get_embedding(query)
    if embedding is None:
        return []

    try:
        collection = client.get_or_create_collection("features")

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={"status": {"$ne": "archived"}},
        )

        return results["ids"][0] if results["ids"] else []
    except Exception:
        return []


def search_workflows_semantic(query: str, db_path: Path, n_results: int = 10) -> list[str]:
    """Semantic search for workflows. Returns list of workflow IDs."""
    client = get_chroma_client(db_path)
    if client is None:
        return []

    embedding = get_embedding(query)
    if embedding is None:
        return []

    try:
        collection = client.get_or_create_collection("workflows")

        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where={"status": {"$ne": "archived"}},
        )

        return results["ids"][0] if results["ids"] else []
    except Exception:
        return []


def delete_feature_embedding(feature_id: str, db_path: Path) -> bool:
    """Remove feature from ChromaDB."""
    client = get_chroma_client(db_path)
    if client is None:
        return False

    try:
        collection = client.get_or_create_collection("features")
        collection.delete(ids=[feature_id])
        return True
    except Exception:
        return False


def delete_workflow_embedding(workflow_id: str, db_path: Path) -> bool:
    """Remove workflow from ChromaDB."""
    client = get_chroma_client(db_path)
    if client is None:
        return False

    try:
        collection = client.get_or_create_collection("workflows")
        collection.delete(ids=[workflow_id])
        return True
    except Exception:
        return False


def migrate_embeddings(db_path: Path, features: list[dict], workflows: list[dict]) -> dict:
    """Create embeddings for all existing features and workflows.

    Returns {"features": N, "workflows": M} with counts of successfully embedded items.
    """
    feature_count = 0
    workflow_count = 0

    for feature in features:
        if feature.get("status") != "archived":
            if embed_feature(feature, db_path):
                feature_count += 1

    for workflow in workflows:
        if workflow.get("status") != "archived":
            if embed_workflow(workflow, db_path):
                workflow_count += 1

    return {"features": feature_count, "workflows": workflow_count}
