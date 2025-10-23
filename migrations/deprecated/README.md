# Deprecated Migrations

## Overview

This directory contains **historical incremental migrations** (003-024) that were used to evolve the database schema over time. These migrations are **no longer used** in the current deployment process.

## Why Deprecated?

The Survey Engine project has migrated to a **consolidated bootstrap approach** using a single comprehensive schema file:

- **Current Schema**: `migrations/000_bootstrap_complete_schema.sql`
- **Source of Truth**: `src/database/models.py` (SQLAlchemy models)

This approach provides:
- ✅ Single source of truth for database schema
- ✅ Idempotent schema creation (safe to run multiple times)
- ✅ No complex migration chains or dependency issues
- ✅ Consistent schema across environments (local, staging, production)
- ✅ Faster deployment and setup

## Migration History

These files represent the evolution of the database schema from the project's beginning until the consolidation. They are kept for:

1. **Historical Reference**: Understanding how the schema evolved
2. **Debugging**: If issues arise related to old deployments
3. **Documentation**: Showing the progression of features

## Files in This Directory

### Schema Migrations (003-024)
- Incremental SQL scripts that added/modified tables and indexes
- Examples: `003_add_survey_rules.sql`, `012_add_llm_audit_system.sql`, `020_add_qnr_label_taxonomy.sql`

### Python Migrations
- Schema changes that required data transformation
- Examples: `add_labels_to_annotations.py`, `add_advanced_labeling_to_annotations.py`

### Fix Migrations
- Corrections to schema issues discovered during development
- Examples: `fix_survey_annotation_constraint.sql`, `015_fix_duplicate_rules.sql`

### Test Migrations
- Experimental or test migrations
- Example: `test_simple_migration.sql`

## Current Deployment Process

**DO NOT use these deprecated migrations for new deployments.**

Instead, follow the consolidated approach documented in `docs/DATABASE_SETUP.md`:

```bash
# 1. Bootstrap complete schema
POST /api/v1/admin/bootstrap-complete?confirmation_code=BOOTSTRAP_DATABASE&force=true

# 2. Seed data
python migrations/seed_core_generation_rules.py
python scripts/populate_rule_based_multi_level_rag.py
```

## If You Need to Reference These

If you're debugging an issue or need to understand a specific schema change:

1. **Find the migration** that made the change (by number or name)
2. **Compare with current schema** in `000_bootstrap_complete_schema.sql`
3. **Check SQLAlchemy models** in `src/database/models.py` for the current state

## Future Schema Changes

For new features or schema changes:

1. **Update** `src/database/models.py` (SQLAlchemy models)
2. **Update** `migrations/000_bootstrap_complete_schema.sql` (bootstrap schema)
3. **Test** locally with reset → bootstrap
4. **Deploy** to production (idempotent bootstrap)

Do **NOT** create new numbered migrations (025, 026, etc.).

## Last Consolidation Date

These migrations were consolidated on [date of consolidation] into version 1.0.0 of the bootstrap schema.

---

**For questions about the current schema or deployment process, see `docs/DATABASE_SETUP.md`.**

