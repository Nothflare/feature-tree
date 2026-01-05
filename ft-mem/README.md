# ft-mem

Session continuity for Claude Code. Companion plugin to feature-tree.

## Why Use ft-mem?

### The Problem

Without session memory:
- Every `/clear` loses all context
- Next Claude re-asks the same questions
- Debugging progress lost
- Design decisions forgotten

### What ft-mem Gives You

| Before | After |
|--------|-------|
| "What were we working on?" → no idea | Next session reads handoff.md automatically |
| "Why did we choose X?" → lost forever | Decision recorded in memories/architecture.md |
| "What files are involved?" → grep again | Handoff lists files, features, and state |

## Installation

```bash
/plugin marketplace add github:Nothflare/feature-tree
/plugin install ft-mem@feature-tree
# Restart Claude Code
```

Usually installed alongside feature-tree.

## Skills

### /ft-mem:handoff

**Use before `/clear`** to save session context.

```
Human: /ft-mem:handoff

Claude: [Creates handoff.md with current state]
        - What we were working on
        - Features created/modified
        - Key decisions and why
        - What to do next

        Safe to /clear.
```

Next session automatically reads handoff.md and continues seamlessly.

### /ft-mem:onboarding

**First-time project setup.** Creates:
- `.feat-tree/CONTEXT.md` - Product overview, constraints, assumptions
- `.feat-tree/memories/` - Directory for persistent knowledge

### /ft-mem:brainstorm-sync

**After brainstorming sessions.** Syncs discoveries to project memory:
- Updates CONTEXT.md with new insights
- Creates relevant memory files

## How It Works

### Session Start

Hook reads and injects into context:
1. `FT_SESSION=N` (session ID for multi-project safety)
2. `.feat-tree/CONTEXT.md` (product context)
3. `.feat-tree/memories/handoff.md` if exists

### Before /clear

Run `/ft-mem:handoff`. It:
1. Records features you created/modified
2. Captures current state (DONE, IN-PROGRESS, DEBUGGING, BLOCKED)
3. Saves key decisions with rationale
4. Lists files to read next session

### Next Session

Claude automatically:
1. Reads handoff context
2. Queries Feature Tree for mentioned features
3. Continues where you left off

## Handoff Templates

The handoff skill uses status-appropriate templates:

| Status | Captured |
|--------|----------|
| **DONE** | What was completed, notes for future |
| **IN-PROGRESS** | Current approach, progress, next steps |
| **DEBUGGING** | Bug description, what was tried, hypotheses |
| **BLOCKED** | Blocker, options, needs |

## Storage

```
.feat-tree/
├── CONTEXT.md              # Product context (injected at session start)
└── memories/
    ├── handoff.md          # Session handoff (auto-read on startup)
    ├── codebase_structure.md
    ├── code_style.md
    ├── debugging_*.md
    └── [anything].md       # You can create any memory files
```

## Memory Files

Create any `.md` file in `memories/` for persistent knowledge:

| File | Purpose |
|------|---------|
| `code_style.md` | Project conventions |
| `codebase_structure.md` | Key directories and patterns |
| `api_patterns.md` | API conventions |
| `debugging_auth.md` | Solved auth issues |

These survive `/clear` and provide context to future sessions.

## Benefits

1. **No re-explaining**: Context persists across sessions
2. **No repeated mistakes**: Debugging notes prevent re-trying failed approaches
3. **Seamless handoff**: Start where you left off
4. **Team knowledge**: Memory files work for any Claude session on the project

## License

MIT
