---
description: Use before /clear to save session context for seamless handoff to next session
---

# Session Handoff

Save context so next Claude continues seamlessly. Handoff depth depends on task status.

## Steps

### 1. Record Feature Tree Changes

**List features/workflows YOU created or modified this session.**

You already know what you did — it's in your context. Record:
- Features you created (add_feature)
- Features you modified (update_feature)
- Workflows you created/modified
- Status changes

This prevents next Claude from recreating features that already exist.

### 2. Update or Create Memories

Memories are flexible `.md` files in `.feat-tree/memories/`. Update existing ones or create new ones as needed:

**Common memories to check:**
- `code_style.md` - New patterns?
- `suggested_commands.md` - New commands?
- `codebase_structure.md` - New files/dirs?

**Create new memories if session discovered something reusable:**
- `api_patterns.md` - If you figured out API conventions
- `[feature]_notes.md` - If a feature has gotchas
- `debugging_[topic].md` - If you solved a tricky issue
- `[anything].md` - Whatever future sessions need

**Context efficiency:**
- READ before WRITE (avoid duplicates)
- One topic per file
- Dense > verbose (same info, fewer tokens)
- Only create if future sessions will benefit

### 3. Write Handoff (Status-Dependent)

Create `.feat-tree/memories/handoff.md` using appropriate template:

---

#### If DONE

```markdown
# Handoff

## Completed
[What was accomplished]

## Features Created/Modified (QUERY THESE)
| ID | Name | Status | Action |
|----|------|--------|--------|
| AUTH.login | User Login | done | created |
| INFRA.logger | Logger | done | modified |

**Next session MUST run `get_feature(id)` for each row above.**
The table is a summary — the FT entry is the source of truth.

## Files Changed
- path/to/file.ts

## Notes for Future
- [Any gotchas discovered]

## Continue Protocol for Next Session

**Before any implementation:**

1. Run `get_feature(id)` for EACH feature in the table above
2. Check `linked_workflows` in each response
3. For each workflow: run `get_workflow(id)` to understand data flow
4. Trace: where does data come from → how it transforms → where it goes

**The handoff TEXT is a summary. The FT ENTRIES are the source of truth.**
**DO NOT speculate about data structures or DB schema. Trace the actual flow.**

## Read These Memories
Next session should read:
- `.feat-tree/memories/[relevant_memory].md` - [why it's helpful]
```

---

#### If IN-PROGRESS

```markdown
# Handoff

## Working On
[Goal and current state]

## Features Created/Modified (QUERY THESE)
| ID | Name | Status | Action |
|----|------|--------|--------|
| AUTH.login | User Login | in-progress | created |
| AUTH.session | Session Mgmt | planned | created |

**Next session MUST run `get_feature(id)` for each row above.**
The table is a summary — the FT entry is the source of truth.

## Approach
[Strategy being used and why]

## Progress
- [x] Done: [step]
- [ ] Next: [step]

## Key Decisions
- [Decision]: [Why, so next Claude doesn't revisit]

## Files Involved
- path/to/file.ts - [what was changed/needs changing]

## Watch Out For
- [Gotcha or edge case discovered]

## Continue Protocol for Next Session

**Before any implementation:**

1. Run `get_feature(id)` for EACH feature in the table above
2. Check `linked_workflows` in each response
3. For each workflow: run `get_workflow(id)` to understand data flow
4. Trace: where does data come from → how it transforms → where it goes

**The handoff TEXT is a summary. The FT ENTRIES are the source of truth.**
**DO NOT speculate about data structures or DB schema. Trace the actual flow.**

## Read These Memories
Next session MUST read:
- `.feat-tree/memories/[relevant_memory].md` - [why it's critical]
- `.feat-tree/memories/[another].md` - [why needed]
```

---

#### If DEBUGGING

```markdown
# Handoff

## Bug/Issue
[Clear description]

## Features Affected (QUERY THESE)
| ID | Name | Notes |
|----|------|-------|
| AUTH.login | User Login | Bug is here |

**Next session MUST run `get_feature(id)` for each row above.**
The table is a summary — the FT entry is the source of truth.

## Root Cause
[Cause or "Still investigating"]

## What Was Tried
- [Approach]: [Result and WHY it didn't work]

## Current Hypothesis
[Best guess for next Claude]

## Next To Try
- [Specific next step]

## Continue Protocol for Next Session

**Before any implementation:**

1. Run `get_feature(id)` for EACH feature in the table above
2. Check `linked_workflows` in each response
3. For each workflow: run `get_workflow(id)` to understand data flow
4. Trace: where does data come from → how it transforms → where it goes

**The handoff TEXT is a summary. The FT ENTRIES are the source of truth.**
**DO NOT speculate about data structures or DB schema. Trace the actual flow.**

## Read These Memories
Next session should read:
- `.feat-tree/memories/debugging_[topic].md` - [contains relevant context]
```

---

#### If BLOCKED

```markdown
# Handoff

## Task
[What was being attempted]

## Features Involved (QUERY THESE)
| ID | Name | Status |
|----|------|--------|
| ... | ... | ... |

**Next session MUST run `get_feature(id)` for each row above.**
The table is a summary — the FT entry is the source of truth.

## Blocker
[What's preventing progress]

## Possible Paths Forward
- [Option A]: [Pros/cons]

## Needs
- [External input/decision needed]

## Continue Protocol for Next Session

**Before any implementation:**

1. Run `get_feature(id)` for EACH feature in the table above
2. Check `linked_workflows` in each response
3. For each workflow: run `get_workflow(id)` to understand data flow
4. Trace: where does data come from → how it transforms → where it goes

**The handoff TEXT is a summary. The FT ENTRIES are the source of truth.**
**DO NOT speculate about data structures or DB schema. Trace the actual flow.**

## Read These Memories
Next session should read:
- `.feat-tree/memories/[relevant].md` - [why needed to understand blocker]
```

---

### 4. Confirm

Say:
```
Memories updated. Safe to /clear.

Next session should read:
- .feat-tree/memories/handoff.md
- .feat-tree/memories/[other relevant files]

Features in Feature Tree:
- [list any created/modified features]
```

## Context Efficiency

- Handoff length matches complexity
- Include WHY things failed, not just WHAT
- Future Claude should never repeat failed approaches
- Decisions need reasoning so they're not re-questioned
- **Always list features created** — prevents duplicate creation
- **Always list memories to read** — ensures seamless continuation
