---
description: Use before /clear to save session context for seamless handoff to next session
---

# Session Handoff

Save context so next Claude continues seamlessly. Handoff depth depends on task status.

## Steps

### 1. Update or Create Memories

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

### 2. Write Handoff (Status-Dependent)

Create `.feat-tree/memories/handoff.md` using appropriate template:

---

#### If DONE

```markdown
# Handoff

## Completed
[What was accomplished]

## Files Changed
- path/to/file.ts

## Notes for Future
- [Any gotchas discovered]
```

---

#### If IN-PROGRESS

```markdown
# Handoff

## Working On
[Goal and current state]

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
```

---

#### If DEBUGGING

```markdown
# Handoff

## Bug/Issue
[Clear description]

## Root Cause
[Cause or "Still investigating"]

## What Was Tried
- [Approach]: [Result and WHY it didn't work]

## Current Hypothesis
[Best guess for next Claude]

## Next To Try
- [Specific next step]
```

---

#### If BLOCKED

```markdown
# Handoff

## Task
[What was being attempted]

## Blocker
[What's preventing progress]

## Possible Paths Forward
- [Option A]: [Pros/cons]

## Needs
- [External input/decision needed]
```

---

### 3. Confirm

Say: "Memories updated. Safe to /clear"

## Context Efficiency

- Handoff length matches complexity
- Include WHY things failed, not just WHAT
- Future Claude should never repeat failed approaches
- Decisions need reasoning so they're not re-questioned
