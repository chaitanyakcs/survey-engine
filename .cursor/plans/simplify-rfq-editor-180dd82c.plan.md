<!-- 180dd82c-1127-44e0-83b9-486ff46237b3 b707c890-6cad-40f0-a6de-d3b0a9596b49 -->
# RFQ Editor Simplification and Parsing Update

## Overview

Simplify the RFQ editor interface by merging/removing unnecessary fields, updating document parsing logic, and adding a new Concept Stimuli validation section. Removed fields will be moved to `additional_info` (stored as `unmapped_context` in the backend).

## Changes Required

### 1. Type Definitions (`frontend/src/types/index.ts`)

**Business Context Changes:**

- Merge `business_problem` and `business_objective` into single field `business_problem_and_objective: string`
- Rename `stakeholder_requirements` to `sample_requirements: string` (repurpose to describe type of consumer/sample needs)
- Remove `decision_criteria` field (move to `additional_info`)

**Research Objectives Changes:**

- Remove `success_metrics`, `validation_requirements`, `measurement_approach` (move to `additional_info`)

**Methodology Changes:**

- Keep only `primary_method` and `stimuli_details`
- Remove `methodology_requirements`, `complexity_level`, `required_methodologies`, `sample_size_target` (move to `additional_info`)
- Add checkbox/deselect capability for methodologies

**Survey Requirements Changes:**

- Keep `sample_plan` (enhance UI for tabular structure)
- Remove `must_have_questions` (move to `additional_info`)
- Remove `accessibility_requirements` and `data_quality_requirements` (move to `additional_info`)

**Survey Structure Changes:**

- Keep `text_requirements` (Text Blocks) with add/edit capability
- Note: Sample plan section should be table/quota only, no questions

**Advanced Classification Changes:**

- Remove `compliance_requirements` (move to `additional_info`)

**New Section:**

- Add `concept_stimuli?: Array<{id: string, title: string, description: string}>` to validate Concept Stimuli (1 or more)

**Additional Info:**

- Add `additional_info?: string` field to store removed fields' context (maps to backend `unmapped_context`)

### 2. Frontend State (`frontend/src/store/useAppStore.ts`)

Update `enhancedRfq` initial state to:

- Reflect merged/removed fields
- Initialize `concept_stimuli` as empty array
- Initialize `additional_info` as empty string

### 3. RFQ Editor Component (`frontend/src/components/EnhancedRFQEditor.tsx`)

**Business Context Section:**

- Replace two fields with single merged field "Business Problem & Objective"
- Rename "Stakeholder Requirements" to "Sample Requirements" with updated placeholder/text
- Remove "Decision Criteria" field UI

**Research Objectives Section:**

- Remove "Success Metrics", "Validation Requirements", "Measurement Approach" fields

**Methodology Section:**

- Simplify to show only Primary Methodology (with clear uncheck option) and Stimuli Details
- Remove all enhanced methodology fields UI
- Make methodology selection more explicit with uncheck capability

**Survey Requirements Section:**

- Keep Sample Plan field (prepare for enhanced tabular UI later)
- Remove "Must-Have Questions" field
- Remove "Accessibility Requirements" and "Data Quality Requirements" fields

**Survey Structure Section:**

- Enhance Text Blocks section with add/edit functionality
- Ensure sample plan section UI reflects table/quota structure

**Advanced Classification Section:**

- Remove "Compliance Requirements" field

**New Concept Stimuli Section:**

- Add new section after Methodology or in Survey Structure
- Show list of stimuli with edit/delete options
- If stimuli already exist (from parsing), display them with edit capability
- Add button to add new stimuli

**Additional Info Section:**

- Add collapsible "Additional Information" section at bottom
- Store removed fields' context here (when editing existing RFQs that had those fields)

### 4. Document Parser Prompt (`src/services/document_parser.py`)

Update `create_rfq_extraction_prompt` method:

- Remove field examples for: `decision_criteria`, `success_metrics`, `validation_requirements`, `measurement_approach`, `methodology_requirements`, `complexity_level`, `required_methodologies`, `sample_size_target`, `must_have_questions`, `accessibility_requirements`, `data_quality_requirements`, `compliance_requirements`
- Update field example for merged `business_problem_and_objective`
- Update field example for renamed `sample_requirements` (clarify it's about consumer/sample type needs)
- Add field example for `concept_stimuli` array extraction
- Update instructions to extract removed fields and place them in `unmapped_context` section

### 5. Enhanced RFQ Converter (`frontend/src/utils/enhancedRfqConverter.ts`)

Update `buildEnhancedRFQText` function:

- Handle merged `business_problem_and_objective` field
- Handle renamed `sample_requirements` field
- Remove references to deleted fields
- Add handling for `concept_stimuli` array
- Include `additional_info` in text output if present

### 6. Backend API (`src/api/rfq.py`)

Ensure validation accepts:

- New simplified structure
- `concept_stimuli` array (optional)
- `additional_info` field (maps to `unmapped_context`)

### 7. Workflow State (`src/workflows/state.py`)

No changes needed - `unmapped_context` already exists and will be populated from `additional_info`.

## Implementation Order

1. Update type definitions with new structure
2. Update document parser prompt to extract simplified fields and move removed fields to unmapped_context
3. Update RFQ editor component UI with simplified sections
4. Add Concept Stimuli section to editor
5. Update state management and converters
6. Test document parsing with simplified schema
7. Test editor with new structure

## Migration Considerations

- Existing RFQs with old structure: preserve old fields in `additional_info`/`unmapped_context` during parsing
- Document parser should extract old fields and move them to `unmapped_context` when found
- Editor should show `additional_info` section if data exists from old structure

## Key Files to Modify

- `frontend/src/types/index.ts` - Type definitions
- `frontend/src/store/useAppStore.ts` - Initial state
- `frontend/src/components/EnhancedRFQEditor.tsx` - UI changes
- `frontend/src/utils/enhancedRfqConverter.ts` - Text conversion
- `src/services/document_parser.py` - Parsing prompt and logic
- `src/api/rfq.py` - Validation (if needed)