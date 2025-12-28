---
name: onboarding
description: First-time project setup - creates .feat-tree/ with CONTEXT.md and memories
---

# Project Onboarding

One-time setup: create `.feat-tree/CONTEXT.md` and memory files for session continuity.

## When to Use

- First time using Feature Tree in a project
- When `.feat-tree/CONTEXT.md` is missing
- SessionStart hook will prompt you

## Process

1. Create directories: `mkdir -p .feat-tree/memories`
2. **Create CONTEXT.md** (required - this is your product spec)
3. Explore: Read README, package.json, pyproject.toml, etc.
4. Create memory files based on what's useful

## Step 1: Create CONTEXT.md

Ask the user these questions, then write `.feat-tree/CONTEXT.md`:

```markdown
# CONTEXT

## Problem
[What pain point does this solve?]

## Target Users
[Who is this for? Brief descriptions.]

## Success Criteria
[How do we know it's working?]

## Constraints
[Solo dev? Budget? Platform requirements?]

## Key Assumptions
- [untested] ...
- [validated] ...
- [invalidated] ...
```

## Step 2: Create Memories

| File | Purpose |
|------|---------|
| `codebase_structure.md` | Key directories and their purpose |
| `suggested_commands.md` | Test, lint, format, build commands |

Optional:
```
.feat-tree/memories/
├── api_patterns.md          # If complex API
├── auth_flow.md             # If auth is tricky
├── database_schema.md       # If DB-heavy
└── [anything_useful].md
```

## Guidelines

- CONTEXT.md is required - ask user if info not in code
- One topic per memory file
- Dense > verbose (same info, fewer tokens)
