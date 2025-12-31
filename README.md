# Feature Tree

A semantic layer connecting human intent and AI implementation.

## The Problem

AI handles implementation. Humans move to abstract levels (product vision, taste, specification). But there's no unified protocol connecting them.

**The gap:**
- Context window limits what AI can hold
- Human thinks "what should exist" / AI thinks "what code to write"
- No shared language between product intent and code structure
- Sessions restart cold, losing accumulated understanding

## The Solution

Two parallel trees that speak both human and AI:

| Tree | Speaks to | Contains |
|------|-----------|----------|
| **Features** | AI (code) | Symbols, files, technical notes |
| **Workflows** | Human (product) | User journeys, flows, dependencies |

The explicit mapping between them is the protocol:
- Modify a feature → see which workflows break
- Design a workflow → see what features exist vs. need building

## Core Concepts

### Atomic Features

Features are small, implementable units. NOT categories.

```
BAD:  "User Authentication" (category - can't implement in one task)
GOOD: "User Login", "Email Verification", "Password Reset" (atomic)
```

**Rule:** If you can't "implement this feature" and get a complete, testable unit - it's not atomic enough.

### Track Symbols, Files, Notes

Every 1x effort noting these = 10x saved later.

| Field | Purpose | Example |
|-------|---------|---------|
| Symbols | LSP-queryable identifiers | `handleLogin`, `UserSession` |
| Files | Paths involved | `src/auth/login.ts` |
| Notes | What code can't capture | "Uses Redis for rate limiting" |

Without tracking: Claude guesses → inconsistent code → hours debugging.

### Workflows

Workflows compose features into user-facing experiences. Two types:

| Type | What it is | Example |
|------|------------|---------|
| **Journey** | User goal (the "why") | "New user becomes paying customer" |
| **Flow** | Steps to achieve (the "how") | "Signup flow", "Checkout flow" |

```
Journey: User Onboarding
  └── Flow: Signup Flow      → depends on [AUTH.Register, EMAIL.Verify]
  └── Flow: First Purchase   → depends on [CART.Add, PAYMENT.Stripe]
```

Journeys contain flows. Flows reference features.

## Installation

```bash
/plugin marketplace add github:Nothflare/feature-tree
/plugin install feature-tree@feature-tree
/plugin install ft-mem@feature-tree
# Restart Claude Code
```

## Plugins

| Plugin | Description |
|--------|-------------|
| **feature-tree** | MCP tools + `/bootstrap` skill |
| **ft-mem** | Session continuity (handoff, memories, onboarding) |

## MCP Tools

### Features

| Tool | Description |
|------|-------------|
| `search_features(query)` | Fuzzy search, trimmed output |
| `get_feature(id)` | Full details + linked workflows |
| `add_feature(id, name, ...)` | Create atomic feature |
| `update_feature(id, ...)` | Track symbols, files, commits, status |
| `delete_feature(id)` | Hard if planned, soft if in-progress/done |

### Workflows

| Tool | Description |
|------|-------------|
| `search_workflows(query)` | Fuzzy search journeys/flows |
| `get_workflow(id)` | Full details + linked features |
| `add_workflow(id, name, type, depends_on?, mermaid?)` | Create journey or flow |
| `update_workflow(id, ...)` | Update status, depends_on, mermaid |
| `delete_workflow(id)` | Hard if planned, soft if in-progress/done |

## Skills

| Skill | Description |
|-------|-------------|
| `/bootstrap` | Scan codebase by tracing workflows |
| `/ft-mem:onboarding` | First-time setup (CONTEXT.md + memories) |
| `/ft-mem:handoff` | Save context before /clear |

## Storage

```
.feat-tree/
├── features.db      # SQLite + FTS5
├── FEATURES.md      # Auto-generated
├── WORKFLOWS.md     # Auto-generated (with mermaid)
├── CONTEXT.md       # Product context (created by onboarding)
└── memories/        # Session continuity
```

## Feature Lifecycle

```
planned → in-progress → done
   ↓
hard delete (no trace)    soft delete (recoverable)
```

## Usage

```
Human: Add user signup flow

Claude: [search_features("signup")] - checking existing
        [add_workflow(id="signup-flow", type="flow", depends_on=[...])]
        [add_feature(id="auth-register", name="User Registration")]

        Implementing...
        [update_feature(id="auth-register", status="in-progress",
                       code_symbols=["registerUser"], files=["src/auth/register.ts"])]
```

## Requirements

- Python 3.11+
- uv

## License

MIT
