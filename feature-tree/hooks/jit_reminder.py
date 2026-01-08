#!/usr/bin/env python3
"""JIT reminder for PreToolUse(Read|Edit) - surfaces feature context when touching files."""
import json
import sqlite3
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({}))
        return

    # Get file path from tool input
    tool_input = input_data.get("input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path")

    if not file_path:
        print(json.dumps({}))
        return

    # Get cwd from hook context
    cwd = input_data.get("cwd", "")
    if not cwd:
        print(json.dumps({}))
        return

    # Find feature by file
    feature = find_feature_by_file(file_path, cwd)
    if not feature:
        print(json.dumps({}))
        return

    # Build reminder based on feature state
    if feature.get("being_modified", "none") != "none":
        reminder = build_rich_reminder(feature, cwd)
    else:
        used_by_count = count_used_by(feature["id"], cwd)
        reminder = f"📍 {feature['id']} ({used_by_count} dependents)"

    output = {
        "hookSpecificOutput": {
            "additionalContext": reminder
        }
    }
    print(json.dumps(output))


def get_db_path(cwd: str) -> Path:
    """Get path to features.db."""
    return Path(cwd) / ".feat-tree" / "features.db"


def find_feature_by_file(file_path: str, cwd: str) -> dict | None:
    """Query features.db for feature containing this file."""
    db_path = get_db_path(cwd)
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Normalize path for matching (handle both / and \)
        normalized = file_path.replace("\\", "/")
        # Also try relative path
        try:
            rel_path = str(Path(file_path).relative_to(cwd)).replace("\\", "/")
        except ValueError:
            rel_path = normalized

        # Search features with this file (check both absolute and relative)
        cursor = conn.execute(
            """SELECT * FROM features
               WHERE (files LIKE ? OR files LIKE ?)
               AND status != 'archived'
               LIMIT 1""",
            [f'%{normalized}%', f'%{rel_path}%']
        )
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
    except Exception:
        return None


def count_used_by(feature_id: str, cwd: str) -> int:
    """Count features that use this feature."""
    db_path = get_db_path(cwd)
    if not db_path.exists():
        return 0

    try:
        conn = sqlite3.connect(str(db_path))
        count = 0
        rows = conn.execute(
            "SELECT uses FROM features WHERE status != 'archived'"
        ).fetchall()
        for row in rows:
            if row[0]:
                uses = json.loads(row[0])
                if feature_id in uses:
                    count += 1
        conn.close()
        return count
    except Exception:
        return 0


def get_used_by(feature_id: str, cwd: str, limit: int = 3) -> list[str]:
    """Get list of feature IDs that use this feature."""
    db_path = get_db_path(cwd)
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        result = []
        rows = conn.execute(
            "SELECT id, uses FROM features WHERE status != 'archived'"
        ).fetchall()
        for row in rows:
            if row[1]:
                uses = json.loads(row[1])
                if feature_id in uses:
                    result.append(row[0])
                    if len(result) >= limit:
                        break
        conn.close()
        return result
    except Exception:
        return []


def get_linked_workflows(feature_id: str, cwd: str, limit: int = 3) -> list[str]:
    """Get workflows that depend on this feature."""
    db_path = get_db_path(cwd)
    if not db_path.exists():
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        result = []
        rows = conn.execute(
            "SELECT id, depends_on FROM workflows WHERE status != 'archived'"
        ).fetchall()
        for row in rows:
            if row[1]:
                depends = json.loads(row[1])
                if feature_id in depends:
                    result.append(row[0])
                    if len(result) >= limit:
                        break
        conn.close()
        return result
    except Exception:
        return []


def build_rich_reminder(feature: dict, cwd: str) -> str:
    """Build rich context for feature being actively modified."""
    lines = [
        f"📍 {feature['id']} [{feature.get('status', 'planned')}] [{feature.get('being_modified', 'none')}]"
    ]

    if feature.get("important_message"):
        lines.append(f"⚠️ {feature['important_message']}")

    uses = json.loads(feature.get("uses") or "[]")
    lines.append(f"Uses: {', '.join(uses[:3]) if uses else 'none'}")

    used_by = get_used_by(feature["id"], cwd)
    lines.append(f"Used by ({count_used_by(feature['id'], cwd)}): {', '.join(used_by)}")

    workflows = get_linked_workflows(feature["id"], cwd)
    lines.append(f"Workflows: {', '.join(workflows) if workflows else 'none'}")

    lines.append(f"\nRun get_feature(\"{feature['id']}\") for full context.")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
