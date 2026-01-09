# feature_tree/embeddings.py
"""Semantic search using ChromaDB + OpenRouter API for embeddings."""

import json
import os
import threading
import queue
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Callable

import httpx

# Lazy imports for optional dependencies
_chroma_client = None
_chroma_available = None

# Background embedding queue
_embed_queue: queue.Queue = None
_embed_worker: threading.Thread = None
_embed_worker_stop = threading.Event()


def _embedding_worker(status_callback: Callable[[str, str, dict], None]):
    """Background worker that processes embedding jobs.

    status_callback(item_type, item_id, status_dict) is called after each job.
    status_dict: {"status": "success"|"failed", "at": timestamp, "error"?: str}
    """
    while not _embed_worker_stop.is_set():
        try:
            job = _embed_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if job is None:  # Poison pill
            break

        item_type, item_data, db_path = job
        item_id = item_data.get("id", "unknown")

        try:
            if item_type == "feature":
                success = embed_feature(item_data, db_path)
            else:
                success = embed_workflow(item_data, db_path)

            if success:
                status = {"status": "success", "at": datetime.now(UTC).isoformat()}
            else:
                status = {"status": "failed", "error": "embedding_unavailable", "at": datetime.now(UTC).isoformat()}

            status_callback(item_type, item_id, status)
        except Exception as e:
            status = {"status": "failed", "error": str(e), "at": datetime.now(UTC).isoformat()}
            status_callback(item_type, item_id, status)
        finally:
            _embed_queue.task_done()


def start_embed_worker(status_callback: Callable[[str, str, dict], None]):
    """Start the background embedding worker thread.

    status_callback(item_type, item_id, status_dict) is called when each job completes.
    """
    global _embed_queue, _embed_worker, _embed_worker_stop

    if _embed_worker is not None and _embed_worker.is_alive():
        return  # Already running

    _embed_queue = queue.Queue()
    _embed_worker_stop.clear()
    _embed_worker = threading.Thread(
        target=_embedding_worker,
        args=(status_callback,),
        daemon=True,
        name="EmbeddingWorker"
    )
    _embed_worker.start()


def stop_embed_worker():
    """Stop the background embedding worker thread."""
    global _embed_worker

    if _embed_worker is None:
        return

    _embed_worker_stop.set()
    if _embed_queue is not None:
        _embed_queue.put(None)  # Poison pill
    _embed_worker.join(timeout=5.0)
    _embed_worker = None


def queue_embed_feature(feature: dict, db_path: Path) -> bool:
    """Queue a feature for background embedding.

    Returns True if queued, False if worker not running or no API key.
    """
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    if _embed_queue is None:
        return False

    _embed_queue.put(("feature", feature, db_path))
    return True


def queue_embed_workflow(workflow: dict, db_path: Path) -> bool:
    """Queue a workflow for background embedding.

    Returns True if queued, False if worker not running or no API key.
    """
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    if _embed_queue is None:
        return False

    _embed_queue.put(("workflow", workflow, db_path))
    return True


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
    - FT_EMBEDDING_API_KEY: API key for OpenRouter
    """
    return {
        "endpoint": os.environ.get("FT_EMBEDDING_ENDPOINT", "https://openrouter.ai/api/v1/embeddings"),
        "model": os.environ.get("FT_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
        "api_key": os.environ.get("FT_EMBEDDING_API_KEY", ""),
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

    # Add uses (dependencies) - searching "database" finds features using INFRA.database
    uses = feature.get("uses")
    if uses:
        if isinstance(uses, str):
            uses = json.loads(uses)
        parts.extend(uses)

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

    # Add steps - searching "verify conversation" finds workflows with that step
    steps = workflow.get("steps")
    if steps:
        if isinstance(steps, str):
            steps = json.loads(steps)
        parts.extend(steps)

    return " ".join(filter(None, parts))


def embed_feature(feature: dict, db_path: Path) -> bool:
    """Add or update feature embedding in ChromaDB.

    Returns True if successful, False if embeddings not available.
    """
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    text = feature_to_text(feature)
    embedding = get_embedding(text, config)
    if embedding is None:
        return False

    # Only NOW touch ChromaDB
    client = get_chroma_client(db_path)
    if client is None:
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
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    text = workflow_to_text(workflow)
    embedding = get_embedding(text, config)
    if embedding is None:
        return False

    # Only NOW touch ChromaDB
    client = get_chroma_client(db_path)
    if client is None:
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
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return []

    embedding = get_embedding(query, config)
    if embedding is None:
        return []

    # Only NOW touch ChromaDB
    client = get_chroma_client(db_path)
    if client is None:
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
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return []

    embedding = get_embedding(query, config)
    if embedding is None:
        return []

    # Only NOW touch ChromaDB
    client = get_chroma_client(db_path)
    if client is None:
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
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

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
    # Check API key FIRST - skip ChromaDB entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

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
    # Check API key FIRST - skip entirely if no key
    config = get_embedding_config()
    if not config.get("api_key"):
        return {"features": 0, "workflows": 0}

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
