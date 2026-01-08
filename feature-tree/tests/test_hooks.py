# tests/test_hooks.py
"""Test hook functionality."""
import json
import os
import sqlite3
import tempfile
import sys
from pathlib import Path
from io import StringIO

# Add hooks directory to path for importing
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))


def test_jit_reminder_finds_feature():
    """JIT reminder finds feature by file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create .feat-tree/features.db
        feat_tree_dir = Path(tmpdir) / ".feat-tree"
        feat_tree_dir.mkdir()
        db_path = feat_tree_dir / "features.db"

        # Create database with a feature
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT DEFAULT 'planned',
                being_modified TEXT DEFAULT 'none',
                important_message TEXT,
                files TEXT,
                uses TEXT
            )
        """)
        conn.execute("""
            INSERT INTO features (id, name, status, files)
            VALUES ('AUTH.login', 'Login', 'active', '["src/auth/login.ts"]')
        """)
        conn.commit()
        conn.close()

        # Import and test the hook function directly
        from jit_reminder import find_feature_by_file

        feature = find_feature_by_file("src/auth/login.ts", tmpdir)
        assert feature is not None
        assert feature['id'] == 'AUTH.login'


def test_jit_reminder_no_match():
    """JIT reminder returns None for untracked file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feat_tree_dir = Path(tmpdir) / ".feat-tree"
        feat_tree_dir.mkdir()
        db_path = feat_tree_dir / "features.db"

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE features (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT DEFAULT 'planned',
                being_modified TEXT DEFAULT 'none',
                files TEXT
            )
        """)
        conn.execute("""
            INSERT INTO features (id, name, files)
            VALUES ('AUTH.login', 'Login', '["src/auth/login.ts"]')
        """)
        conn.commit()
        conn.close()

        from jit_reminder import find_feature_by_file

        feature = find_feature_by_file("src/other/file.ts", tmpdir)
        assert feature is None


def test_session_start_parse_restore_state():
    """SessionStart parses Restore State from handoff."""
    from session_start import parse_restore_state

    handoff_content = """# Handoff

## Completed
Did some work.

## Restore State
```json
{"feature": "AUTH.login", "being_modified": "refactoring"}
```

## Notes
Some notes.
"""

    result = parse_restore_state(handoff_content)
    assert result is not None
    assert result['feature'] == 'AUTH.login'
    assert result['being_modified'] == 'refactoring'


def test_session_start_no_restore_state():
    """SessionStart returns None when no Restore State."""
    from session_start import parse_restore_state

    handoff_content = """# Handoff

## Completed
Did some work.

## Notes
Some notes.
"""

    result = parse_restore_state(handoff_content)
    assert result is None


def test_session_start_malformed_json():
    """SessionStart handles malformed JSON gracefully."""
    from session_start import parse_restore_state

    handoff_content = """# Handoff

## Restore State
```json
{invalid json here}
```
"""

    result = parse_restore_state(handoff_content)
    assert result is None
