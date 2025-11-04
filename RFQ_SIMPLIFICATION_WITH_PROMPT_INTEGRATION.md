# RFQ Simplification + Modular Prompt Integration Plan

## Overview
This plan combines RFQ editor simplification with enhancements to our new 5-module prompt system to ensure simplified inputs flow correctly through all modules and improve survey generation quality.

## Part 1: RFQ Editor Simplification (Frontend + Parser)

### Phase 1A: Type Definitions & State Management

**Files**: `frontend/src/types/index.ts`, `frontend/src/store/useAppStore.ts`

**Changes**:
1. **Business Context** - Merge fields:
   - `business_problem` + `business_objective` → `business_problem_and_objective: string`
   - `stakeholder_requirements` → `sample_requirements: string`
   - Remove `decision_criteria` → move to `additional_info`

2. **Research Objectives** - Simplify:
   - Remove `success_metrics`, `validation_requirements`, `measurement_approach` → move to `additional_info`

3. **Methodology** - Focus on essentials:
   - Keep `primary_method`, `stimuli_details`
   - Remove `methodology_requirements`, `complexity_level`, etc. → move to `additional_info`

4. **Survey Requirements** - Streamline:
   - Keep `sample_plan`
   - Remove `must_have_questions`, `accessibility_requirements`, `data_quality_requirements` → move to `additional_info`

5. **Advanced Classification** - Simplify:
   - Remove `compliance_requirements` → move to `additional_info`

6. **NEW: Concept Stimuli Section**:
   ```typescript
   concept_stimuli?: Array<{
     id: string;
     title: string;
     description: string;
     display_order?: number;
   }>
   ```

7. **NEW: Additional Info**:
   ```typescript
   additional_info?: string; // Maps to backend unmapped_context
   ```

### Phase 1B: Frontend UI Updates

**File**: `frontend/src/components/EnhancedRFQEditor.tsx`

**Changes**:

1. **Business Context Section**:
   - Single textarea: "Business Problem & Objective"
   - Rename: "Sample Requirements" (focus on consumer/sample type)
   - Remove: "Decision Criteria" field

2. **Research Objectives Section**:
   - Simplified to core objectives only
   - Remove enhanced fields UI

3. **Methodology Section**:
   - Primary method dropdown with clear uncheck option
   - Stimuli details textarea
   - Remove all enhanced methodology fields

4. **NEW: Concept Stimuli Section** (after Methodology):
   ```typescript
   <div className="space-y-4">
     <h3 className="text-lg font-semibold">Concept Stimuli to Evaluate</h3>
     <p className="text-sm text-gray-600">
       Define the concepts/products respondents will evaluate
     </p>
     
     {conceptStimuli.map((stimulus, index) => (
       <div key={stimulus.id} className="border p-4 rounded">
         <div className="flex justify-between items-start mb-2">
           <span className="font-medium">Concept {index + 1}</span>
           <button onClick={() => removeStimulus(stimulus.id)}>
             Remove
           </button>
         </div>
         <input
           placeholder="Concept Title"
           value={stimulus.title}
           onChange={(e) => updateStimulus(stimulus.id, 'title', e.target.value)}
         />
         <textarea
           placeholder="Concept Description"
           value={stimulus.description}
           onChange={(e) => updateStimulus(stimulus.id, 'description', e.target.value)}
         />
       </div>
     ))}
     
     <button onClick={addNewStimulus}>+ Add Concept</button>
   </div>
   ```

5. **Survey Requirements Section**:
   - Keep Sample Plan field
   - Remove must-have questions fields

6. **Additional Info Section** (collapsible, at bottom):
   ```typescript
   <Collapsible title="Additional Information (Optional)">
     <textarea
       placeholder="Any additional context from original RFQ..."
       value={additionalInfo}
       onChange={(e) => setAdditionalInfo(e.target.value)}
     />
   </Collapsible>
   ```

### Phase 1C: Document Parser Updates

**File**: `src/services/document_parser.py`

**Update `create_rfq_extraction_prompt`**:

```python
def create_rfq_extraction_prompt(self, document_text: str) -> str:
    return f"""Extract structured information from this RFQ document.

DOCUMENT TEXT:
{document_text}

EXTRACT INTO THIS SIMPLIFIED SCHEMA:

1. **business_problem_and_objective** (string): Combined business problem and research objective
2. **sample_requirements** (string): Consumer/sample type requirements (demographics, quotas)
3. **primary_method** (string): Primary research methodology (if mentioned)
4. **stimuli_details** (string): Details about products/concepts to test
5. **concept_stimuli** (array): Extract each concept/product to evaluate:
   [
     {{
       "id": "concept_1",
       "title": "Concept Name",
       "description": "Full description of concept/product"
     }}
   ]
   - Look for multiple products, concepts, formulations, or variants
   - Each should be a separate entry
   - Include all descriptive details

6. **sample_plan** (string): Quota tables, sample sizes, screening criteria
7. **text_requirements** (object): Mandatory text blocks (Study_Intro, Survey_Closing, etc.)
8. **unmapped_context** (string): ALL other context that doesn't fit above categories
   - Include success metrics, validation requirements, methodology details
   - Include compliance, accessibility, data quality requirements
   - Include any other relevant information

Return ONLY valid JSON with these fields.
"""
```

### Phase 1D: Enhanced RFQ Converter

**File**: `frontend/src/utils/enhancedRfqConverter.ts`

**Update `buildEnhancedRFQText`**:

```typescript
export function buildEnhancedRFQText(enhancedRfq: EnhancedRFQ): string {
  const sections: string[] = [];

  // Business Context
  if (enhancedRfq.business_problem_and_objective) {
    sections.push(`## Business Problem & Objective\n${enhancedRfq.business_problem_and_objective}`);
  }

  if (enhancedRfq.sample_requirements) {
    sections.push(`## Sample Requirements\n${enhancedRfq.sample_requirements}`);
  }

  // Research Objectives
  if (enhancedRfq.primary_objective) {
    sections.push(`## Research Objective\n${enhancedRfq.primary_objective}`);
  }

  // Methodology
  if (enhancedRfq.primary_method) {
    sections.push(`## Primary Methodology\n${enhancedRfq.primary_method}`);
  }

  // Concept Stimuli
  if (enhancedRfq.concept_stimuli && enhancedRfq.concept_stimuli.length > 0) {
    const stimuliText = enhancedRfq.concept_stimuli
      .map((s, i) => `### Concept ${i + 1}: ${s.title}\n${s.description}`)
      .join('\n\n');
    sections.push(`## Concept Stimuli\n${stimuliText}`);
  }

  if (enhancedRfq.stimuli_details) {
    sections.push(`## Stimuli Details\n${enhancedRfq.stimuli_details}`);
  }

  // Survey Requirements
  if (enhancedRfq.sample_plan) {
    sections.push(`## Sample Plan\n${enhancedRfq.sample_plan}`);
  }

  // Text Requirements
  if (enhancedRfq.text_requirements) {
    sections.push(`## Text Requirements\n${JSON.stringify(enhancedRfq.text_requirements, null, 2)}`);
  }

  // Additional Info (unmapped context)
  if (enhancedRfq.additional_info) {
    sections.push(`## Additional Information\n${enhancedRfq.additional_info}`);
  }

  return sections.join('\n\n');
}
```

---

## Part 2: Modular Prompt Enhancements

### Phase 2A: InputsModule Enhancement

**File**: `src/services/prompt_builder.py` - Update `InputsModule.build()`

**Add Concept Stimuli Display**:

```python
# In InputsModule.build() method, after research_context

# Add Concept Stimuli section
concept_stimuli = context.get("concept_stimuli", [])
if concept_stimuli:
    stimuli_parts = [
        "",
        "# CONCEPT STIMULI TO EVALUATE",
        "",
        f"The survey will evaluate {len(concept_stimuli)} concept(s)/product(s):",
        ""
    ]
    
    for i, stimulus in enumerate(concept_stimuli, 1):
        stimuli_parts.extend([
            f"## Concept {i}: {stimulus.get('title', 'Untitled')}",
            f"{stimulus.get('description', 'No description provided')}",
            ""
        ])
    
    stimuli_parts.extend([
        "**IMPORTANT**: Generate evaluation questions for EACH concept listed above.",
        "Typically 8-15 questions per concept for comprehensive evaluation.",
        ""
    ])
    
    sections.append(PromptSection("concept_stimuli", stimuli_parts, order=2.4))

# Add Unmapped Context section
unmapped_context = context.get("unmapped_context", "")
if unmapped_context:
    unmapped_parts = [
        "",
        "# ADDITIONAL CONTEXT FROM RFQ",
        "",
        unmapped_context,
        ""
    ]
    sections.append(PromptSection("unmapped_context", unmapped_parts, order=2.5))
```

### Phase 2B: InstructionModule Enhancement

**File**: `src/services/prompt_builder.py` - Update `InstructionModule.build()`

**Add to Section 3.2 (Methodology-Specific Depth)**:

```python
# After existing methodology checks, add concept evaluation guidance

# Check for concept stimuli
concept_stimuli = context.get("concept_stimuli", [])
if concept_stimuli:
    methodology_depth.extend([
        "",
        "## CONCEPT/PRODUCT EVALUATION:",
        f"**Number of Concepts**: {len(concept_stimuli)}",
        "**Question Density**: 8-15 evaluation questions per concept",
        "",
        "**Required Question Types per Concept**:",
        "1. Overall impression (1-2 questions)",
        "2. Attribute ratings (3-5 questions) - e.g., appeal, uniqueness, relevance",
        "3. Purchase intent (1 question) - 5-point scale typical",
        "4. Open-ended feedback (1-2 questions) - likes/dislikes",
        "5. Preference ranking (if multiple concepts)",
        "",
        "**Design Approach**:",
        "- Sequential Monadic: Show concepts one at a time, evaluate each fully",
        "- Rotation: Randomize concept order (specify in Section 7 programmer instructions)",
        "- Comparative: After all concepts, ask preference/ranking questions",
        "",
        "**CRITICAL**: Each concept gets its own sub-section in Section 4 (Concept Exposure)",
        ""
    ])
```

**Add to Section 3.5 (Static Text Requirements)**:

```python
# After existing Section 4 text block example, add:

concept_stimuli = context.get("concept_stimuli", [])
if concept_stimuli and len(concept_stimuli) > 0:
    static_text.extend([
        "",
        "### IMPORTANT: Multiple Concept Handling",
        "When RFQ includes multiple concepts:",
        "```json",
        '"introText": {',
        '  "id": "intro_4",',
        '  "type": "concept_intro",',
        '  "label": "Concept_Intro",',
        '  "content": "You will now evaluate different product concepts. Please review each concept carefully before answering. Concept order is randomized.",',
        '  "mandatory": true',
        "}",
        "```",
        "",
        "For each concept, create a sub-section or use textBlocks:",
        "```json",
        '"textBlocks": [',
        '  {',
        '    "id": "concept_1_intro",',
        '    "type": "concept_description",',
        '    "label": "Concept_1_Description",',
        f'    "content": "{concept_stimuli[0].get("title")} - {concept_stimuli[0].get("description")[:100]}...",',
        '    "mandatory": true',
        '  }',
        ']',
        "```",
        ""
    ])
```

### Phase 2C: OutputModule Enhancement

**File**: `src/services/prompt_builder.py` - Update `OutputModule.build()`

**Add to Section 5.3 (Validation Checklist)**:

```python
# After existing validation items, add:

# Check if concept stimuli exist
concept_stimuli = context.get("concept_stimuli", [])
if concept_stimuli:
    validation_content.extend([
        "",
        "## Concept/Product Coverage Validation:",
        f"- [ ] Generated evaluation questions for ALL {len(concept_stimuli)} concepts",
        "- [ ] Each concept has 8-15 evaluation questions",
        "- [ ] Concept questions in Section 4 (Concept Exposure)",
        "- [ ] Included concept descriptions in textBlocks or introText",
        "- [ ] Rotation/randomization instructions in Section 7 (if multiple concepts)",
        "- [ ] Preference/ranking questions after all concept evaluations",
        ""
    ])
```

### Phase 2D: Sample Plan Clarification

**File**: `src/services/prompt_builder.py` - Update `InputsModule.build()`

**Enhance QNR Structure section**:

```python
# Update Section 1 description in QNR Structure

"## Section 1: Sample Plan",
"Purpose: Sample quotas, demographic targets, and screening criteria",
"**Note**: This section typically has 2-5 brief screening questions only",
"**Note**: Detailed survey questions belong in later sections, NOT in Sample Plan",
"Text blocks: Study_Intro (introText - MANDATORY)",
""
```

---

## Part 3: Workflow Integration

### Phase 3A: Context Building

**File**: `src/workflows/nodes.py` (or wherever context is built)

**Ensure Enhanced RFQ fields map correctly**:

```python
# In the node that builds context for prompt generation

def build_generation_context(enhanced_rfq: Dict[str, Any]) -> Dict[str, Any]:
    context = {
        "rfq_details": {
            "text": build_rfq_text(enhanced_rfq),  # Uses enhancedRfqConverter
            "methodology_tags": extract_methodology_tags(enhanced_rfq.get("primary_method")),
            # ... other fields
        }
    }
    
    # Add concept stimuli if present
    if "concept_stimuli" in enhanced_rfq and enhanced_rfq["concept_stimuli"]:
        context["concept_stimuli"] = enhanced_rfq["concept_stimuli"]
    
    # Add unmapped context if present
    if "additional_info" in enhanced_rfq and enhanced_rfq["additional_info"]:
        context["unmapped_context"] = enhanced_rfq["additional_info"]
    
    return context
```

---

## Implementation Order

### Sprint 1: RFQ Simplification (Frontend Heavy)
1. ✅ Update type definitions (`types/index.ts`)
2. ✅ Update initial state (`useAppStore.ts`)
3. ✅ Update RFQ editor UI (`EnhancedRFQEditor.tsx`)
   - Remove unnecessary fields
   - Add Concept Stimuli section
   - Add Additional Info section
4. ✅ Update RFQ converter (`enhancedRfqConverter.ts`)
5. ✅ Test UI changes manually

### Sprint 2: Parser Integration
6. ✅ Update document parser prompt (`document_parser.py`)
   - Simplified field extraction
   - Concept stimuli extraction
   - Unmapped context handling
7. ✅ Test document parsing with sample RFQs
8. ✅ Verify parsed data flows to editor correctly

### Sprint 3: Prompt Module Enhancements (Backend)
9. ✅ Update `InputsModule` to show concept stimuli
10. ✅ Update `InputsModule` to show unmapped context
11. ✅ Update `InstructionModule` section 3.2 (concept evaluation guidance)
12. ✅ Update `InstructionModule` section 3.5 (concept text blocks)
13. ✅ Update `OutputModule` section 5.3 (concept validation checklist)
14. ✅ Update context building in workflow

### Sprint 4: Testing & Validation
15. ✅ End-to-end test: Upload document → Parse → Edit → Generate survey
16. ✅ Validate concept stimuli appear in prompts
17. ✅ Validate generated surveys include all concepts
18. ✅ Test with reference vodka RFQ (multi-sample concept)
19. ✅ Compare output quality: Before vs After

---

## Testing Checklist

### Frontend Tests
- [ ] RFQ editor shows simplified fields
- [ ] Can add/edit/remove concept stimuli
- [ ] Additional info section stores extra context
- [ ] Removed fields don't cause errors
- [ ] State persists correctly during editing

### Parser Tests
- [ ] Document with single concept → extracts correctly
- [ ] Document with multiple concepts → extracts all
- [ ] Old-style RFQ → moves removed fields to unmapped_context
- [ ] New-style RFQ → parses into simplified schema

### Prompt Tests
- [ ] Concept stimuli appear in Module 2 (Inputs)
- [ ] Unmapped context appears in Module 2
- [ ] Module 3.2 includes concept evaluation guidance
- [ ] Module 3.5 includes concept text block examples
- [ ] Module 5.3 includes concept validation checklist

### Survey Generation Tests
With vodka taste test RFQ (3 samples = 3 concepts):
- [ ] Generated survey has 70-90 questions (vs 59 before)
- [ ] Each sample has 20-30 rating questions
- [ ] Concept descriptions appear in Section 4 textBlocks
- [ ] Follow-up questions after ratings (10-15% ratio)
- [ ] All 3 samples evaluated (not just 1)
- [ ] 6/7 sections have introText (vs 2/7 before)
- [ ] Section 7 has closingText

---

## Migration Strategy

### For Existing RFQs
When loading old RFQs with removed fields:

```typescript
function migrateOldRFQ(oldRfq: any): EnhancedRFQ {
  const additionalInfo: string[] = [];
  
  // Collect removed fields
  if (oldRfq.decision_criteria) {
    additionalInfo.push(`Decision Criteria: ${oldRfq.decision_criteria}`);
  }
  if (oldRfq.success_metrics) {
    additionalInfo.push(`Success Metrics: ${oldRfq.success_metrics}`);
  }
  // ... collect all removed fields
  
  return {
    // Merge business fields
    business_problem_and_objective: 
      `${oldRfq.business_problem || ''}\n\n${oldRfq.business_objective || ''}`.trim(),
    
    // Rename field
    sample_requirements: oldRfq.stakeholder_requirements || '',
    
    // Keep existing fields
    primary_method: oldRfq.primary_method,
    stimuli_details: oldRfq.stimuli_details,
    
    // New fields
    concept_stimuli: [],
    additional_info: additionalInfo.join('\n\n'),
    
    // ... other fields
  };
}
```

---

## Success Metrics

### Immediate (Post-Implementation)
1. ✅ RFQ editor has 50% fewer fields
2. ✅ Document parser extracts concept stimuli array
3. ✅ Prompts include concept-specific guidance
4. ✅ No regression in existing survey quality

### Short-term (2 weeks)
1. ✅ Generated surveys include all concepts from RFQ
2. ✅ Multi-concept surveys have appropriate question distribution
3. ✅ Text blocks reference specific concepts
4. ✅ Validation checklist catches missing concepts

### Long-term (1 month)
1. ✅ 30% improvement in concept coverage (all concepts evaluated)
2. ✅ 20% increase in questions per concept (8-15 vs 3-5 currently)
3. ✅ User satisfaction with simplified RFQ editor
4. ✅ Reduced parsing errors from cleaner schema

---

## Files Modified Summary

### Frontend (7 files)
1. `frontend/src/types/index.ts` - Type definitions
2. `frontend/src/store/useAppStore.ts` - Initial state
3. `frontend/src/components/EnhancedRFQEditor.tsx` - UI changes
4. `frontend/src/utils/enhancedRfqConverter.ts` - Text conversion
5. `frontend/src/components/ConceptStimuliEditor.tsx` - NEW component
6. `frontend/src/styles/...` - Styling if needed

### Backend (3 files)
1. `src/services/document_parser.py` - Parsing prompt
2. `src/services/prompt_builder.py` - All 3 module enhancements
3. `src/workflows/nodes.py` - Context building (minor)

### Optional
1. `src/api/rfq.py` - Validation updates (if schema changes significantly)

---

## Risk Mitigation

### Risk: Existing RFQs break
**Mitigation**: Migration function to move old fields to additional_info

### Risk: Parser misses concept stimuli
**Mitigation**: Strong prompt examples, fallback to stimuli_details field

### Risk: Prompts too long with concept details
**Mitigation**: Truncate long concept descriptions (200 chars per concept)

### Risk: Generated surveys still miss concepts
**Mitigation**: Validation checklist in Module 5, post-generation validation

---

## Rollback Plan

If issues arise:
1. Keep old type definitions in `types/index.legacy.ts`
2. Feature flag for new vs old RFQ editor
3. Parser can output both old and new schemas
4. Prompts work with both structures (backward compatible)

---

## Next Steps After Implementation

1. **Enhanced Sample Plan UI**: Make sample_plan field support tabular input (Phase 2)
2. **Text Blocks Editor**: Add visual editor for text_requirements (Phase 2)
3. **Concept Rotation**: Add UI for concept rotation settings (Phase 3)
4. **Template Library**: Pre-defined concept stimuli templates (Phase 3)

