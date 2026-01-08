---
name: brainstorm-sync
description: Capture brainstorm discoveries that aren't in the plan — the thinking that makes this project unique
---

# Brainstorm Sync

After brainstorming, capture the THINKING that didn't make it into the plan. The plan has workflows and features. This captures WHY and WHO and WHAT WE SAID NO TO.

## What to Capture

From the brainstorm conversation, extract:

### 1. User Insight (from User Day-In-Life)

The specific person, their context, their pain. This grounds all future decisions.

→ Write to `.feat-tree/memories/user.md`

```markdown
# User

**Who:** [Name, role, context]
**When problem appears:** [Specific moment in their day]
**Current workaround:** [What they do now]
**Pain:** [What's frustrating about it]
```

### 2. Scope Fence (from Scope Fence)

What we explicitly said NO to. Prevents scope creep in future sessions.

→ Write to `.feat-tree/memories/scope.md`

```markdown
# Scope

**This IS:** [One sentence]

**This is NOT:**
- [Explicit exclusion]
- [Explicit exclusion]

**Features we said no to:**
- [Feature]: [Why not]
```

### 3. Core Assumption (from Crux)

The ONE thing that must be true. Future sessions should validate this.

→ Update `.feat-tree/CONTEXT.md` Key Assumptions section

```markdown
## Key Assumptions
- [untested] [The core assumption] — test by [how to validate]
```

### 4. Risks (from Pre-Mortem)

How this fails. Future sessions should watch for warning signs.

→ Write to `.feat-tree/memories/risks.md`

```markdown
# Risks

**"It failed because..."**
1. [Failure mode] — Watch for: [early warning sign]
2. [Failure mode] — Watch for: [early warning sign]

**Mitigations:**
- [What we're doing to prevent]
```

### 5. Design Rationale (from Design phase)

WHY we chose this approach over alternatives. Prevents revisiting decisions.

→ Write to `.feat-tree/memories/decisions.md`

```markdown
# Design Decisions

**[Topic]:** [Choice]
- Considered: [Alternative 1], [Alternative 2]
- Chose because: [Why this fits better]
- Trade-off accepted: [What we gave up]
```

## Process

1. **Review brainstorm conversation** — What thinking happened that's NOT in the plan?
2. **Extract each category above** — Only if it was actually discussed
3. **Write to memory files** — Dense, not verbose
4. **Update CONTEXT.md** — If core assumptions or project understanding changed

## What NOT to Capture

- Stuff already in the plan (workflows, features, implementation order)
- Generic/speculative content (only capture what was actually discussed)
- Session-specific details that won't help future sessions

## Confirm

```
Synced brainstorm discoveries:
- memories/user.md — [created/updated]
- memories/scope.md — [created/updated]  
- memories/risks.md — [created/updated]
- memories/decisions.md — [created/updated]
- CONTEXT.md — [updated assumptions]

Future sessions will have this context.
```
