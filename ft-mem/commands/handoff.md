---
description: Use before /clear to save session context for seamless handoff to next session
---

# Session Handoff

Save context so next Claude continues seamlessly.

## What Handoff Does

1. **Points to the plan** — Reference, don't duplicate
2. **Shows progress** — What's done, current, planned
3. **Captures session context** — Decisions, failures, thinking (stuff not in Feature Tree)

## Structure

```markdown
# Handoff

## Plan
See: `docs/plans/YYYY-MM-DD-<topic>.md`

## Progress
- [x] AUTH.login — done
- [~] AUTH.session — current  
- [ ] AUTH.logout — planned

## Current Task: AUTH.session
[What you were doing, where you stopped]
[Add detail if it helps: file, function, what's next]

## Decisions Made
- [Decision]: [Why] — so next Claude doesn't revisit

## What Failed (if any)
- [Approach]: [Why it didn't work]
```

## Guidelines

- **Reference plan, don't duplicate it**
- **Progress list for quick visibility** — Use [x] done, [~] current, [ ] planned
- **Current task gets most detail** — Where you stopped, what's next
- **Decisions include WHY** — Prevents next Claude from revisiting
- **Failures include WHY** — Prevents next Claude from repeating
- **Flexible detail** — Add more if it helps, less if obvious

## If Mid-Task

Mark the feature so next Claude knows work is active:
```
update_feature(id="AUTH.session", being_modified="building")
```

## After Writing

```
Handoff written to .feat-tree/memories/handoff.md
Safe to /clear.
```
