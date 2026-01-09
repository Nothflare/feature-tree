# Ralph Subagent Execution Plan

**Date:** 2026-01-09
**Status:** Approved

---

## Summary

A skill + 3 agents that enable overnight autonomous development. Main agent orchestrates via a skill. Subagents (Implementer, Tester, Reviewer) do focused work with fresh context. Feature Tree tracks state. Human sleeps, wakes up to working app.

---

## Architecture (Viable System Model)

```
System 5 (Policy)       = DESIGN FILES — product spec, what we're building
System 4 (Intelligence) = HUMAN — strategic decisions, "is this still right?"
System 3 (Management)   = MAIN AGENT — orchestrates subagents, tracks progress
System 2 (Coordination) = (Phase 2) — parallel coordination, not needed yet
System 1 (Operations)   = SUBAGENTS — fresh context workers
```

**Key insight:** Main agent stays alive, subagents get fresh context each time.

---

## Deliverables

| Deliverable | Location | Model | Purpose |
|-------------|----------|-------|---------|
| Skill: ralph-execute | `skills/ralph-execute/SKILL.md` | — | Orchestration loop |
| Agent: implementer | `agents/implementer.md` | opus | Implement features |
| Agent: tester | `agents/tester.md` | sonnet | Run tests (cheaper) |
| Agent: reviewer | `agents/reviewer.md` | opus | Review quality |

---

## Workflows

### Pre-flight Check
Before human leaves, verify ALL dependencies. Fail loud and early.

### Execution Loop
```
Query FT → Spawn Implementer → Spawn Tester → Spawn Reviewer → Loop
```

### Failure Recovery
Max 3 retries per feature, then log blocker and continue.

### Handoff
If implementer can't finish, write handoff file for next implementer.

---

## File Conventions

```
.feat-tree/ralph/
  ├── handoff/{feature_id}.md      # Implementer → Implementer
  ├── test-spec/{feature_id}.md    # What to test
  ├── test-results/{feature_id}.md # Raw test output
  ├── review/{feature_id}.md       # Review findings
  └── blockers/{feature_id}.md     # Stuck after retries
```

---

## Subagent Return Format

```json
{
  "status": "ready-for-test | pass | fail | approved | rejected | needs-continuation",
  "feature_id": "AUTH.login",
  "summary": "One line of what happened",
  "concerns": "Optional: risks or issues noticed",
  "next_action": "test | review | continue | retry | next-feature"
}
```

---

## Implementation Order

### Commit 1: Agents
- implementer.md
- tester.md
- reviewer.md

### Commit 2: Skill
- ralph-execute/SKILL.md

### Commit 3: Integration test
- Manual test with simple feature

---

## Key Decisions

1. **Linear first** — One subagent at a time. Parallel is Phase 2.
2. **Feature Tree as state** — No custom state management.
3. **Sonnet for tester** — Cost optimization.
4. **Trust Claude's intelligence** — Principles over procedures in prompts.
5. **Max 3 retries** — Then blocker and move on.
6. **Main agent stays alive** — No need to persist memory between iterations.

---

## Prompt Philosophy

DON'T enumerate every edge case.
DO explain purpose, context, principles.
TRUST Claude to figure out details.
