#!/usr/bin/env python3
"""Write project cwd for MCP server and inject CONTEXT.md."""
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

    # Write cwd for MCP server
    feat_tree_home = Path.home() / ".feat-tree"
    feat_tree_home.mkdir(exist_ok=True)
    (feat_tree_home / "current-project").write_text(cwd, encoding="utf-8")

    # Check for CONTEXT.md
    context_file = Path(cwd) / ".feat-tree" / "CONTEXT.md"

    if context_file.exists():
        try:
            context_content = context_file.read_text(encoding="utf-8").strip()
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": context_content
                }
            }
            print(json.dumps(output))
            return
        except Exception:
            pass
    else:
        # Prompt to create CONTEXT.md
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "[No CONTEXT.md found] Run ft-mem:onboarding to create .feat-tree/CONTEXT.md"
            }
        }
        print(json.dumps(output))
        return

    print(json.dumps({}))

if __name__ == "__main__":
    main()
