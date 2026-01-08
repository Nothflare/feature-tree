#!/usr/bin/env python3
"""Session start hook: create session mapping, inject context, and workflow-first reminder."""
import json
import sys
from pathlib import Path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    cwd = input_data.get("cwd", "")
    if not cwd:
        print(json.dumps({}))
        return

    feat_tree_home = Path.home() / ".feat-tree"
    feat_tree_home.mkdir(parents=True, exist_ok=True)
    sessions_file = feat_tree_home / "sessions.json"

    # Load existing sessions map: {project_path: session_id}
    try:
        sessions = json.loads(sessions_file.read_text(encoding="utf-8"))
    except:
        sessions = {}

    # Reuse existing ID for this project, or assign next available
    if cwd in sessions:
        session_id = sessions[cwd]
    else:
        session_id = max(sessions.values(), default=0) + 1
        sessions[cwd] = session_id
        sessions_file.write_text(json.dumps(sessions), encoding="utf-8")

    # Also write to current-project for backwards compatibility
    (feat_tree_home / "current-project").write_text(cwd, encoding="utf-8")

    # Build context
    context_parts = []

    # Workflow-first reminder
    context_parts.append("""## Workflow-First Approach

Start at the right zoom level:
- **Workflows** = broad context (user journeys)
- **Features** = focused context (atomic code units)  
- **Code** = finest detail (files, symbols)

Search before implementing. Update after implementing.""")

    context_parts.append(f"FT_SESSION={session_id}")

    # Check for CONTEXT.md
    context_file = Path(cwd) / ".feat-tree" / "CONTEXT.md"
    if context_file.exists():
        try:
            context_parts.append("# CONTEXT\n\n" + context_file.read_text(encoding="utf-8").strip())
        except Exception:
            pass

    # Check for handoff.md
    handoff_file = Path(cwd) / ".feat-tree" / "memories" / "handoff.md"
    if handoff_file.exists():
        try:
            handoff_content = handoff_file.read_text(encoding="utf-8")
            context_parts.append("# Session Handoff\n" + handoff_content.strip())
        except Exception:
            pass

    # List other memories
    memories_dir = Path(cwd) / ".feat-tree" / "memories"
    if memories_dir.exists():
        try:
            other_memories = [f.stem for f in memories_dir.glob("*.md") if f.stem != "handoff"]
            if other_memories:
                context_parts.append(f"Other memories: {', '.join(other_memories)}\nRead from .feat-tree/memories/<name>.md if needed.")
        except Exception:
            pass

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(context_parts)
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
