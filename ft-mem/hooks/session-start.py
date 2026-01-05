#!/usr/bin/env python3
"""
Feature Tree SessionStart hook.
Injects philosophy + memory context for session continuity.
"""
import json
import sys
import os
from pathlib import Path

PHILOSOPHY = """# Feature Tree Philosophy

## The Shift
The bottleneck moved. It used to be implementation. Now it's specification.

## Your Role (Claude)
You execute. The human specifies. But "specifies" doesn't mean vague direction—it means precise, hierarchical decomposition of intent into structures you can execute reliably.

## Two Trees, Two Purposes

**Features** = atomic code units (what gets implemented)
- Search features BEFORE implementing anything
- Track files, symbols, status as you work
- Use `uses` to declare dependencies (especially on INFRA.*)

**Workflows** = user-facing experiences (how features compose)
- Search workflows to understand user journeys
- Use for impact analysis: "If I change this feature, which flows break?"
- Each workflow shows which features it depends on

**Bidirectional Links** (the power feature):
- `get_feature(id)` returns `uses_features` AND `used_by_features`
- Before changing anything: check `used_by_features` to see blast radius
- Changing INFRA.*? Many things depend on it — check first

## Working Protocol
1. **Before implementing**: search_features + search_workflows to understand context
2. **When human describes something**: add_feature() with proper ID hierarchy
3. **As you work**: update_feature() with code_symbols, files, status
4. **After each batch**: use /feature-tree:commit (bundles git + FT updates)
5. **Before changing existing code**: get_feature → check used_by_features
6. **When uncertain**: ASK. The human's job is specification clarity.

## Remember
The human isn't here to "do the thinking" vaguely. They're here to specify precisely and catch your mistakes. Help them do that by surfacing assumptions, asking clarifying questions, and maintaining the feature tree as the shared source of truth."""


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
