# ft-mem

Session continuity for Claude Code. Companion plugin to feature-tree.

## What It Does

- **Handoff**: Save session context before `/clear` so next Claude continues seamlessly
- **Memories**: Persist project knowledge in `.feat-tree/memories/`
- **Onboarding**: First-time setup to create memory files

## Installation

```bash
# Add marketplace
/plugin marketplace add /path/to/feature-tree

# Install (usually alongside feature-tree)
/plugin install feature-tree@feature-tree-marketplace
/plugin install ft-mem@feature-tree-marketplace

# Restart Claude Code
```

## Commands

| Command | Description |
|---------|-------------|
| **/handoff** | Save session context before /clear |

## Skills

| Skill | Description |
|-------|-------------|
| **onboarding** | First-time `.feat-tree/memories/` setup |

## Storage

```
.feat-tree/
├── features.db              # Feature Tree database
├── FEATURES.md              # Human-readable features
└── memories/                # Session memories
    ├── handoff.md           # Auto-read on startup
    ├── project_overview.md
    ├── code_style.md
    └── [anything].md
```

## Session Handoff

Before `/clear`, run `/handoff`:

```
Human: /handoff

Claude: [Saves current state to handoff.md]
Claude: Memories updated. Safe to /clear
```

Next session automatically reads handoff and continues.

## License

MIT
