#!/usr/bin/env python3
"""
Feature Tree SessionStart hook.
Injects philosophy + memory context for session continuity.
"""
import json
import sys
import os
from pathlib import Path

PHILOSOPHY = """# Feature Tree Active

**Mantras:** Trace don't speculate • Query entries not text • Check impact before changing • Create entry before implementing

## Cross-Session Protocol

If handoff.md lists features, run `get_feature(id)` for each — the text is a summary, the FT entry is truth.

## Quick Reference

- **Before implementing:** search_features + search_workflows first
- **Before changing:** get_feature → check used_by_features + linked_workflows
- **After implementing:** update_feature with files, code_symbols
- **Commits:** use /feature-tree:commit (not regular git commit)

See Feature Tree MCP server instructions for full protocol."""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    cwd = input_data.get("cwd", os.getcwd())
    memories_dir = Path(cwd) / ".feat-tree" / "memories"
    handoff_file = memories_dir / "handoff.md"

    # Build context
    context_parts = [PHILOSOPHY]

    # Check if memories exist
    has_memories = memories_dir.exists() and any(memories_dir.glob("*.md"))

    if not has_memories:
        context_parts.append("""
---
[Onboarding Required]
No memories in .feat-tree/memories/
Use the ft-mem:onboarding skill to create memory files.""")
    else:
        memory_files = [f.stem for f in memories_dir.glob("*.md") if f.stem != "handoff"]

        # Read handoff if exists
        handoff_content = ""
        if handoff_file.exists():
            try:
                handoff_content = handoff_file.read_text(encoding="utf-8").strip()
            except:
                pass

        if handoff_content:
            context_parts.append(f"""
---
# Session Handoff
{handoff_content}

---
Other memories: {', '.join(memory_files)}
Read from .feat-tree/memories/<name>.md if needed.""")
        else:
            context_parts.append(f"""
---
Memories available: {', '.join(memory_files)}
Read from .feat-tree/memories/<name>.md before starting work.""")

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context_parts)
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
