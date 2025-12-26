---
name: onboarding
description: First-time project setup - creates .feat-tree/memories/ for session continuity
---

# Project Onboarding

One-time setup: create memory files in `.feat-tree/memories/` for session continuity.

## When to Use

- First time using Feature Tree in a project
- When `.feat-tree/memories/` is empty or missing
- SessionStart hook will prompt you

## Process

1. Create directory: `mkdir -p .feat-tree/memories`
2. Explore: Read README, package.json, pyproject.toml, etc.
3. Create memory files based on what's useful for this project

## Suggested Memories

| File | Purpose |
|------|---------|
| `project_overview.md` | What it does, tech stack, entry points |
| `suggested_commands.md` | Test, lint, format, build commands |
| `code_style.md` | Naming, types, patterns used |
| `codebase_structure.md` | Key directories and their purpose |

## Additional Memories

Create any that help future sessions:

```
.feat-tree/memories/
├── project_overview.md
├── suggested_commands.md
├── api_patterns.md          # If complex API
├── auth_flow.md             # If auth is tricky
├── database_schema.md       # If DB-heavy
├── known_issues.md          # Ongoing quirks
└── [anything_useful].md
```

## Guidelines

- One topic per file
- Dense > verbose (same info, fewer tokens)
- Ask user if info not findable in code
- Only create what future sessions will actually use
