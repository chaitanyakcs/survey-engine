<!-- a58b349b-1485-4520-8775-228657bebe8c cfb27b61-9a60-4ca2-a8e8-4493ebc61b6a -->
# Golden Question Card UI Redesign & Usage Tracking

## Overview

Redesign the golden question card UI to remove clutter, fix misleading quality scores, implement proper usage tracking for individual questions with survey audit trail, and add "Recently Used" feature.

## Phase 1: Database Schema Changes

### 1.1 Create Usage Tracking Tables

Create new migration file `migrations/013_add_golden_content_usage_tracking.sql`:

- Add `golden_question_usage` table to track question→survey relationships
- Fields: id, golden_question_id (FK), survey_id (FK), used_at (timestamp)
- Add indexes for efficient queries (golden_question_id, survey_id, used_at)
- Add `golden_section_usage` table to track section→survey relationships
- Fields: id, golden_section_id (FK), survey_id (FK), used_at (timestamp)
- Add indexes for efficient queries (golden_section_id, survey_id, used_at)

### 1.2 Update Survey Model

Modify `src/database/models.py`:

- Add `used_golden_questions` field to Survey model (array of UUIDs, similar to `used_golden_examples`)
- Add `used_golden_sections` field to Survey model (array of UUIDs)

## Phase 2: Backend Implementation

### 2.1 Implement Usage Tracking Service

Modify `src/services/retrieval_service.py` or create new tracking utility:

- Add function to increment `usage_count` for golden questions when they're retrieved/used
- Add function to record usage in `golden_question_usage` table with survey_id and timestamp
- Track both questions and sections during prompt building

### 2.2 Add Usage History API Endpoint

Add to `src/api/golden.py`:

- New endpoint: `GET /api/v1/golden/questions/{question_id}/usage`
- Returns list of surveys that used this question with dates
- Include survey title, RFQ title, and generation date
- Limit to recent 10 usages by default, with optional limit parameter

### 2.3 Update Golden Questions List API

Modify existing endpoint in `src/api/golden.py`:

- Add optional `last_used_at` field to GoldenQuestion response (most recent usage date)
- Can be populated via LEFT JOIN to golden_question_usage table

## Phase 3: Frontend Type & API Updates

### 3.1 Update TypeScript Types

Modify `frontend/src/types/index.ts`:

- Add `last_used_at?: string` to GoldenQuestion interface
- Create new `QuestionUsage` interface for usage history items
- Fields: survey_id, survey_title, rfq_title, used_at

### 3.2 Add API Service Methods

Modify `frontend/src/services/api.ts`:

- Add `getGoldenQuestionUsage(questionId: string)` method
- Returns Promise<QuestionUsage[]>

## Phase 4: UI Component Redesign

### 4.1 Redesign GoldenQuestionsList.tsx Card Layout

File: `frontend/src/components/GoldenQuestionsList.tsx` (lines 210-331)

**Remove from header:**

- Large "Question {question.question_id}" title

**New compact header design:**

- Small badge with question_id (smaller font, subtle styling)
- Add copy-to-clipboard icon button next to question_id badge
- Keep human_verified and annotation_id badges

**Quality Score display (lines 301-310):**

- Only show quality score section if `quality_score !== null && quality_score !== undefined`
- When quality score exists AND annotation_id exists, show "From Annotation #{annotation_id}" tooltip on hover

**Methodology tags (lines 283-296):**

- Show only first 2 tags inline
- Add "+N more" badge that shows tooltip on hover with all remaining tags
- Use Heroicons InformationCircleIcon for hover indicator

**Add "Recently Used" section:**

- Show last_used_at date if available (e.g., "Last used: 2 days ago")
- Add "View usage history" link that opens modal
- Use relative time formatting (e.g., "2 hours ago", "3 days ago")

### 4.2 Create QuestionUsageModal Component

New file: `frontend/src/components/QuestionUsageModal.tsx`

- Modal that displays usage history for a question
- Shows table with: Survey Title, RFQ Title, Date Used
- Click on survey to navigate to that survey
- Loading state while fetching usage data
- Empty state for unused questions

### 4.3 Add Zustand Store Methods

Modify `frontend/src/store/useAppStore.ts`:

- Add `fetchQuestionUsage(questionId: string)` method
- Add `questionUsageHistory` state (map of questionId → usage array)
- Add loading state for usage fetching

## Phase 5: Integration & Testing

### 5.1 Wire Up Tracking in Workflow

Modify survey generation workflow to track question usage:

- In `src/workflows/workflow.py` or relevant node
- After survey generation, extract question IDs that were actually used
- Call tracking service to record usage

### 5.2 Update Migration Endpoint

Modify `src/api/admin.py`:

- Ensure new migration can be run via admin API

## Implementation Notes

**Quality Score Logic:**

- Only display when `question.quality_score !== null && question.quality_score !== undefined`
- Show "From Annotation" badge only when both quality_score AND annotation_id exist
- This indicates the score came from human annotation, not AI

**Question ID Copy:**

- Use browser Clipboard API
- Show brief toast/notification on successful copy
- Fallback for older browsers

**Methodology Tags Hover:**

- Use Tailwind's group-hover utilities
- Show tooltip with all tags on hover over "+N more" badge
- Keep first 2 tags always visible

**Usage Tracking:**

- Track at survey finalization (when status changes to 'validated' or 'final')
- Atomic operation - if survey creation fails, usage shouldn't be recorded
- Handle duplicate tracking gracefully (idempotent)

### To-dos

- [ ] Create migration for golden_question_usage table and update Survey model fields
- [ ] Implement usage tracking service and integrate with workflow
- [ ] Add usage history API endpoint and update golden questions list endpoint
- [ ] Update TypeScript types and add API service methods
- [ ] Redesign GoldenQuestionsList card layout with compact header, conditional quality score, and methodology hover
- [ ] Create QuestionUsageModal component and wire up usage history feature
- [ ] Test end-to-end: generate survey, verify tracking, check UI updates