---
name: brainstorm
description: "Workflow-first design through collaborative dialogue. Use before creating features, building components, or modifying behavior."
---

# Feature Tree Brainstorming

Turn ideas into fully formed plans through collaborative dialogue.

**Four phases:** Discovery → Product → Design → Specification

---

## Phase 1: Discovery

Push yourself to think. Don't skip these.

### First Principle — Find Actual Intention

Users communicate in solutions, not problems. "Add a spinner" might mean "page feels slow."

Ask yourself:
- What did they say? (surface)
- Why did they say it? (intention)
- Is there a better approach?

### Crux — Core Assumption

Every project has ONE assumption that must be true or everything falls apart.

Ask yourself:
- What's the ONE thing that must be true?
- How do we test it before building everything else?

### Pre-Mortem — How This Fails

Imagine it failed. Why?

Ask yourself:
- "It failed because..." (top 3 reasons)
- What are early warning signs?
- What can we do to prevent each?

### Scope Fence — What This Is NOT

Scope creep kills projects. Define the boundaries.

Ask yourself:
- This IS: [one sentence]
- This is NOT: [explicit exclusions]
- Features we're saying no to?

### User Day-In-Life — Who Specifically

"Users" is too vague. Pick a real person.

Ask yourself:
- Who specifically has this problem?
- When in their day does it appear?
- What do they do now? What's annoying about it?

---

## Phase 2: Product

Think like you're explaining to a YC partner. Capture the essence.

### What IS This Product?

Not the features. The VALUE.

Ask yourself:
- If I had 30 seconds to explain this, what would I say?
- What's the ONE thing that makes this valuable?
- What's the core experience?

### Core Workflows

Identify the workflows that ARE the product (not supporting stuff like auth).

For each core workflow:
- Write the Description (YC partner level)
- Write the Steps (the actual user experience)

This is human thinking. No technical details yet.

---

## Phase 3: Design

Technical thinking. Consider alternatives, find simplicity, identify risks.

### Approaches & Trade-offs

Don't jump to first solution.

Ask yourself:
- What are 2-3 ways to solve this?
- What are the trade-offs of each?
- Which fits this context best? Why?

### Simplest Thing That Works

Complexity is the enemy.

Ask yourself:
- What's the minimal solution?
- What can we NOT build?
- What complexity are we avoiding?

### Hard Parts / Where It Breaks

Every design has weak points.

Ask yourself:
- What's the technically risky part?
- Where will this fail first?
- What needs extra attention during implementation?

---

## Phase 4: Specification

Output the plan. Workflows first, always.

### Output Format

```markdown
# [Topic] Plan

## Summary
[What we're building, why, for whom — 2-3 sentences]

## Workflows

### WORKFLOW.id — Workflow Name
**Status:** planned
**Description:** [YC partner explanation — what this journey IS, why it matters]
**Steps:**
1. [Detailed step — what user does, what system does]
2. [Next step...]
3. [...]
**Depends on:** FEATURE.id, FEATURE.id

---

### WORKFLOW.id — Another Workflow
...

---

## Features

### FEATURE.id — Feature Name
**Status:** planned
**Description:** [YC partner explanation — what it does, user-facing]
**Technical Notes:** [How it works, gotchas, implementation details — enough for Claude to implement without asking questions]
**Uses:** INFRA.id, FEATURE.id

---

### INFRA.id — Infrastructure Feature
**Status:** planned
**Description:** [What it provides]
**Technical Notes:** [Technical details]
**Uses:** —

---

## Implementation Order

Group by commit. Distribute effort evenly — big features get own commit, small ones batch together.

### Commit 1: [Group Name]
- [ ] INFRA.database — setup connection pool
- [ ] INFRA.config — env-based config
(small, related → batch together)

### Commit 2: [Big Feature Name]
- [ ] AUTH.login — validate credentials, create session, handle errors
(complex feature → own commit)

### Commit 3: [Group Name]
- [ ] AUTH.logout — destroy session
- [ ] AUTH.refresh — refresh token
(small, related → batch together)

### Commit 4: [Integration]
- [ ] USER.login_flow — end-to-end test
(workflow integration test)

**Grouping rules:**
- Big/complex feature → own commit
- Small/simple features → batch with related ones
- Each commit should be test-able with REAL testing
- If a group feels too big to test confidently → split it

## Decisions
- [Decision]: [Why we chose this over alternatives]
- [Decision]: [Why]
```

### Key Points for Specification

- **Workflows FIRST** — Always
- **Self-contained detail** — Description + Technical Notes + Steps should be complete enough that Claude can implement without further questions
- **Status markers** — planned / in-progress / done
- **Commit grouping** — Group by effort: big features alone, small features batched
- **Each commit must be testable** — If you can't test it REAL, the group is wrong

---

## After Plan Approval

### 1. Save Plan

Write to `docs/plans/YYYY-MM-DD-<topic>.md`

### 2. Create in Feature Tree

Create the workflows and features in Feature Tree:
```
add_workflow(id="...", name="...", description="...", purpose="...", steps=[...], depends_on=[...])
add_feature(id="...", name="...", description="...", technical_notes="...", uses=[...])
```

### 3. Sync to Memory

**Use sub-skill:** `ft-mem:brainstorm-sync`

Syncs discoveries to CONTEXT.md and memories.

### 4. Implementation

**Use sub-skill:** `feature-tree:executing-plans`

Implements the plan task-by-task with commits between.

---

## Principles

- **Workflow-first, always** — Broad context before details
- **Think, don't checkbox** — Mind tools push real thinking
- **Self-contained output** — Plan needs no further explanation
- **Simplest thing that works** — YAGNI ruthlessly
- **Capture WHY** — Decisions include rationale
