# Plan: Add `uses` Field to Features

## Context

Feature Tree has two parallel trees:
- **Features** (atomic code units) - symbols, files, technical notes
- **Workflows** (user experiences) - depends_on features, mermaid diagrams

**Problem:** Rate limiters, caching, logging, auth middleware are shared infrastructure. Features use them, but there's no way to track this dependency.

## Solution

Add `uses` field to features (same pattern as workflows' `depends_on`).

**No new type field.** Use ID naming convention: `INFRA.*` for infrastructure.

```
AUTH.login uses [INFRA.rate_limiter, INFRA.redis_cache]
INFRA.rate_limiter used_by [AUTH.login, AUTH.register]
```

**The pattern:**
```
Workflows depends_on → Features uses → Features (infra)
```

All just dependency tracking at different layers.

## Current State (v1.3.0)

### Features Table
```sql
CREATE TABLE features (
    id TEXT PRIMARY KEY,
    parent_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'planned',
    code_symbols TEXT,
    files TEXT,
    technical_notes TEXT,
    commit_ids TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

## Implementation

### 1. Add `uses` field to features table

In `db.py` `_init_tables()`:
```sql
CREATE TABLE IF NOT EXISTS features (
    id            TEXT PRIMARY KEY,
    parent_id     TEXT REFERENCES features(id),
    name          TEXT NOT NULL,
    description   TEXT,
    status        TEXT DEFAULT 'planned',
    code_symbols  TEXT,
    files         TEXT,
    technical_notes TEXT,
    commit_ids    TEXT,
    uses          TEXT,  -- NEW: JSON array of feature IDs this feature uses
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Update db.py: add_feature

```python
def add_feature(
    self,
    id: str,
    name: str,
    parent_id: Optional[str] = None,
    description: Optional[str] = None,
    uses: Optional[list[str]] = None,  # NEW
    status: str = "planned"
) -> dict:
    now = datetime.now(UTC).isoformat()
    uses_json = json.dumps(uses) if uses else None  # NEW
    self.conn.execute(
        """INSERT INTO features (id, parent_id, name, description, uses, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (id, parent_id, name, description, uses_json, status, now, now)
    )
    # ... rest unchanged
```

### 3. Update db.py: update_feature

Add `uses` to the fields that can be updated:

```python
def update_feature(self, id: str, **fields) -> Optional[dict]:
    # Convert lists to JSON
    for key in ["code_symbols", "files", "commit_ids", "uses"]:  # ADD "uses"
        if key in fields and isinstance(fields[key], list):
            fields[key] = json.dumps(fields[key])
    # ... rest unchanged
```

### 4. Add db.py: get_features_using

```python
def get_features_using(self, feature_id: str) -> list[dict]:
    """Get features that use this feature (reverse lookup)."""
    rows = self.conn.execute(
        "SELECT * FROM features WHERE status != 'deleted'"
    ).fetchall()
    result = []
    for row in rows:
        f = dict(row)
        uses = json.loads(f.get("uses") or "[]")
        if feature_id in uses:
            result.append(f)
    return result
```

### 5. Update mcp_server.py: update_feature tool

```python
@mcp.tool()
def update_feature(
    id: str,
    status: str | None = None,
    code_symbols: list[str] | None = None,
    files: list[str] | None = None,
    commit_ids: list[str] | None = None,
    technical_notes: str | None = None,
    description: str | None = None,
    uses: list[str] | None = None  # NEW
) -> str:
    """Update a feature. ALWAYS record code_symbols + files after implementing. 1x effort now = 10x saved later."""
    db = get_db()
    try:
        fields = {}
        if status is not None:
            fields["status"] = status
        if code_symbols is not None:
            fields["code_symbols"] = code_symbols
        if files is not None:
            fields["files"] = files
        if commit_ids is not None:
            fields["commit_ids"] = commit_ids
        if technical_notes is not None:
            fields["technical_notes"] = technical_notes
        if description is not None:
            fields["description"] = description
        if uses is not None:  # NEW
            fields["uses"] = uses

        db.update_feature(id, **fields)
        regenerate_markdown()
        return '{"ok":true}'
    finally:
        db.close()
```

### 6. Update mcp_server.py: get_feature tool

```python
@mcp.tool()
def get_feature(id: str) -> str:
    """Get full details of a single feature by ID, including linked workflows and used features."""
    db = get_db()
    try:
        feature = db.get_feature(id)
        if feature:
            # Add linked workflows
            workflows = db.get_workflows_for_feature(id)
            feature["linked_workflows"] = [
                {"id": w["id"], "name": w["name"]}
                for w in workflows
            ]

            # NEW: Add features this feature uses
            if feature.get("uses"):
                uses_ids = json.loads(feature["uses"])
                feature["uses_features"] = [
                    {"id": f["id"], "name": f["name"]}
                    for uid in uses_ids
                    if (f := db.get_feature(uid))
                ]

            # NEW: Add features that use this feature (reverse lookup)
            used_by = db.get_features_using(id)
            if used_by:
                feature["used_by_features"] = [
                    {"id": f["id"], "name": f["name"]}
                    for f in used_by
                ]

            return json.dumps(feature, default=str)
        return '{"ok":false,"error":"not found"}'
    finally:
        db.close()
```

### 7. Update SERVER_INSTRUCTIONS

Add to the instructions:

```python
## INFRASTRUCTURE

Use naming convention `INFRA.*` for shared utilities (rate limiter, cache, etc.)

Features can declare `uses` to link to other features they depend on:
- AUTH.login uses [INFRA.rate_limiter]
- get_feature shows both `uses_features` and `used_by_features`

No separate "infra type" - just features with INFRA.* IDs.
```

### 8. Update search_features output (optional)

Could include `uses` count in trimmed output, but probably not needed.

## Files to Modify

1. **`feature-tree/feature_tree/db.py`**
   - Add `uses` column to features table schema
   - Update `add_feature()` to accept uses param
   - Update `update_feature()` to handle uses in JSON conversion
   - Add `get_features_using()` method for reverse lookup

2. **`feature-tree/feature_tree/mcp_server.py`**
   - Update `update_feature()` tool to accept uses param
   - Update `get_feature()` tool to show uses_features and used_by_features
   - Update SERVER_INSTRUCTIONS to document INFRA convention

3. **`README.md`**
   - Document `uses` field and INFRA.* convention

## Example Usage

```python
# Add infrastructure
add_feature(id="INFRA.rate_limiter", name="Rate Limiter")
add_feature(id="INFRA.redis_cache", name="Redis Cache")

# Add feature that uses infra
add_feature(id="AUTH.login", name="User Login")
update_feature(id="AUTH.login", uses=["INFRA.rate_limiter", "INFRA.redis_cache"])

# Query shows bidirectional links
get_feature("AUTH.login")
# → {
#     "id": "AUTH.login",
#     "uses": "[\"INFRA.rate_limiter\", \"INFRA.redis_cache\"]",
#     "uses_features": [
#       {"id": "INFRA.rate_limiter", "name": "Rate Limiter"},
#       {"id": "INFRA.redis_cache", "name": "Redis Cache"}
#     ],
#     "linked_workflows": [...]
#   }

get_feature("INFRA.rate_limiter")
# → {
#     "id": "INFRA.rate_limiter",
#     "used_by_features": [
#       {"id": "AUTH.login", "name": "User Login"}
#     ]
#   }
```

## Version

Bump to `1.4.0` after implementation.

## Test Checklist

- [ ] add_feature with uses param works
- [ ] update_feature with uses param works
- [ ] get_feature shows uses_features (forward lookup)
- [ ] get_feature shows used_by_features (reverse lookup)
- [ ] INFRA.* naming convention documented
- [ ] Existing features without uses still work (backward compat)
