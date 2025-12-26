#!/usr/bin/env python3
"""Write project cwd for MCP server to read."""
import json
import sys
from pathlib import Path

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    cwd = input_data.get("cwd", "")
    if cwd:
        feat_tree_home = Path.home() / ".feat-tree"
        feat_tree_home.mkdir(exist_ok=True)
        (feat_tree_home / "current-project").write_text(cwd, encoding="utf-8")

    print(json.dumps({}))

if __name__ == "__main__":
    main()
