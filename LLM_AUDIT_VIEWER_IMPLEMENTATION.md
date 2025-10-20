# LLM Audit Viewer Implementation Summary

## Overview
Replaced the non-functional "View System Prompt" button with a comprehensive "View LLM Audit" feature that displays all AI interactions for a survey.

## Changes Made

### 1. Backend API (`src/api/survey.py`)
**Added:**
- New endpoint: `GET /api/v1/survey/{survey_id}/llm-audits`
- Fetches all LLM audit records for a specific survey
- Returns chronologically ordered list of all AI interactions
- Includes full audit details: prompts, responses, hyperparameters, metrics

**Import added:**
```python
from src.database.models import LLMAudit
```

**Key features:**
- Queries `llm_audit` table by `parent_survey_id`
- Parses raw_response to proper JSON/string format
- Returns comprehensive audit data with all metadata

### 2. Frontend Types (`frontend/src/types/index.ts`)
**Added:**
- `LLMAuditRecord` interface with all audit fields
- Includes: prompts, responses, hyperparameters, tokens, timing, errors

### 3. New Component (`frontend/src/components/LLMAuditViewer.tsx`)
**Created comprehensive modal component with:**

**Features:**
- **Tabbed Interface**: Separate tabs for each interaction type
  - Survey Generation
  - Content Validity
  - Methodological Rigor
  - Respondent Experience
  - Analytical Value
  - Business Impact
  - Other Interactions

- **Audit Card Display**:
  - Success/failure indicators
  - Model info (name, provider, version)
  - Performance metrics (response time, tokens)
  - Hyperparameters (temperature, top_p, max_tokens)
  - Error messages (if failed)

- **Collapsible Sections**:
  - Input Prompt (with copy button)
  - Output Content (with copy button)
  - Raw LLM Response (with copy button)

- **Search Functionality**:
  - Search within prompts and responses
  - Real-time filtering

- **Empty States**:
  - Helpful messages when no audit data exists
  - Guidance for tabs without data

### 4. Updated SurveyPreview (`frontend/src/components/SurveyPreview.tsx`)
**Changes:**
- Added import for `LLMAuditRecord` and `LLMAuditViewer`
- Added state management:
  - `showLLMAuditViewer` - modal visibility
  - `llmAudits` - audit data
  - `loadingAudits` - loading state

- Replaced `handleViewSystemPrompt` with `handleViewLLMAudits`:
  - Fetches audit data from API
  - Opens modal with audit viewer
  - Handles errors gracefully

- Updated button:
  - Changed from "View System Prompt" to "View LLM Audit"
  - Added loading state
  - Changed color to purple for visibility
  - Added disabled state during loading

- Added modal rendering at end of component

## What Users Can Now See

### For Each LLM Interaction:
1. **Metadata**
   - Success/failure status
   - Model name and provider
   - Timestamp
   - Response time
   - Input/output token counts

2. **Hyperparameters**
   - Temperature
   - Top P
   - Max tokens
   - Frequency/presence penalties

3. **Full Prompts**
   - Complete system prompt sent to LLM
   - Copy-to-clipboard functionality
   - Syntax highlighting-ready format

4. **Responses**
   - Parsed output content
   - Raw LLM response
   - Error messages (if failed)

5. **Search & Navigation**
   - Search across all prompts/responses
   - Tab-based organization
   - Collapsible sections for space efficiency

## Technical Details

### API Flow
```
User clicks "View LLM Audit" 
  → Frontend calls /api/v1/survey/{survey_id}/llm-audits
  → Backend queries llm_audit table filtered by parent_survey_id
  → Returns array of audit records ordered by created_at
  → Frontend displays in modal with tabs
```

### Data Structure
```json
{
  "id": "uuid",
  "purpose": "survey_generation" | "evaluation",
  "sub_purpose": "content_validity" | "methodological_rigor" | ...,
  "model_name": "meta/llama-3.3-70b-instruct",
  "input_prompt": "Full system prompt...",
  "output_content": "Generated survey JSON...",
  "raw_response": "Raw LLM output...",
  "response_time_ms": 2500,
  "input_tokens": 5000,
  "output_tokens": 3000,
  "success": true,
  "temperature": 0.2,
  ...
}
```

### LLM Interactions Tracked
1. **Survey Generation** (1 call)
   - Main LLM call to generate survey from RFQ
   - Includes full prompt with rules, examples, RFQ details

2. **5-Pillar Evaluations** (5 calls, if run)
   - Content Validity
   - Methodological Rigor
   - Respondent Experience
   - Analytical Value
   - Business Impact

3. **Field Extraction** (if document upload used)
   - Document parsing and field extraction

4. **RFQ Parsing** (if applicable)
   - Enhanced RFQ text extraction

**Note:** Label detection is NOT included (it's rule-based, not AI)

## Testing Checklist

- [ ] API endpoint returns audit data for existing surveys
- [ ] Modal opens when clicking "View LLM Audit" button
- [ ] Tabs show correct interaction types
- [ ] Each audit card displays all information correctly
- [ ] Collapsible sections work (input, output, raw response)
- [ ] Copy buttons successfully copy text to clipboard
- [ ] Search filters audit records correctly
- [ ] Empty states display when no audit data exists
- [ ] Loading state shows during API fetch
- [ ] Modal closes properly
- [ ] Works for surveys with:
  - Only generation (no evaluations)
  - Generation + all 5 evaluations
  - Failed LLM calls (error display)

## Benefits

1. **Transparency**: Full visibility into AI decision-making process
2. **Debugging**: Easy access to prompts and responses for troubleshooting
3. **Analysis**: Can copy prompts for analysis and improvement
4. **Audit Trail**: Complete history of all AI interactions
5. **Educational**: Learn how the system constructs prompts
6. **Quality Assurance**: Verify AI is receiving correct context

## Files Modified
1. `src/api/survey.py` - Added endpoint (85 lines)
2. `frontend/src/types/index.ts` - Added types (32 lines)
3. `frontend/src/components/LLMAuditViewer.tsx` - New component (478 lines)
4. `frontend/src/components/SurveyPreview.tsx` - Updated button and handler (30 lines changed)

Total: ~625 lines of code

