# Annotation RAG Integration - Implementation Complete

## Overview

This implementation integrates human-annotated survey questions and sections into the multi-level RAG (Retrieval-Augmented Generation) system. The system now automatically syncs high-quality, human-verified questions and sections from annotations to the RAG tables for use in survey generation.

## Key Features

### 1. Real-Time Sync
- **Automatic Sync**: When users annotate questions/sections, they are automatically added to the RAG system
- **No Manual Intervention**: Sync happens in the background during annotation save
- **Non-Blocking**: Sync failures don't block annotation saves

### 2. Quality-Based Prioritization
- **Quality Scores**: Derived from annotation metadata (1-5 scale → 0.0-1.0)
- **Human Verification Boost**: +0.2 for human-verified annotations
- **Label-Based Boost**: +0.1 for positive quality labels
- **Capped at 1.0**: Ensures scores stay within bounds

### 3. Deduplication
- **Smart Matching**: Prevents duplicate entries for the same question/section
- **Update on Conflict**: Updates existing entries instead of creating duplicates
- **Tracks Source**: Links back to annotation via `annotation_id` foreign key

## Implementation Details

### Database Schema

#### New Fields in `golden_questions` and `golden_sections`:
```sql
-- Links to source annotation
annotation_id INTEGER REFERENCES {question|section}_annotations(id) ON DELETE SET NULL

-- Indexed for fast lookups
CREATE INDEX idx_golden_questions_annotation ON golden_questions(annotation_id);
CREATE INDEX idx_golden_sections_annotation ON golden_sections(annotation_id);
```

### Core Service: `AnnotationRAGSyncService`

**Location**: `src/services/annotation_rag_sync_service.py`

**Key Methods**:
- `sync_question_annotation(annotation_id)` - Syncs a question annotation to RAG
- `sync_section_annotation(annotation_id)` - Syncs a section annotation to RAG
- `_calculate_quality_score(annotation)` - Derives quality score from annotation
- `_extract_question_from_survey(survey_data, question_id)` - Extracts question from survey JSON
- `_extract_section_from_survey(survey_data, section_id)` - Extracts section from survey JSON

**Quality Score Formula**:
```python
base_score = (annotation.quality - 1) / 4.0  # Normalize 1-5 to 0.0-1.0
if annotation.human_verified:
    base_score += 0.2
if has_positive_labels:
    base_score += 0.1
quality_score = min(1.0, base_score)
```

### Real-Time Hooks

**Location**: `src/api/annotations.py`

**Endpoint**: `POST /api/v1/annotations/survey/{survey_id}/bulk`

**Integration Point**: After successful annotation save, syncs to RAG:
```python
# After db.commit() of annotations
sync_service = AnnotationRAGSyncService(db)

for qa in question_annotations:
    if qa.annotator_id == "current-user":  # Only human annotations
        await sync_service.sync_question_annotation(qa.id)

for sa in section_annotations:
    if sa.annotator_id == "current-user":  # Only human annotations
        await sync_service.sync_section_annotation(sa.id)
```

### Admin Endpoint for Batch Sync

**Endpoint**: `POST /api/v1/admin/sync-annotations-to-rag`

**Purpose**: One-time batch operation to sync all existing annotations

**Usage**:
```bash
curl -X POST http://localhost:8000/api/v1/admin/sync-annotations-to-rag
```

**Returns**:
```json
{
  "status": "success",
  "message": "Synced 15 questions and 8 sections to RAG",
  "question_annotations_processed": 15,
  "section_annotations_processed": 8,
  "questions_synced": 15,
  "sections_synced": 8,
  "errors": []
}
```

## Migration

### Migration File
**Location**: `migrations/add_annotation_id_to_golden_tables.sql`

**Changes**:
- Adds `annotation_id` column to `golden_questions`
- Adds `annotation_id` column to `golden_sections`
- Creates indexes for fast lookups
- Adds column comments for documentation

### Running Migration

**Local**:
```bash
curl -X POST http://localhost:8000/api/v1/admin/migrate-all
```

**Production** (Railway):
```bash
./deploy.sh --auto-migrate --clean
```

The migration is included in Step 12 of the `migrate-all` endpoint and runs automatically.

## Testing

### Test Script
**Location**: `test_annotation_rag_sync.py`

**Run**:
```bash
python test_annotation_rag_sync.py
```

**Tests**:
1. Checks for existing annotations
2. Syncs a question annotation and verifies
3. Syncs a section annotation and verifies
4. Checks overall RAG data statistics
5. Verifies quality score calculation

### Manual Testing

1. **Annotate a survey question**:
   - Go to Annotation Page in frontend
   - Annotate a question with quality score 5
   - Mark as human-verified
   - Save

2. **Verify sync**:
```bash
# Check golden_questions table
curl http://localhost:8000/api/v1/admin/check-migration-status
```

3. **Test retrieval**:
   - Generate a new survey
   - Check if the annotated question appears in context

## Data Flow

### Annotation → RAG Flow

```
User Annotates Question
        ↓
Frontend saves via POST /api/v1/annotations/survey/{id}/bulk
        ↓
Backend saves annotation to question_annotations table
        ↓
Real-time hook: AnnotationRAGSyncService.sync_question_annotation()
        ↓
Extract question from survey.final_output
        ↓
Calculate quality score from annotation
        ↓
Create/update entry in golden_questions table
        ↓
Link via annotation_id foreign key
```

### Survey Generation → RAG Flow

```
User submits RFQ
        ↓
Workflow: GoldenRetrieverNode
        ↓
RetrievalService.retrieve_golden_questions()
        ↓
RuleBasedMultiLevelRAGService (for sections/questions)
        ↓
Query golden_questions with rule-based matching
        ↓
Include annotation-sourced questions in context
        ↓
Prioritize by quality_score (which includes annotation metadata)
        ↓
Generate survey with high-quality annotated examples
```

## Configuration

### Only Human Annotations
The system only syncs annotations with `annotator_id == "current-user"` to ensure only human-verified content is used.

### Sync on Save
Sync happens automatically on every annotation save. No configuration needed.

### Error Handling
- Sync failures are logged but don't block annotation saves
- Failed syncs are reported in response but don't return 500 errors
- Graceful degradation: System continues working even if sync fails

## Production Deployment

### Prerequisites
1. Backend deployed to Railway
2. Database migrations applied
3. Golden pairs bootstrapped

### Deployment Steps

1. **Deploy with migration**:
```bash
./deploy.sh --auto-migrate --clean
```

2. **Verify migration**:
```bash
curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status
```

3. **Batch sync existing annotations** (one-time):
```bash
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/sync-annotations-to-rag
```

4. **Test annotation sync**:
   - Annotate a question in production
   - Check logs for "✅ Synced question {id}"
   - Verify entry in golden_questions table

## Monitoring

### Logs to Watch
- `🔗 [API] Syncing annotations to RAG tables...` - Sync started
- `✅ Synced question {id}: {action}` - Question synced successfully
- `✅ Synced section {id}: {action}` - Section synced successfully
- `⚠️ Failed to sync question {id}: {error}` - Sync failed (non-fatal)

### Database Queries

**Check annotation-sourced RAG entries**:
```sql
-- Questions from annotations
SELECT COUNT(*) FROM golden_questions WHERE annotation_id IS NOT NULL;

-- Sections from annotations
SELECT COUNT(*) FROM golden_sections WHERE annotation_id IS NOT NULL;

-- Quality distribution
SELECT quality_score, COUNT(*) 
FROM golden_questions 
WHERE annotation_id IS NOT NULL 
GROUP BY quality_score 
ORDER BY quality_score DESC;
```

## Benefits

### For Researchers
- **Immediate Impact**: Annotations instantly improve future surveys
- **Quality Feedback Loop**: Good examples propagate automatically
- **No Extra Work**: Sync happens in background

### For System
- **Dynamic Learning**: RAG system continuously improves
- **Human Curation**: Only verified, high-quality examples
- **Traceability**: Can track back to source annotation

### For Survey Quality
- **Better Context**: More relevant examples in prompts
- **Human-Verified**: Examples vetted by researchers
- **Domain-Specific**: Annotations capture domain expertise

## Future Enhancements

1. **Pillar-Based Scoring**: Incorporate pillar scores into quality calculation
2. **Label-Based Filtering**: Filter by specific annotation labels
3. **Time-Based Decay**: Reduce weight of older annotations
4. **Explicit Quality Gates**: Only sync annotations above threshold
5. **Annotation Feedback**: Show researchers impact of their annotations

## Troubleshooting

### Sync Not Working

**Check**:
1. Migration applied: `annotation_id` column exists
2. Annotations saved with `annotator_id == "current-user"`
3. Survey has `final_output` with questions/sections
4. Logs show sync attempts

### Quality Scores Incorrect

**Verify**:
1. Annotation quality field (1-5)
2. Human verified flag
3. Labels array
4. Formula: `(quality-1)/4.0 + 0.2*human_verified + 0.1*has_positive_labels`

### Duplicate Entries

**Should Not Happen**:
- Deduplication checks `survey_id` + `question_id`/`section_id`
- Updates existing entry instead of creating new one

## Summary

The Annotation RAG Integration provides:

✅ **Real-time sync** of annotations to RAG tables  
✅ **Quality-based prioritization** with human verification boost  
✅ **Automatic deduplication** to prevent duplicates  
✅ **Batch migration** for existing annotations  
✅ **Non-blocking** error handling  
✅ **Production-ready** with comprehensive testing  

This completes the human-in-the-loop quality improvement system, ensuring that researcher feedback directly enhances future survey generation.


