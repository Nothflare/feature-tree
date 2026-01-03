---
name: brainstorm
description: "Workflow-first design through collaborative dialogue. Use before creating features, building components, or modifying behavior. Finds actual intentions, not just surface requests."
---

# Feature Tree Brainstorming

Turn ideas into fully formed designs through collaborative dialogue. Focus on user experiences first, descend to implementation later.

## The Mentality

**Don't execute literally. Find the actual intention.**

User requests often contain surface symptoms, not root causes. Solutions they think they want, not what they need.

```
USER REQUEST
    ↓
SURFACE INTERPRETATION (what they said)
    ↓
ACTUAL INTENTION (why they said it)
    ↓
SMART SOLUTION (address the real need)
```

### Example

**User:** "Don't use emojis and gradient colors in the dashboard"

| Level | Content |
|-------|---------|
| Surface | Remove emojis, remove gradients |
| Intention | "The UI looks AI-designed and it's embarrassing" |
| Smart solution | Research good design principles → understand the project's vibe → propose a design language based on wisdom, not default AI aesthetics |

---

## Mind Tools

These are thinking tools, not scripts. Understand WHY they work, apply them when they fit.

---

### First Principle Reasoning

**WHY IT EXISTS:** People communicate in solutions, not problems. "Add a spinner" is a solution. The problem might be "page feels slow" — which has ten better solutions than a spinner. If you execute the solution without understanding the problem, you might build the wrong thing perfectly.

**THE INSIGHT:** There's always a gap between what someone says and what they mean. The gap isn't deception — it's just how humans communicate. They've already done the (often flawed) reasoning from problem to solution in their head, then handed you the conclusion.

**WHEN IT MATTERS:** User gives a specific request without explaining why. The request is a solution to an unstated problem.

**WHAT YOU'RE LOOKING FOR:** The actual intention. The frustration or desire that spawned the request. Once you find it, you can often propose something better than what they asked for.

---

### The Crux Finder

**WHY IT EXISTS:** Every project has a core bet — an assumption that if true means this works, if false means it doesn't. People bury this under months of building before testing it. They build auth systems and polish UIs before checking if anyone wants the core thing.

**THE INSIGHT:** Building feels productive. "Finding the crux" feels like stalling. But testing the wrong assumption efficiently is still waste. If the core bet is wrong, everything built on top of it is worthless.

**WHEN IT MATTERS:** Starting something new. Before significant investment. When there's implicit optimism that hasn't been examined.

**WHAT YOU'RE LOOKING FOR:** The ONE belief that everything else depends on. Then: how to test it with minimum investment before building.

---

### Pre-Mortem

**WHY IT EXISTS:** "What could go wrong?" triggers self-censorship. It feels pessimistic, disloyal, like you're not a team player. But "why did it fail?" is just forensics — analyzing something that already happened. The hypothetical framing gives social cover to say the uncomfortable things everyone suspects but nobody's saying.

**THE INSIGHT:** The psychological trick of past-tense framing unlocks honesty. People will say things in a pre-mortem they'd never say in a risk assessment.

**WHEN IT MATTERS:** After initial enthusiasm, before building. Before major commitments. When optimism is high and no one's playing devil's advocate.

**WHAT YOU'RE LOOKING FOR:** The failure modes people are secretly worried about. Early warning signs. Preventive measures that seem obvious once spoken but nobody was going to say.

---

### Scope Fence

**WHY IT EXISTS:** Most projects die of scope creep, not bad core ideas. Features accrete. "What if we also..." multiplies. Each addition seems small but they compound into a monster that never ships.

**THE INSIGHT:** Saying "we are NOT doing X" out loud creates permission to focus. It's almost physically relieving. The negative space defines the positive space. Explicit boundaries prevent implicit expansion.

**WHEN IT MATTERS:** When the feature list is growing. When "nice to have" is indistinguishable from "essential." When scope has never been explicitly discussed.

**WHAT YOU'RE LOOKING FOR:** The NOTs. What this explicitly isn't. What users you're okay losing. What features you're saying no to. The one-sentence answer to "what is this?"

---

### User Day-In-Life

**WHY IT EXISTS:** "Users" as an abstraction lets you build for imaginary people. You can convince yourself anyone would want anything if you never get specific. But when you pick a real person with a real name and walk through their real Tuesday, the bullshit evaporates. Either you can describe their day concretely or you can't — and if you can't, you don't understand your user yet.

**THE INSIGHT:** Specificity is a bullshit detector. If the exercise feels hard, that's information — you need to go learn about your users before designing for them.

**WHEN IT MATTERS:** When "users" is plural and vague. When the problem statement is abstract. When no one can describe WHO specifically has this problem and WHEN in their day it appears.

**WHAT YOU'RE LOOKING FOR:** A specific person (named), their context, WHEN the problem appears in their day, what they currently do about it, what's annoying about that. This person becomes the reference point for all design decisions.

---

## Two Planning Modes

### Forward Planning
**Journey → Flow → Feature**

Use when designing new experiences:
- "Users should be able to..."
- "I want to add..."
- "We need a way to..."

### Reverse Planning
**Problem → Solution → Feature**

Use when solving problems:
- "Users are struggling with..."
- "We need to fix..."
- "This is broken..."

**Detection:** Infer from user's request. If ambiguous, ask: "Are you designing a new experience (Forward) or solving a problem (Reverse)?"

---

## The Process

### Before Brainstorming

1. **Check Feature Tree context:**
   ```
   search_features("relevant keywords")
   search_workflows("relevant keywords")
   ```
2. **Present relevant context:** "I found these existing features/workflows that might relate..."

### During Brainstorming

**Conversation style:**
- Ask questions one at a time — don't overwhelm
- Prefer multiple choice when possible, open-ended when exploring
- Propose 2-3 approaches with trade-offs
- Lead with your recommended option and explain why

**Forward mode flow:**
1. Understand the journey — What's the user trying to achieve?
2. Map the flows — What steps does the user take?
3. Identify features — What capabilities support each flow?

**Reverse mode flow:**
1. Clarify the problem — What's broken or missing? Who's affected?
2. Design the solution — What experience solves this?
3. Identify features — What capabilities are needed?

**Throughout:**
- Apply mind tools when relevant (Crux Finder, Pre-Mortem, Scope Fence, User Day-In-Life)
- Explore technical decisions with rationale
- YAGNI ruthlessly — remove unnecessary features

### Presenting the Design

- Break into sections of 200-300 words
- Ask after each section: "Does this look right?"
- Include mermaid diagrams for flow clarity
- Be ready to go back and clarify

---

## Output Format

### Design Doc Structure

```markdown
# [Topic] Design

## Context
- What exists (from FT search)
- Why we're designing this

## [Journeys & Flows / Problem & Solution]

[Content based on mode]

### Flow Diagram

​```mermaid
graph TD
    A[User action] --> B[FEATURE.one]
    B --> C[FEATURE.two]
    C --> D[Outcome]
​```

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth method | JWT | Stateless, mobile-friendly |
| Storage | PostgreSQL | Relational, team knows it |

## Scope Fence

NOT doing:
- [Explicit exclusions]
- [Features we're saying no to]

## Features Identified

| ID | Name | Status | Notes |
|----|------|--------|-------|
| EXISTING.feature | ... | reuse | already exists |
| NEW.feature | ... | new | needs implementation |

## Open Questions
- [Unresolved items]
```

### What's in the Design Doc
- Workflows and flows with mermaid diagrams
- Technical decisions with rationale
- Scope fences (explicit "nots")
- Feature mapping

### What's NOT in the Design Doc
- File paths, folder structure
- Code snippets, function names
- Step-by-step implementation instructions

---

## After Design Approval

### 1. Save Design Doc

Write to `docs/plans/YYYY-MM-DD-<topic>-design.md`

(Plans are gitignored — don't commit)

### 2. Offer Feature Tree Population

```
Design saved. Create these in Feature Tree?

Workflows:
- USER_ONBOARDING.signup_flow
- USER_ONBOARDING.verify_flow

Features (new):
- AUTH.register
- AUTH.email_verify

Features (reuse):
- DB.user (exists)

[yes / no / review first]
```

If yes: Create with proper `depends_on` relationships and mermaid diagrams.

### 3. Sync Project Memory

If ft-mem plugin is installed:
```
Sync brainstorming discoveries to project memory?
(updates CONTEXT.md, captures decisions, scope fences, user insights)
```

→ Invoke `ft-mem:brainstorm-sync` skill if available
→ If skill not found, skip silently (ft-mem not installed)

### 4. Implementation Handoff

```
Ready to implement?
1. Start implementation now
2. Done for now
```

---

## Key Principles

1. **Workflow-first** — Human creativity at the abstract level, descend to features later

2. **Find actual intention** — Surface requests hide real needs; ask "why" gently

3. **Check before creating** — Search existing FT context, build on what exists

4. **One question at a time** — Don't overwhelm; prefer choices when possible

5. **Explore alternatives** — Always propose 2-3 approaches before settling

6. **Decisions, not speculation** — Capture choices with rationale, not implementation guesses

7. **Mermaid for clarity** — Visual diagrams help humans validate

8. **YAGNI ruthlessly** — Remove unnecessary features from all designs

9. **Incremental validation** — Present in sections, check each one

10. **Be flexible** — Go back and clarify when something doesn't fit
