---
name: understand
description: "Build global awareness of codebase via workflows and features. Use when onboarding to a project or needing to understand the big picture."
---

# Understand Codebase

Build a mental model of the entire codebase through Feature Tree's workflows and features.

**Announce at start:** "I'm using the feature-tree:understand skill to build global awareness."

---

## When to Use

- Starting work on an unfamiliar codebase
- Need to understand how features connect
- Looking for the "right place" to make a change
- User asks "how does X work?" or "where should I put Y?"

---

## The Process

### Step 1: Load All Workflows

```
search_workflows("*")
```

Workflows represent user-facing experiences. They show HOW features compose into journeys.

### Step 2: Rank by Importance

Identify the most important workflows:
- **Most features referenced** — Complex, central to the system
- **Entry points** — User-facing starting points
- **Revenue-critical** — Checkout, payment, subscription flows

### Step 3: Present Tree View

Show the user a hierarchical view:

```
USER_ONBOARDING (4 features)
├── signup_flow → AUTH.register, EMAIL.verify, DB.user
└── login_flow → AUTH.login, AUTH.session

CHECKOUT (6 features)
├── cart_flow → CART.add, CART.update, CART.remove
└── payment_flow → PAYMENTS.process, PAYMENTS.refund

INFRA (shared by many)
├── INFRA.database — used by 12 features
├── INFRA.logger — used by 8 features
└── INFRA.rate_limiter — used by 5 features
```

### Step 4: Ask User

"Which area should I explore deeper?"

Options:
- A specific workflow (e.g., "checkout")
- A specific feature (e.g., "AUTH.login")
- Infrastructure (INFRA.*)
- "Show me everything"

### Step 5: Deep Dive

For the selected area:

1. **Get each feature:**
   ```
   get_feature("AUTH.login")
   get_feature("AUTH.session")
   ```

2. **Trace data flow:**
   - What files are involved?
   - What symbols handle the logic?
   - What does this feature depend on?
   - What depends on this feature?

3. **Build understanding:**
   - Entry points (routes, handlers, commands)
   - Data transformations
   - External dependencies
   - Error handling patterns

4. **Report findings:**
   - Architecture summary
   - Key files and symbols
   - Dependencies and impact
   - Patterns used

---

## Output Format

After exploration, provide:

```
## Codebase Understanding

### Architecture Overview
[High-level description of how the system is organized]

### Key Workflows
| Workflow | Purpose | Features |
|----------|---------|----------|
| USER.login_flow | User authentication | AUTH.login, AUTH.session |
| ... | ... | ... |

### Infrastructure (INFRA.*)
| Feature | Used By | Purpose |
|---------|---------|---------|
| INFRA.database | 12 features | PostgreSQL connection pool |
| ... | ... | ... |

### Key Patterns
- [Pattern 1: e.g., "All API routes use middleware chain"]
- [Pattern 2: e.g., "Errors bubble up through Result types"]

### Recommended Starting Points
For [user's goal], start with:
1. `get_feature("X")` — [why]
2. Read `path/to/file.ts` — [why]
```

---

## Integration

**After understanding:**
- Use insights to guide implementation
- Reference features when making changes
- Check impact before modifying INFRA.*

**If Feature Tree is empty:**
- Suggest running `/feature-tree:bootstrap` first
- Or manually create features as you explore
