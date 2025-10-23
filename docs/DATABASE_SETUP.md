# Database Setup Guide

This guide covers the simplified database setup process for the Survey Engine project.

## Overview

The database setup has been simplified to use a consolidated bootstrap approach:

- **Single Schema File**: `migrations/000_bootstrap_complete_schema.sql` contains all tables, indexes, and constraints
- **Idempotent Operations**: Safe to run multiple times without side effects
- **Manual Control**: Database operations are explicit and controlled

## Simplified Deployment Process

### Production (Railway)

**deploy.sh now only deploys code - database operations are manual:**

```bash
# 1. Deploy code
./deploy.sh

# 2. (Optional) Reset database if fresh start needed
# Set RESET_DATABASE=true before deploying, then run:
curl -X POST 'https://your-app.railway.app/api/v1/admin/reset-database?confirmation_code=DANGER_DELETE_ALL_DATA&force=true'

# 3. Bootstrap schema (idempotent - safe to run)
curl -X POST 'https://your-app.railway.app/api/v1/admin/migrate-all'

# 4. Seed data (after bootstrap)
python migrations/seed_core_generation_rules.py
python scripts/populate_rule_based_multi_level_rag.py
```

**Why manual?**

- Prevents accidental data loss
- Explicit control over database state
- Clear separation of code deployment vs database management

### Local Development

```bash
# 1. Start server
./start-local.sh

# 2. Bootstrap schema (first time or updates)
./start-local.sh migrate

# 3. Seed data (optional)
python migrations/seed_core_generation_rules.py
python scripts/populate_rule_based_multi_level_rag.py
```

## migrate-all Changes

The `/api/v1/admin/migrate-all` endpoint now calls the consolidated bootstrap:

- **Idempotent**: Safe to run multiple times
- **Simple**: Just executes `000_bootstrap_complete_schema.sql`
- **Fast**: No complex migration chains
- **Safe**: Uses `CREATE TABLE IF NOT EXISTS`

## Database Schema

The consolidated schema includes all 24 tables:

### Core Tables
- `rfqs` - Request for Quotations
- `surveys` - Generated surveys
- `edits` - Survey edit history

### Golden Example Tables
- `golden_rfq_survey_pairs` - Reference RFQ-survey pairs
- `golden_sections` - Reference survey sections
- `golden_questions` - Reference survey questions
- `golden_example_states` - Temporary state for golden example creation

### RAG Configuration
- `retrieval_weights` - RAG retrieval configuration
- `methodology_compatibility` - Methodology compatibility rules

### Rules and Validation
- `survey_rules` - Survey generation rules
- `rule_validations` - Rule validation results

### Annotations
- `question_annotations` - Question-level annotations
- `section_annotations` - Section-level annotations
- `survey_annotations` - Survey-level annotations

### Workflow Management
- `human_reviews` - Human review records
- `workflow_states` - Workflow state management

### Configuration
- `settings` - Application settings

### Document Management
- `document_uploads` - Document upload records
- `document_rfq_mappings` - Document to RFQ mappings

### LLM Audit
- `llm_audit` - LLM call audit trail
- `llm_hyperparameter_configs` - LLM configuration
- `llm_prompt_templates` - Prompt templates

### QNR Taxonomy
- `qnr_label_definitions` - QNR label definitions
- `qnr_tag_definitions` - QNR tag definitions

## Extensions

The schema enables these PostgreSQL extensions:

- `uuid-ossp` - UUID generation
- `pgcrypto` - Cryptographic functions
- `vector` - Vector similarity search (pgvector)

## Indexes

Performance indexes are included for:

- Primary keys (automatic)
- Foreign keys
- Frequently queried columns
- Vector similarity search columns

## Safety Features

### Bootstrap Safety
- Requires confirmation code: `BOOTSTRAP_DATABASE`
- Requires force flag: `force=true`
- Production environment protection

### Reset Safety
- Requires confirmation code: `DANGER_DELETE_ALL_DATA`
- Requires force flag: `force=true`
- Only available via environment variable in deploy.sh

## Troubleshooting

### Common Issues

1. **Schema Mismatch**: Run `migrate-all` to sync schema
2. **Missing Tables**: Bootstrap creates all tables idempotently
3. **Vector Search Issues**: Ensure pgvector extension is enabled

### Verification

Check database status:
```bash
curl https://your-app.railway.app/api/v1/admin/check-migration-status
```

Check health:
```bash
curl https://your-app.railway.app/api/v1/admin/health
```

## Migration Path

### For Existing Systems

**Railway**:
1. Deploy with new `./deploy.sh`
2. Run `migrate-all` (now calls bootstrap)
3. Continue normally

**Local**:
1. Run `./start-local.sh` (server starts)
2. Run `./start-local.sh migrate` if needed
3. Continue development

No breaking changes - just simpler and safer!

## Key Benefits

1. **Safety**: No accidental database operations
2. **Clarity**: Explicit database management
3. **Simplicity**: Scripts do one thing well
4. **Idempotent**: Bootstrap is safe to run repeatedly
5. **Fast Startup**: No waiting for migrations
6. **Fresh DB Support**: No pointless operations on empty database