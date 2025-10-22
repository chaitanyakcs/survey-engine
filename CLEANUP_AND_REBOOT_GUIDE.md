# Survey Engine - Cleanup and Reboot Guide

This document provides a step-by-step guide for completely cleaning up and rebooting the Survey Engine database and application using the admin APIs.

## 🚨 **Important Notes**

- **This process will DELETE ALL DATA** - use only when you need a fresh start
- **Backup any important data** before proceeding
- **All API calls should be made to the production environment**: `https://survey-engine-production.up.railway.app`
- **Wait 2-3 minutes** between deployment and API calls to ensure the server is fully started

## 🛡️ **Safety Features**

The cleanup operations are protected with multiple safety layers to prevent accidental execution:

1. **Confirmation Codes Required**: Must provide specific confirmation codes
2. **Force Flags Required**: Must explicitly set force=true
3. **Production Protection**: Blocked in production unless `ALLOW_DANGEROUS_OPERATIONS=true`
4. **LLM Protection**: Designed to prevent accidental AI execution

### Get Safety Information
```bash
curl https://survey-engine-production.up.railway.app/api/v1/admin/safety-info
```

## 📋 **Complete Cleanup and Reboot Process**

### Step 1: Reset Database (Complete Data Wipe)
```bash
curl -X POST "https://survey-engine-production.up.railway.app/api/v1/admin/reset-database?confirmation_code=DANGER_DELETE_ALL_DATA&force=true"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Database reset completed - all tables and data deleted",
  "reset_completed": true
}
```

**Safety Requirements:**
- `confirmation_code=DANGER_DELETE_ALL_DATA` (exact string required)
- `force=true` (boolean flag required)

### Step 2: Bootstrap Complete Database Schema
```bash
curl -X POST "https://survey-engine-production.up.railway.app/api/v1/admin/bootstrap-complete?confirmation_code=BOOTSTRAP_DATABASE&force=true"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Complete database bootstrap completed - all tables, indexes, and default data created",
  "bootstrap_completed": true,
  "tables_created": [
    "rfqs", "surveys", "golden_rfq_survey_pairs", "survey_rules",
    "golden_sections", "golden_questions", "llm_audit",
    "llm_hyperparameter_configs", "llm_prompt_templates",
    "retrieval_weights", "methodology_compatibility",
    "question_annotations", "section_annotations", "survey_annotations",
    "human_reviews", "document_uploads"
  ],
  "extensions_enabled": ["vector", "pgcrypto"],
  "indexes_created": "performance indexes for all major tables",
  "default_data_inserted": "retrieval weights, LLM configs, prompt templates"
}
```

### Step 3: Seed Retrieval Weights Configuration
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-retrieval-weights
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Retrieval weights seeding completed - methodology and industry weights added",
  "weights_seeded": {
    "methodology_weights": 8,
    "industry_weights": 6,
    "total_weights": 14
  },
  "seeding_completed": true
}
```

### Step 4: Seed Methodology Compatibility Matrix
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-methodology-compatibility
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Methodology compatibility seeding completed - compatibility pairs added",
  "compatibility_pairs_seeded": 12,
  "seeding_completed": true
}
```

### Step 5: Seed Methodology Rules
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-methodology-rules
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Methodology rules seeding completed - 7 methodology types added",
  "methodologies_seeded": [
    "van_westendorp", "conjoint", "maxdiff", "nps", 
    "csat", "brand_tracking", "pricing_research"
  ],
  "seeding_completed": true
}
```

### Step 6: Populate Multi-Level RAG (Optional, after adding golden pairs)
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/populate-multi-level-rag
```

**Note:** This step is only needed if you have existing golden pairs that were added before automatic population was enabled. New golden pairs will automatically populate multi-level RAG.

**Expected Response:**
```json
{
  "status": "success",
  "message": "Multi-level RAG population completed - created X sections and Y questions",
  "sections_created": X,
  "questions_created": Y,
  "golden_pairs_processed": Z
}
```

### Step 7: Run Complete Migration (Alternative to Steps 3-5)
**Note:** This is an alternative to steps 3-5 above. Use either the individual seeding steps OR this complete migration.

```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all
```

**Expected Response:**
```json
{
  "status": "partial",
  "message": "Database migration completed with some failures",
  "migration_results": [
    // Array of migration step results
  ],
  "summary": {
    "total_migrations": 18,
    "successful_migrations": 14,
    "failed_migrations": 4
  },
  "railway_ready": false
}
```

## 🔍 **Verification Steps**

### Check Database Health
```bash
curl https://survey-engine-production.up.railway.app/api/v1/admin/health
```

### Verify Migration Status
```bash
curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status
```

### Check Seeded Data
```bash
# Check retrieval weights count
curl -s "https://survey-engine-production.up.railway.app/api/v1/retrieval-weights/" | jq 'length'

# Check methodology compatibility count
curl -s "https://survey-engine-production.up.railway.app/api/v1/retrieval-weights/methodology-compatibility" | jq 'length'

# Check methodology rules count
curl -s "https://survey-engine-production.up.railway.app/api/v1/rules/methodology-rules" | jq 'length'

# Check generation rules count
curl -s "https://survey-engine-production.up.railway.app/api/v1/rules/generation-rules" | jq 'length'
```

### Test Core API Functionality
```bash
# Test surveys list (should return empty array)
curl https://survey-engine-production.up.railway.app/api/v1/survey/list

# Test RFQs list (should return empty array)
curl https://survey-engine-production.up.railway.app/api/v1/rfq/list
```

## 🚀 **Complete One-Line Script**

For convenience, here's a complete script that runs all the necessary steps:

```bash
#!/bin/bash
echo "🧹 Starting Survey Engine Cleanup and Reboot Process..."

echo "Step 1: Resetting database..."
curl -X POST "https://survey-engine-production.up.railway.app/api/v1/admin/reset-database?confirmation_code=DANGER_DELETE_ALL_DATA&force=true"

echo -e "\nStep 2: Bootstrapping complete database schema..."
curl -X POST "https://survey-engine-production.up.railway.app/api/v1/admin/bootstrap-complete?confirmation_code=BOOTSTRAP_DATABASE&force=true"

echo -e "\nStep 3: Seeding retrieval weights..."
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-retrieval-weights

echo -e "\nStep 4: Seeding methodology compatibility..."
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-methodology-compatibility

echo -e "\nStep 5: Seeding methodology rules..."
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/seed-methodology-rules

echo -e "\nStep 6: Populating multi-level RAG (optional)..."
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/populate-multi-level-rag

echo -e "\nStep 7: Verifying database health..."
curl https://survey-engine-production.up.railway.app/api/v1/admin/health

echo -e "\n✅ Cleanup and reboot process completed!"
```

## 📊 **Expected Final State**

After completing the cleanup and reboot process, your Survey Engine should have:

- **15 Retrieval Weights**: 8 methodology-specific + 6 industry-specific + 1 global default
- **12 Methodology Compatibility Pairs**: Cross-methodology compatibility scores
- **7 Methodology Rules**: Complete methodology definitions with validation rules
- **58 Generation Rules**: Core AiRA v1 framework rules
- **16 Database Tables**: All core application tables with proper schema
- **pgvector Extension**: Enabled for vector similarity search
- **Performance Indexes**: Optimized for all major tables

## ⚠️ **Troubleshooting**

### If API calls fail with safety violations:
```json
{
  "error": "Invalid confirmation code",
  "message": "To reset the database, you must provide confirmation_code='DANGER_DELETE_ALL_DATA'",
  "safety_required": true
}
```
**Solution**: Use the exact confirmation codes and force flags as shown in the examples.

### If API calls fail with production protection:
```json
{
  "error": "Production environment protection",
  "message": "Database reset is blocked in production environment",
  "safety_required": true
}
```
**Solution**: Set environment variable `ALLOW_DANGEROUS_OPERATIONS=true` in your Railway environment.

### If API calls fail with connection errors:
1. Wait 2-3 minutes for the server to fully start after deployment
2. Check if the service is running: `curl https://survey-engine-production.up.railway.app/api/v1/admin/health`

### If seeding fails:
1. Check the error message in the response
2. Ensure the previous step completed successfully
3. Try running individual seeding steps instead of migrate-all

### If database is in inconsistent state:
1. Run the reset-database step again with proper safety parameters
2. Follow the complete process from the beginning

## 🔄 **Regular Maintenance**

For regular maintenance (without full data wipe), use:
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all
```

This will run incremental migrations without deleting existing data.

---

**Last Updated:** October 21, 2025  
**Version:** 1.0  
**Environment:** Production (Railway)
