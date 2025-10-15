# QNR Labeling Survey Structure Enhancement Plan

## Overview
Improve survey structural integrity by implementing QNR Labeling framework for validation, section requirements, and question placement—keeping prompts lean while adding robust post-generation checks.

## Problem Statement
Current system:
- Defines 7 sections but doesn't enforce what questions belong where
- No validation of screener requirements (CoI, participation checks)
- No methodology-conditional validation (VW needs 4 price questions)
- No question sequencing enforcement
- Labels exist in DB but aren't used for structural validation

## Solution Architecture

### 1. Enhanced Prompt Structure (Minimal Additions)
**File: `src/services/prompt_builder.py`**

Add concise structural requirements to existing section descriptions:

**Section 2 - Screener (Enhanced):**
```
2. **Screener** (id: 2): Initial qualification questions and basic demographics
   REQUIRED QUESTIONS:
   - Recent participation check (market research in last 6 months)
   - Conflict of interest screening (industry employment, competitors)
   - Basic demographics (age, gender)
   - Category usage qualification
   SEQUENCING: General → Specific, terminate early if disqualified
```

**Section 3 - Brand/Product Awareness (Enhanced):**
```
3. **Brand/Product Awareness & Usage** (id: 3): Brand recall, awareness funnel, and usage patterns
   REQUIRED QUESTIONS (if brand study):
   - Unaided brand recall
   - Brand awareness funnel (Aware → Considered → Purchased → Continue → Preferred)
   - Brand/product satisfaction ratings
   - Usage frequency and patterns
```

**Section 5 - Methodology (Enhanced):**
```
5. **Methodology** (id: 5): Research-specific questions
   Van Westendorp REQUIRED:
   - "Too cheap" price point
   - "Bargain" price point
   - "Getting expensive" price point  
   - "Too expensive" price point
   
   Gabor Granger REQUIRED:
   - Sequential price acceptance (starting at optimal price, adjusting based on response)
```

**Estimated addition: ~800 characters (~200 tokens)**

### 2. QNR Label Taxonomy Service (NEW)
**File: `src/services/qnr_label_taxonomy.py`**

Define the complete QNR label taxonomy from CSV data:

```python
class QNRLabelTaxonomy:
    """QNR Label definitions and requirements"""
    
    def __init__(self):
        self.screener_labels = self._load_screener_labels()
        self.brand_labels = self._load_brand_labels()
        self.concept_labels = self._load_concept_labels()
        self.methodology_labels = self._load_methodology_labels()
        self.additional_labels = self._load_additional_labels()
        self.qnr_tags = self._load_qnr_tags()
        
    def get_required_labels(self, section_id: int, methodology: str = None, 
                          industry: str = None) -> List[Dict]:
        """Get required labels for a section based on context"""
        
    def get_conditional_labels(self, methodology: str, industry: str, 
                              respondent_type: str) -> List[Dict]:
        """Get labels required based on methodology/industry/respondent"""
```

Load from QNR_Labeling CSVs at initialization.

### 3. Survey Structure Validator (NEW)
**File: `src/services/survey_structure_validator.py`**

Post-generation validation using QNR taxonomy:

```python
class SurveyStructureValidator:
    """Validates generated surveys against QNR structural requirements"""
    
    def __init__(self, db_session):
        self.taxonomy = QNRLabelTaxonomy()
        self.label_detector = QuestionLabelDetector()
        
    async def validate_structure(self, survey_json: Dict, 
                                 rfq_context: Dict) -> StructureValidationReport:
        """
        Comprehensive structural validation:
        1. Section-specific requirements
        2. Mandatory questions present
        3. Question placement (screeners early, demographics late)
        4. Methodology-specific requirements
        5. Sequencing rules
        """
        
        report = StructureValidationReport()
        
        # Extract context
        methodology = rfq_context.get('methodology_tags', [])
        industry = rfq_context.get('industry')
        
        # Validate each section
        for section in survey_json.get('sections', []):
            section_validation = self._validate_section(
                section, methodology, industry
            )
            report.add_section_validation(section_validation)
            
        # Validate cross-section requirements
        report.add_sequencing_validation(
            self._validate_sequencing(survey_json)
        )
        
        # Validate methodology requirements
        if 'van_westendorp' in methodology:
            report.add_methodology_validation(
                self._validate_van_westendorp(survey_json)
            )
        
        return report
        
    def _validate_section(self, section, methodology, industry):
        """Validate section has required questions"""
        section_id = section.get('id')
        required_labels = self.taxonomy.get_required_labels(
            section_id, methodology, industry
        )
        
        # Detect labels in section questions
        detected_labels = self.label_detector.detect_labels_in_section(section)
        
        # Find missing required labels
        missing = [
            label for label in required_labels 
            if label['label'] not in detected_labels and label['mandatory']
        ]
        
        return SectionValidation(
            section_id=section_id,
            required_labels=required_labels,
            detected_labels=detected_labels,
            missing_labels=missing,
            is_valid=len(missing) == 0
        )
```

### 4. Question Label Detector (NEW)
**File: `src/services/question_label_detector.py`**

Auto-detect QNR labels in generated questions using NLP/rules:

```python
class QuestionLabelDetector:
    """Detects QNR labels in survey questions"""
    
    def __init__(self):
        self.label_patterns = self._load_label_patterns()
        
    def detect_labels_in_question(self, question: Dict) -> List[str]:
        """Detect applicable labels for a question"""
        labels = []
        q_text = question.get('text', '').lower()
        q_type = question.get('type', '')
        
        # Recent participation
        if any(kw in q_text for kw in ['participated', 'market research', 'recent study']):
            labels.append('Recent_Participation')
            
        # CoI Check
        if any(kw in q_text for kw in ['work for', 'employed by', 'conflict of interest']):
            labels.append('CoI_Check')
            
        # Brand awareness funnel
        if any(kw in q_text for kw in ['aware of', 'considered', 'purchased', 'prefer']):
            if self._is_brand_funnel_pattern(question):
                labels.append('Brand_awareness_funnel')
                
        # Van Westendorp pricing
        if 'numeric_open' == q_type and any(kw in q_text for kw in ['price', 'expensive', 'cheap']):
            if 'too expensive' in q_text:
                labels.append('VW_Too_Expensive')
            elif 'too cheap' in q_text:
                labels.append('VW_Too_Cheap')
            elif 'getting expensive' in q_text:
                labels.append('VW_Getting_Expensive')
            elif 'bargain' in q_text or 'good value' in q_text:
                labels.append('VW_Bargain')
                
        # Demographic questions
        if any(kw in q_text for kw in ['age', 'gender', 'male', 'female']):
            labels.append('Demog_Basic')
            
        return labels
```

### 5. Integration into Workflow
**File: `src/workflows/nodes.py` - Enhance ValidationAgent**

Add structural validation after generation:

```python
class ValidationAgent:
    def __init__(self, db: Session):
        self.db = db
        self.structure_validator = SurveyStructureValidator(db)
        # ... existing validators
        
    async def __call__(self, state: SurveyGenerationState):
        # ... existing validation
        
        # NEW: Structural validation
        structure_report = await self.structure_validator.validate_structure(
            survey_json=state.generated_survey,
            rfq_context={
                'methodology_tags': state.methodology_tags,
                'industry': state.industry_category,
                'respondent_type': state.respondent_type
            }
        )
        
        validation_results['structure_validation'] = structure_report.to_dict()
        
        # If critical structural issues, flag for review
        if structure_report.has_critical_issues():
            validation_results['needs_review'] = True
            validation_results['review_reason'] = structure_report.get_critical_issues_summary()
```

### 6. Database Schema Updates
**File: `migrations/020_add_qnr_label_taxonomy.sql`**

Store QNR label taxonomy in database:

```sql
-- QNR Label Definitions table
CREATE TABLE IF NOT EXISTS qnr_label_definitions (
    id SERIAL PRIMARY KEY,
    label_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL, -- screener, brand, concept, methodology, additional
    description TEXT,
    mandatory BOOLEAN DEFAULT FALSE,
    applicable_labels JSONB, -- Conditional requirements
    label_type VARCHAR(50), -- Text, QNR, Rules
    detection_patterns JSONB, -- Keywords and patterns for auto-detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_qnr_labels_category ON qnr_label_definitions(category);
CREATE INDEX idx_qnr_labels_mandatory ON qnr_label_definitions(mandatory);

-- QNR Tag Definitions (metadata)
CREATE TABLE IF NOT EXISTS qnr_tag_definitions (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL,
    tag_values TEXT[], -- Allowed values
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed from CSV data
INSERT INTO qnr_label_definitions (label_name, category, description, mandatory, applicable_labels, label_type)
VALUES 
    ('Study_Intro', 'screener', 'Thanks for agreeing, inform eligibility, state LOI', TRUE, NULL, 'Text'),
    ('Recent_Participation', 'screener', 'Participated in Market Research study recently. Terminate', TRUE, NULL, 'QNR'),
    ('CoI_Check', 'screener', 'Conflict of Interest check. Terminate', TRUE, NULL, 'QNR'),
    ('Demog_Basic', 'screener', 'Age, Gender. Check categories specific to country', TRUE, NULL, 'QNR'),
    -- ... all other labels from CSV
;
```

### 7. Annotation UI Enhancement
**File: `frontend/src/components/QuestionAnnotationPanel.tsx`**

Show detected labels + allow manual label assignment:

```typescript
// Add label selector
<div className="label-section">
  <h4>QNR Labels</h4>
  <div className="detected-labels">
    {detectedLabels.map(label => (
      <Badge key={label} color="green">{label}</Badge>
    ))}
  </div>
  <Select
    multiple
    value={selectedLabels}
    onChange={(e) => setSelectedLabels(e.target.value)}
    options={availableLabels}
  />
</div>
```

### 8. Validation Report UI
**File: `frontend/src/components/StructureValidationReport.tsx`**

Display structure validation results:

```typescript
interface StructureValidationReportProps {
  report: StructureValidationReport;
}

export const StructureValidationReport: React.FC<StructureValidationReportProps> = ({ report }) => {
  return (
    <div className="structure-report">
      <h3>Survey Structure Validation</h3>
      
      {report.sections.map(section => (
        <SectionValidationCard
          key={section.section_id}
          section={section}
          showMissing={true}
        />
      ))}
      
      {report.methodology_validation && (
        <MethodologyValidationCard validation={report.methodology_validation} />
      )}
      
      <OverallScore score={report.structure_score} />
    </div>
  );
};
```

## Implementation Phases

### Phase 1: Foundation (High Priority)
1. Create `QNRLabelTaxonomy` service - load CSV data
2. Create `QuestionLabelDetector` with basic pattern matching
3. Add enhanced section descriptions to prompt (+800 chars)
4. Database migration for label taxonomy
5. **Estimated effort:** 2-3 days

### Phase 2: Validation (High Priority)
1. Create `SurveyStructureValidator`
2. Integrate into ValidationAgent workflow
3. Add structure validation to survey generation flow
4. API endpoint for structure validation
5. **Estimated effort:** 2-3 days

### Phase 3: UI Integration (Medium Priority)
1. Structure validation report component
2. Label detection display in annotation UI
3. Manual label assignment interface
4. Validation insights in survey preview
5. **Estimated effort:** 2 days

### Phase 4: Enhancement (Low Priority)
1. ML-based label detection (vs rule-based)
2. Automated survey fixing suggestions
3. Label-based RAG retrieval
4. Analytics dashboard for label compliance
5. **Estimated effort:** 3-4 days

## Key Benefits

1. **Better Surveys**: Ensure screeners have termination logic, methodologies have required questions
2. **Lean Prompts**: Only +800 chars to prompt, rest is post-generation validation
3. **Actionable Feedback**: "Missing CoI check in screener" vs generic "quality issue"
4. **Methodology Compliance**: Enforce VW 4-price rule, GG sequential logic
5. **Training Data**: Auto-labeled questions improve golden examples
6. **Evaluation Integration**: Structure score feeds into 5-pillar framework

## Example: Van Westendorp Validation

**Current state:** Prompt mentions VW, but doesn't enforce structure
**After enhancement:**

```python
# In SurveyStructureValidator
def _validate_van_westendorp(self, survey):
    required_vw_questions = [
        'VW_Too_Cheap',
        'VW_Bargain', 
        'VW_Getting_Expensive',
        'VW_Too_Expensive'
    ]
    
    detected = self.label_detector.detect_all_labels(survey)
    missing = [q for q in required_vw_questions if q not in detected]
    
    if missing:
        return ValidationIssue(
            severity='critical',
            message=f'Van Westendorp methodology requires 4 price questions. Missing: {missing}',
            suggestion='Add missing price sensitivity questions in Methodology section'
        )
```

## Files to Create/Modify

**New Files:**
- `src/services/qnr_label_taxonomy.py`
- `src/services/survey_structure_validator.py`
- `src/services/question_label_detector.py`
- `migrations/020_add_qnr_label_taxonomy.sql`
- `frontend/src/components/StructureValidationReport.tsx`
- `tests/test_structure_validation.py`

**Modified Files:**
- `src/services/prompt_builder.py` - Enhanced section descriptions
- `src/workflows/nodes.py` - Add structure validation to ValidationAgent
- `frontend/src/components/QuestionAnnotationPanel.tsx` - Label UI
- `src/api/survey.py` - Structure validation endpoint

## Success Metrics

- Van Westendorp surveys have all 4 price questions: 100%
- Screener sections have CoI + Recent Participation: 90%+
- Brand studies have awareness funnel: 85%+
- Structure validation score: >0.85 average
- Prompt size increase: <5% (+800 chars)

## To-dos

- [ ] Create QNRLabelTaxonomy service to load and manage QNR label definitions from CSV files
- [ ] Build QuestionLabelDetector with pattern matching for auto-detecting labels in questions
- [ ] Implement SurveyStructureValidator for post-generation structural validation
- [ ] Add concise section-specific requirements to prompt builder (~800 chars)
- [ ] Create migration for qnr_label_definitions and qnr_tag_definitions tables
- [ ] Integrate structure validation into ValidationAgent in workflow
- [ ] Build StructureValidationReport component for frontend display
- [ ] Add label detection and manual assignment UI to annotation panels
- [ ] Create API endpoint for on-demand structure validation
- [ ] Write comprehensive tests for structure validation logic


