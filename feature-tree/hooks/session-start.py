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
    sessions_dir = feat_tree_home / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Get next session ID (incrementing from 1)
    counter_file = sessions_dir / ".counter"
    try:
        session_id = int(counter_file.read_text()) + 1
    except:
        session_id = 1
    counter_file.write_text(str(session_id))

    # Store session -> project mapping
    session_file = sessions_dir / f"{session_id}.json"
    session_file.write_text(json.dumps({"project": cwd}), encoding="utf-8")

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
