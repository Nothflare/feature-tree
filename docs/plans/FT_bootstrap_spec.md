# Feature Tree Bootstrapping Spec

## Context

Feature Tree is a semantic index for AI-assisted development. Traditional indexing (LSP, AST, embeddings) tells AI what code exists. Feature Tree tells AI what the code MEANS - what capabilities the system has, how they compose into user-facing workflows, where the code for each capability lives.

The core data model has two parallel trees:

```
FEATURES (what exists)          WORKFLOWS (how it's used)
─────────────────────           ────────────────────────
# Domain                        # Journey  
## Feature                      ## Flow
### Subfeature                     └─ depends_on: [feature IDs]
   └─ symbols, files, notes        └─ mermaid diagram
```

Features and Workflows reference each other but don't nest. A flow USES features via `depends_on`. A feature can appear in multiple flows.

We already have the base Feature Tree implementation (MCP tools for CRUD, storage in SQLite, auto-generated FEATURES.md). What we need now is BOOTSTRAPPING - taking an existing codebase and generating an initial Feature Tree from it.

---

## What Bootstrapping Produces

**Input:** An existing codebase (local path or pulled from git)

**Output:**
- Features identified with symbols/files mapped
- Infrastructure identified (shared utilities, not user-facing)
- Workflows traced from entry points
- Journeys grouping related workflows
- Confidence levels on everything (LOW/MEDIUM/HIGH)
- Ready for human review and refinement

**Key principle:** Confidence levels are real. LOW means "LLM guessed this, might be wrong." We don't pretend certainty we don't have. Refinement happens on-demand when agent actually needs to touch that code.

---

## Phase 1: Feature Discovery

### Goal
Turn code structure into a feature list. Bottom-up: analyze code, infer capability boundaries.

### Flow

```
Orchestrator Agent
  │
  ├─→ Analyze codebase structure
  │   - Read top-level directories
  │   - Infer modules from folder/file names
  │   - Identify entry points (routes, commands, main exports)
  │
  ├─→ Dispatch N subagents (one per inferred module)
  │   - Each subagent owns a slice of the codebase
  │   - Works independently but aware of other agents
  │
  ├─→ Subagents extract features
  │   - Read files in their module
  │   - Identify capability boundaries
  │   - Map symbols and files to each feature
  │   - Flag shared code with @tags (see Communication Convention)
  │
  ├─→ Handle @tags
  │   - After finishing primary task, check for @self mentions
  │   - Process any cross-module work flagged by others
  │   - Only proceed when ALL agents done (primary + tags)
  │
  └─→ Synthesizer Agent
      - Receives raw feature lists from all subagents
      - Merges duplicates, resolves conflicts
      - Separates FEATURES vs INFRASTRUCTURE
      - Outputs clean feature tree
```

### What Counts as a Feature vs Infrastructure

FEATURE (goes in feature tree):
- Maps to a user-facing capability
- Atomic enough to implement in one Claude session
- Something you'd say "implement the X feature"
- Examples: AUTH.Login, PAYMENTS.Checkout, USER.ProfileUpdate

INFRASTRUCTURE (tracked separately):
- Shared utilities used by multiple features
- Not user-facing on its own
- Examples: validation helpers, logger, db connection pool, error handlers, date formatting

Infrastructure still gets tracked (for impact analysis) but doesn't need to appear in workflows. It's linked to the features that use it.

### Subagent Output Format

Each subagent produces something like:

```yaml
module: "auth"
path: "/src/auth"

features:
  - id: "auth.login"
    name: "User Login"
    description: "Validates credentials, creates session"
    symbols: ["handleLogin", "validateCredentials", "createSession"]
    files: ["src/auth/login.ts", "src/auth/session.ts"]
    confidence: MEDIUM
    
  - id: "auth.logout"
    name: "User Logout"  
    description: "Destroys session, clears tokens"
    symbols: ["handleLogout", "destroySession"]
    files: ["src/auth/logout.ts"]
    confidence: MEDIUM

infrastructure:
  - id: "auth.token-utils"
    name: "Token Utilities"
    description: "JWT signing/verification helpers"
    symbols: ["signToken", "verifyToken", "refreshToken"]
    files: ["src/auth/tokens.ts"]
    used_by: ["auth.login", "auth.logout"]
    confidence: HIGH  # clear from code structure

cross_refs:
  - target: "@db"
    reason: "auth.login calls db.user.findByEmail"
    symbols: ["findByEmail"]
    
  - target: "@everyone"
    reason: "auth/tokens.ts is imported by 5+ modules"
```

---

## Phase 2: Workflow Identification

### Goal
Turn features into workflows. Top-down: start from entry points, trace how features compose into user-facing flows.

### Flow

```
Orchestrator Agent
  │
  ├─→ Identify terminal features
  │   - Entry points (routes, commands, exported APIs)
  │   - Features with no downstream callers
  │   - These are natural workflow starting points
  │
  ├─→ Dispatch N subagents (one per terminal feature)
  │   - Each traces backward AND forward from their starting point
  │   - Backward: what does this feature call?
  │   - Forward: what calls this feature? (for non-terminal entry points)
  │
  ├─→ Subagents return raw traces
  │   - Will be messy, "program" style
  │   - Function call chains, not human-readable flows
  │
  ├─→ Synthesizer Agent (CRITICAL)
  │   - Receives raw traces from all subagents
  │   - Cleans up to Feature Tree standard flows
  │   - Human readable, intuitive, not code-brained
  │   - Merges overlapping traces
  │   - Produces mermaid diagrams
  │
  ├─→ Coverage check
  │   - Does every FEATURE appear in at least one flow?
  │   - Infrastructure doesn't need coverage
  │   - If uncovered features exist:
  │       → Use them as new starting points
  │       → Loop back to dispatch step
  │   - If all covered: proceed
  │
  └─→ Journey grouping (single agent)
      - Sees all flows
      - Groups into journeys based on:
          - Shared entity lifecycle (same data touched progressively)
          - State transitions (status fields changing)
          - Temporal dependencies (B requires A to complete first)
          - Naming/proximity signals
      - Outputs final journey structure
```

### What Makes a Good Flow (FT Standard)

Raw trace from subagent:
```
login_route() -> validateInput() -> turnstile.verify() -> 
db.users.findByEmail() -> bcrypt.compare() -> jwt.sign() -> 
db.sessions.create() -> res.cookie()
```

Cleaned flow from synthesizer:
```yaml
id: "flow.user-login"
name: "User Login"
journey: "user-onboarding"  # assigned later
depends_on: ["turnstile.verify", "auth.login", "db.session"]
mermaid: |
  graph TD
    A[User submits credentials] --> B[TURNSTILE.Verify]
    B --> C[AUTH.Login]
    C --> D[DB.Session create]
    D --> E[User logged in]
confidence: MEDIUM
```

The synthesizer's job is to:
- Collapse implementation details (bcrypt.compare is inside AUTH.Login, not separate)
- Use feature IDs, not function names
- Make it readable by humans who don't know the code
- Group related steps appropriately

---

## Communication Convention

### The @Tag System

Subagents work independently but need to coordinate on cross-module stuff. The convention:

**@agent_name** - Flag something for a specific agent
```
"@db - auth.login calls db.user.findByEmail, you should know about this dependency"
```

**@everyone** - Flag something all agents should know
```
"@everyone - src/utils/validate.ts is used by 5+ modules, should be INFRASTRUCTURE"
```

### How @Tags Work

1. Subagent discovers cross-module reference while working
2. Adds @tag to their output with context
3. After ALL subagents finish primary work, each checks for @self mentions
4. Process flagged items (might just be acknowledging, might need to adjust their output)
5. Only mark phase complete when ALL agents done with primary + tags

### Conflict Resolution

If two agents both claim the same code as their feature:
- Flag it with @conflict
- Synthesizer reviews and decides
- Or: escalate to human if genuinely ambiguous

---

## Confidence Levels

Every node (feature, infrastructure, flow, journey) gets a confidence level:

**HIGH** - Certain from code structure
- File is literally named `login.ts` with exported `handleLogin`
- Directory structure makes boundaries obvious
- Tests explicitly name the feature

**MEDIUM** - Reasonable inference
- Import patterns suggest this grouping
- Naming hints but not definitive
- Most bootstrap output will be MEDIUM

**LOW** - Best guess
- Ambiguous boundaries
- Could plausibly be split differently
- Cross-cutting concerns

### Refinement (On-Demand)

LOW confidence nodes don't need immediate fixing. They get refined when:
- Agent is about to modify code in that area
- Human explicitly asks about it
- Dependency chain requires understanding it

Refinement process:
- Read actual files (not just infer from names)
- Query LSP for real symbol relationships
- Maybe ask human for clarification
- Upgrade confidence level after verification

---

## Final Output Structure

After bootstrapping, the Feature Tree should have:

```
.feat-tree/
├── features.db          # SQLite with all data
├── FEATURES.md          # Auto-generated, human-readable
├── WORKFLOWS.md         # Auto-generated, human-readable  
├── CONTEXT.md           # Product context (human fills in)
├── USERS.md             # User personas (human fills in)
└── bootstrap-log.md     # What was inferred, confidence levels, flagged conflicts
```

The bootstrap-log.md is important - it shows the human what decisions were made so they can review and correct.

---

## Summary

Two phases, both use parallel subagents coordinated by communication conventions:

**Phase 1 (Feature Discovery):** Code → Modules → Subagents extract features → Synthesizer cleans up → Features + Infrastructure

**Phase 2 (Workflow Identification):** Terminal features → Subagents trace call paths → Synthesizer makes human-readable flows → Coverage check (loop if needed) → Single agent groups into journeys

Key principles:
- Confidence levels are honest, not performative
- Subagents coordinate via @tags, not rigid protocols
- Synthesizer agents do the hard work of making output coherent
- Infrastructure is tracked but separate from features
- Refinement is lazy/on-demand, not upfront
