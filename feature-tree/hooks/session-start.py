#!/usr/bin/env python3
"""Create session mapping and inject CONTEXT.md."""
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
    context_parts = [f"FT_SESSION={session_id}"]

    # Check for CONTEXT.md
    context_file = Path(cwd) / ".feat-tree" / "CONTEXT.md"
    if context_file.exists():
        try:
            context_parts.append(context_file.read_text(encoding="utf-8").strip())
        except Exception:
            pass
    else:
        context_parts.append("[No CONTEXT.md found] Run ft-mem:onboarding to create .feat-tree/CONTEXT.md")

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(context_parts)
        }
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
