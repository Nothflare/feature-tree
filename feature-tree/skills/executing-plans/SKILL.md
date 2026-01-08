---
name: executing-plans
description: "Execute implementation plans one commit at a time. Follow the order from brainstorm, implement, test REAL, commit."
---

# Executing Plans

Execute implementation plans from brainstorm. One commit at a time. Test real. Keep state clean.

## The Loop

```
For each commit group in the plan:
    1. Implement the feature(s)
    2. Test REAL (not fake)
    3. Commit with /feature-tree:commit
    4. Report progress
    5. Next
```

That's it. The complexity is in the plan. This skill just executes.

## Before Starting

1. **Have a plan** — From brainstorm, with Implementation Order grouped by commits
2. **Review the plan** — If something feels wrong, go back to brainstorm
3. **Check dependencies** — Make sure earlier commits are done before starting later ones

## Implement

For each commit group:

1. Mark features as `being_modified=building` if big/complex
2. Write the code
3. Keep changes focused — only what's in this commit group

## Test REAL

**This is critical.** Claude tends to fake testing when overwhelmed. Don't.

| Type | Real Testing | NOT Real Testing |
|------|--------------|------------------|
| Web app | Browser automation, real clicks, real pages | Unit tests alone |
| API | Real API calls, real credentials | Curl with fake data |
| Database | Real DB, real queries, real data | Mocked DB |
| Integration | End-to-end with real services | Mocked services |

**Rule:** Test like a real user would. If you can't test it real, the batch is too big or something is missing.

**If testing feels overwhelming:**
- Batch is too big → Split it
- Missing dependency → Go back to plan
- Don't fake it → Ask for help

## Commit

Use `/feature-tree:commit` after each commit group:
- Commits code with descriptive message
- Updates Feature Tree (files, symbols, status)
- Records commit hash

**Never:**
- Commit with failing tests
- Commit multiple groups at once
- Skip the commit step

## Report Progress

After each commit:

```
Commit 1 (Infrastructure) ✓
- INFRA.database — done
- INFRA.config — done
Tested: Real DB connection, config loads from env
Committed: abc1234

Ready for Commit 2 (Auth Login)?
```

Wait for user feedback before continuing.

## When to Stop

**Stop immediately when:**
- Tests fail and you can't fix it
- Something is missing from the plan
- The plan feels wrong
- You're tempted to skip real testing

**Don't:**
- Push through blockers
- Fake tests to move forward
- Implement things not in the plan
- Combine multiple commit groups

## Progress Tracking

Update handoff as you go:

```markdown
## Progress
- [x] Commit 1: Infrastructure — done
- [~] Commit 2: Auth Login — current
- [ ] Commit 3: Auth Supporting — planned
```

If session ends mid-work:
1. Set `being_modified` on incomplete features
2. Update handoff with progress
3. Note what's tested vs not

## Integration

**Preceded by:** `feature-tree:brainstorm` (creates the plan)

**Uses:** `/feature-tree:commit` (after each commit group)

**If ending session:** `ft-mem:handoff` (save progress)
