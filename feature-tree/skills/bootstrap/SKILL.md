---
name: bootstrap
description: Scan codebase by tracing workflows. Discovers features as components of real user journeys/flows.
---

# Bootstrap from Existing Codebase

Discover features by tracing workflows through code. Scan by workflow, not by feature.

## Process

### Step 1: Collect Workflows

Ask the user to describe workflows to trace:

```
What workflows should I trace through the codebase?

Examples:
- "User signup and email verification"
- "Checkout flow from cart to payment"
- "Admin creates new product"

List them (one per line), or describe a journey with multiple flows.
```

For each workflow, clarify:
- Is this a **journey** (user goal) or **flow** (specific steps)?
- Entry point if known (optional)

### Step 2: Parallel Scanning

For each workflow, spawn a subagent using Task():

```python
Task(
    subagent_type="Explore",
    prompt=f"""
Trace this workflow through the codebase: "{workflow_name}"

Your job:
1. Find the entry point (route, handler, component)
2. Follow the code path step by step
3. Note each distinct feature/component encountered
4. Stop at external boundaries (DB, APIs) - these are atomic features

For each feature found, record:
- id: kebab-case identifier (e.g., "auth-email-verify")
- name: Human readable name
- files: List of files involved
- code_symbols: Key functions/classes

Return JSON:
{{
  "workflow": {{
    "id": "{workflow_id}",
    "name": "{workflow_name}",
    "type": "flow",
    "depends_on": ["feature-id-1", "feature-id-2", ...]
  }},
  "features": [
    {{"id": "...", "name": "...", "files": [...], "code_symbols": [...]}},
    ...
  ]
}}
"""
)
```

Launch all subagents in parallel (single message with multiple Task() calls).

### Step 3: Aggregate Results

Collect results from all subagents:
1. Merge feature lists
2. Deduplicate by id (same feature used in multiple workflows)
3. Build complete picture

### Step 4: Present for Approval

Show the user:

```markdown
## Discovered Workflows

### 1. User Signup Flow
- **Type:** flow
- **Depends on:** auth-register, auth-email-verify, db-user-create

### 2. Checkout Flow
- **Type:** flow
- **Depends on:** cart-get, payment-stripe, order-create

## Discovered Features

| ID | Name | Files |
|----|------|-------|
| auth-register | User Registration | src/auth/register.ts |
| auth-email-verify | Email Verification | src/auth/verify.ts |
| payment-stripe | Stripe Payment | src/payment/stripe.ts |
...

**Review:**
- Any workflows missing?
- Any features misnamed or should be split/merged?
- Ready to create?
```

### Step 5: Create

After user approval:

1. Check existing features: `search_features("*")` to avoid duplicates
2. Create features first (in dependency order if possible)
3. Create workflows with depends_on referencing feature IDs

```python
# For each new feature
add_feature(id="auth-register", name="User Registration", description="...")

# For each workflow
add_workflow(
    id="signup-flow",
    name="User Signup Flow",
    type="flow",
    depends_on=["auth-register", "auth-email-verify", "db-user-create"]
)
```

## Guidelines

- **Atomic features**: "Calls Stripe API" is one feature, don't decompose further
- **Deduplication**: Check before creating - same feature may appear in multiple workflows
- **Files + Symbols**: Always record which files and code symbols implement a feature
- **User guides**: If Claude can't find entry point, ask user for hints
- **Iterative**: Can run multiple times to discover more workflows
