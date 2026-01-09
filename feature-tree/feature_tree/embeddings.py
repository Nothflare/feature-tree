# feature_tree/embeddings.py
"""Semantic search using ChromaDB + OpenRouter API for embeddings."""

import json
import os
import time
import threading
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from feature_tree.db import FeatureDB

# Lazy imports for optional dependencies
_chroma_client = None
_chroma_available = None

# Background embedding worker
_embed_worker: threading.Thread = None
_embed_worker_stop = threading.Event()
_db_path_for_worker: Path = None

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2  # seconds, doubles each attempt: 2, 4, 8
POLL_INTERVAL = 2.0  # seconds between queue checks


def _get_worker_db():
    """Get a fresh DB connection for the worker thread."""
    from feature_tree.db import FeatureDB
    if _db_path_for_worker is None:
        return None
    db_file = _db_path_for_worker / "features.db"
    return FeatureDB(str(db_file))


def _embedding_worker(status_callback: Callable[[str, str, dict], None]):
    """Background worker that processes embedding jobs from DB queue with auto-retry.

    Polls DB for ready jobs, processes them, handles retries with backoff.
    Survives restarts - pending jobs are persisted in SQLite.
    """
    while not _embed_worker_stop.is_set():
        db = _get_worker_db()
        if db is None:
            time.sleep(POLL_INTERVAL)
            continue

        try:
            job = db.get_next_embed_job()
            if job is None:
                db.close()
                time.sleep(POLL_INTERVAL)
                continue

            item_type = job["item_type"]
            item_id = job["item_id"]
            attempt = job["attempt"]

            # Fetch actual item data
            if item_type == "feature":
                item_data = db.get_feature(item_id)
            else:
                item_data = db.get_workflow(item_id)

            if item_data is None:
                # Item was deleted, remove from queue
                db.delete_embed_job(item_type, item_id)
                db.close()
                continue

            # Try embedding
            try:
                if item_type == "feature":
                    success = embed_feature(item_data, _db_path_for_worker)
                else:
                    success = embed_workflow(item_data, _db_path_for_worker)

                if success:
                    # Success - remove from queue, update status
                    db.delete_embed_job(item_type, item_id)
                    status = {"status": "success", "at": datetime.now(UTC).isoformat()}
                    status_callback(item_type, item_id, status)
                else:
                    # Failed - retry or give up
                    _handle_failure(db, item_type, item_id, attempt, "embedding_unavailable", status_callback)

            except Exception as e:
                _handle_failure(db, item_type, item_id, attempt, str(e), status_callback)

        except Exception:
            pass  # DB error, will retry next poll
        finally:
            try:
                db.close()
            except Exception:
                pass

        # Small sleep to prevent tight loop
        time.sleep(0.1)


def _handle_failure(db, item_type: str, item_id: str, attempt: int, error: str,
                    status_callback: Callable[[str, str, dict], None]):
    """Handle embedding failure - retry with backoff or wait for restart."""
    if attempt < MAX_RETRY_ATTEMPTS:
        backoff = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
        next_retry = (datetime.now(UTC) + timedelta(seconds=backoff)).isoformat()
        db.update_embed_job_retry(item_type, item_id, attempt + 1, next_retry)
        status = {
            "status": "retrying",
            "attempt": attempt + 1,
            "error": error,
            "next_retry_in": backoff,
            "at": datetime.now(UTC).isoformat()
        }
        status_callback(item_type, item_id, status)
    else:
        # Max retries exceeded - keep in queue for next startup (likely network issue)
        # Set next_retry_at to far future so it won't be picked up this session
        # On next startup, reset_stale_jobs() will clear this
        far_future = (datetime.now(UTC) + timedelta(days=365)).isoformat()
        db.update_embed_job_retry(item_type, item_id, attempt, far_future)
        status = {
            "status": "failed_will_retry",
            "error": error,
            "attempts": attempt,
            "message": "will retry on next startup",
            "at": datetime.now(UTC).isoformat()
        }
        status_callback(item_type, item_id, status)


def start_embed_worker(db_path: Path, status_callback: Callable[[str, str, dict], None]):
    """Start the background embedding worker thread.

    db_path: Path to .feat-tree directory containing features.db
    status_callback(item_type, item_id, status_dict) is called when each job completes.
    """
    global _embed_worker, _embed_worker_stop, _db_path_for_worker

    if _embed_worker is not None and _embed_worker.is_alive():
        return  # Already running

    _db_path_for_worker = db_path

    # Reset stale jobs from previous session for fresh retry
    db = _get_worker_db()
    if db:
        try:
            db.reset_embed_queue_for_startup()
        except Exception:
            pass
        finally:
            db.close()

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
    _embed_worker.join(timeout=5.0)
    _embed_worker = None


def queue_embed_feature(db, feature_id: str) -> bool:
    """Queue a feature for background embedding.

    Returns True if queued, False if no API key configured.
    """
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    return db.queue_embed_job("feature", feature_id)


def queue_embed_workflow(db, workflow_id: str) -> bool:
    """Queue a workflow for background embedding.

    Returns True if queued, False if no API key configured.
    """
    config = get_embedding_config()
    if not config.get("api_key"):
        return False

    return db.queue_embed_job("workflow", workflow_id)


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
