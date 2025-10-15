# QNR Structure UI Enhancement & Status Fix

## Phase 1: Fix Survey Creation Status (Blocking Issue)

**Problem**: Survey creation fails because code tries to insert 'started' status but database constraint only allows: 'draft', 'validated', 'edited', 'final', 'reference'.

**Solution**: Fix the code to use 'draft' status instead of 'started'

1. Find where survey is created with `status='started'` in `src/api/rfq.py`
2. Change it to `status='draft'`
3. Survey workflow will update status to 'validated' or 'final' after generation completes

## Phase 2: Enhance Survey Structure Page

**Current State**: Survey Structure page shows static section checkboxes and text block requirements.

**Enhancement**: Show dynamic QNR label requirements preview based on user's methodology/industry selections.

### 2.1 Add Requirements Preview Section

Location: `frontend/src/components/EnhancedRFQEditor.tsx` (around line 1705, after section checkboxes)

Add new section that displays:

- **Screener Requirements** (always shown):
- Recent Participation check
- Conflict of Interest screening
- Basic Demographics
- Category usage qualification

- **Brand Study Requirements** (if brand study):
- Unaided brand recall
- Brand awareness funnel
- Product satisfaction
- Usage frequency

- **Concept Testing Requirements** (if concept selected):
- Concept introduction text
- Overall impression
- Purchase likelihood

- **Van Westendorp Requirements** (if VW methodology selected):
- Warning: 4 price questions required
- List: Too cheap, Bargain, Getting expensive, Too expensive

- **Gabor Granger Requirements** (if GG methodology selected):
- Sequential price acceptance questions required

### 2.2 UI Design

Use informational cards with:

- Icon indicators (✅ for always required, ⚠️ for conditional)
- Methodology tags (show when requirement applies)
- Expandable/collapsible sections
- Color coding: green for mandatory, blue for conditional

### 2.3 Dynamic Display Logic

Requirements should appear/disappear based on:

- `enhancedRfq.methodology?.methodology_tags` (for VW, GG, etc.)
- `enhancedRfq.business_context?.industry_category` (for industry-specific)
- `enhancedRfq.research_objectives?.primary_objectives` (for concept/brand detection)

### 2.4 Educational Tooltips

Add info icons with tooltips explaining:

- Why each requirement exists
- What happens if it's missing
- Example question formats

## Phase 3: Add Validation Results Display (Post-Generation)

Location: Survey preview page (wherever final survey is shown)

1. Add structure validation score badge
2. Show critical issues if any
3. Link to detailed validation report

## Files to Modify

1. `src/api/rfq.py` - Change survey creation status from 'started' to 'draft'
2. `frontend/src/components/EnhancedRFQEditor.tsx` - Add requirements preview section
3. `frontend/src/types/index.ts` - Add QNR requirements types if needed

## Success Criteria

1. Survey creation no longer fails with status constraint error
2. Survey Structure page shows relevant requirements based on selections
3. Requirements update dynamically when methodology/industry changes
4. Users understand what will be validated before generating survey

### To-dos

- [ ] Fix survey creation in src/api/rfq.py to use 'draft' status instead of 'started'
- [ ] Add QNR label requirements preview section to Survey Structure page
- [ ] Implement logic to show/hide requirements based on methodology/industry
- [ ] Add educational tooltips explaining each requirement
