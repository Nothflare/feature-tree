---
description: "Commit changes and update the feature tree"
---

1. Stage and commit current changes with a descriptive message
2. Push to remote (if configured)
3. Call update_feature() to record:
   - The commit hash(es) for the feature you worked on
   - Any new code_symbols discovered
   - Any new files touched
   - Update status if appropriate (e.g., planned → in-progress → done)
4. If this was a new feature, use add_feature() first
