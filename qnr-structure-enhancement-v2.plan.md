# QNR Labeling Survey Structure Enhancement Plan v2

## Overview
Implement deterministic, rule-based QNR labeling and validation system that flags survey quality issues WITHOUT blocking generation. Simple, accurate, and non-intrusive quality scoring.

## Core Principles
1. **Deterministic**: Rule-based pattern matching, no LLM calls
2. **Non-blocking**: Validation NEVER stops generation, only flags issues
3. **Simple**: Clear, maintainable rules
4. **Accurate**: High precision label detection
5. **Actionable**: Clear feedback on what's good/bad

## Standardized Label Names (Option B)

### Screener Section
```
Study_Intro                      - Study introduction text (mandatory)
Recent_Participation             - Market research participation check (mandatory)
Conflict_Of_Interest_Check       - CoI screening (mandatory)
Demographics_Basic               - Age, gender (mandatory)
Medical_Conditions_General       - General health conditions (conditional: healthcare)
Medical_Conditions_Study         - Study-specific conditions (conditional: healthcare)
Category_Usage_Frequency         - Usage frequency (mandatory)
Category_Usage_Financial         - Spending patterns (mandatory)
Category_Usage_Additional        - Additional usage details (optional)
Category_Usage_Consideration     - Future consideration (mandatory)
User_Category_Rules              - User/non-user logic (mandatory)
Confidentiality_Agreement        - Confidentiality text (mandatory)
```

### Brand/Product Awareness Section
```
Product_Usage                    - Product usage intro text (mandatory)
Product_Usage_Frequency          - Usage and purchase frequency (mandatory)
Product_Usage_Financial          - Spending and channels (mandatory)
Purchase_Decision_Influence      - Decision influencers (optional)
Brand_Recall_Unaided             - Top-of-mind brands (mandatory)
Brand_Awareness_Funnel           - Aware→Consider→Purchase→Prefer (mandatory for brand studies)
Product_Satisfaction             - Satisfaction ratings (mandatory)
```

### Concept Exposure Section
```
Concept_Intro                    - Concept introduction text (mandatory)
Message_Reaction                 - Feature/name preference (optional)
Concept_Impression               - Overall impression (mandatory)
Concept_Feature_Highlight        - Important features (optional)
Concept_Evaluation_Funnel        - Follow-up, new, meets needs, recommend (optional)
Concept_Purchase_Likelihood      - Purchase likelihood (mandatory)
```

### Methodology Section
```
Concept_Intro                    - Pricing intro text (reused, mandatory)

# Van Westendorp (all mandatory if VW methodology)
VW_Price_Too_Cheap               - "Too cheap to trust quality"
VW_Price_Bargain                 - "Bargain/good value"
VW_Price_Getting_Expensive       - "Starting to get expensive"
VW_Price_Too_Expensive           - "Too expensive to consider"
VW_Purchase_Likelihood           - Purchase likelihood at chosen price (optional)

# Gabor Granger
GG_Price_Acceptance              - Sequential price acceptance (mandatory if GG)
```

### Additional Questions Section
```
Additional_Demographics          - Education, employment, salary, ethnicity (optional)
Adoption_Behavior                - New product adoption (optional)
Media_Consumption                - Platform activity (optional)
Additional_Awareness             - Feature/tech awareness (optional)
```

## Architecture

### 1. QNR Label Taxonomy Service
**File: `src/services/qnr_label_taxonomy.py`**

Loads standardized label definitions from CSV files:

```python
from typing import Dict, List, Optional
import csv
import os
from pathlib import Path

class LabelDefinition:
    """Single label definition"""
    def __init__(self, name: str, category: str, description: str, 
                 mandatory: bool, applicable_labels: Optional[List[str]], 
                 label_type: str):
        self.name = name
        self.category = category
        self.description = description
        self.mandatory = mandatory
        self.applicable_labels = applicable_labels or []
        self.label_type = label_type
        self.detection_patterns = self._build_patterns()
    
    def _build_patterns(self) -> List[str]:
        """Build detection keywords from label name and description"""
        # Convert label name to keywords
        # e.g., "Recent_Participation" → ["recent", "participation", "participated"]
        pass

class QNRLabelTaxonomy:
    """Manages QNR label definitions and requirements"""
    
    def __init__(self, csv_directory: str = "QNR_Labeling"):
        self.labels: Dict[str, LabelDefinition] = {}
        self.categories = {
            'screener': [],
            'brand': [],
            'concept': [],
            'methodology': [],
            'additional': []
        }
        self._load_from_csvs(csv_directory)
    
    def _load_from_csvs(self, directory: str):
        """Load label definitions from CSV files"""
        base_path = Path(directory)
        
        # Map CSV files to categories
        csv_files = {
            'screener': 'Screener*.csv',
            'brand': 'Brand*.csv',
            'concept': 'Concept*.csv',
            'methodology': 'Methodology*.csv',
            'additional': 'Additional*.csv'
        }
        
        for category, pattern in csv_files.items():
            files = list(base_path.glob(pattern))
            if files:
                self._load_category_csv(files[0], category)
    
    def get_required_labels(self, section_id: int, methodology: Optional[List[str]] = None,
                          industry: Optional[str] = None) -> List[LabelDefinition]:
        """Get required labels for a section based on context"""
        section_map = {
            1: [],  # Sample Plan - no question labels, just text blocks
            2: 'screener',
            3: 'brand',
            4: 'concept',
            5: 'methodology',
            6: 'additional',
            7: []  # Programmer Instructions
        }
        
        category = section_map.get(section_id)
        if not category:
            return []
        
        labels = self.categories.get(category, [])
        
        # Filter by methodology
        if methodology and category == 'methodology':
            labels = [l for l in labels if self._matches_methodology(l, methodology)]
        
        # Filter by industry
        if industry:
            labels = [l for l in labels if self._matches_industry(l, industry)]
        
        return [l for l in labels if l.mandatory]
    
    def _matches_methodology(self, label: LabelDefinition, methodologies: List[str]) -> bool:
        """Check if label applies to given methodologies"""
        if not label.applicable_labels:
            return True
        return any(m.lower() in [a.lower() for a in label.applicable_labels] 
                  for m in methodologies)
```

### 2. Question Label Detector (Deterministic)
**File: `src/services/question_label_detector.py`**

Rule-based pattern matching for label detection:

```python
from typing import Dict, List, Set
import re

class QuestionLabelDetector:
    """Deterministic rule-based label detection"""
    
    def __init__(self, taxonomy: QNRLabelTaxonomy):
        self.taxonomy = taxonomy
        self.patterns = self._build_detection_patterns()
    
    def _build_detection_patterns(self) -> Dict[str, List[Dict]]:
        """Build detection patterns for each label"""
        return {
            'Recent_Participation': [
                {'keywords': ['participated', 'market research', 'recent study', 'past 6 months', 'last 6 months']},
                {'question_type': 'single_choice'},
            ],
            'Conflict_Of_Interest_Check': [
                {'keywords': ['work for', 'employed by', 'conflict of interest', 'employee of', 'work in']},
                {'context': ['company', 'industry', 'competitor']},
            ],
            'Demographics_Basic': [
                {'keywords': ['age', 'gender', 'male', 'female', 'age range', 'age group']},
            ],
            'Brand_Recall_Unaided': [
                {'keywords': ['brands', 'think of', 'top of mind', 'come to mind', 'aware of brands']},
                {'negative_keywords': ['list', 'shown']},  # Must NOT have these (unaided)
            ],
            'Brand_Awareness_Funnel': [
                {'keywords': ['aware', 'considered', 'purchased', 'continue', 'prefer']},
                {'question_type': 'matrix_likert'},
                {'min_options': 4},  # Must have multiple stages
            ],
            'VW_Price_Too_Cheap': [
                {'keywords': ['too cheap', 'too inexpensive', 'suspiciously cheap']},
                {'question_type': 'numeric_open'},
                {'context': ['price', 'cost']},
            ],
            'VW_Price_Bargain': [
                {'keywords': ['bargain', 'good value', 'great deal', 'good price']},
                {'question_type': 'numeric_open'},
            ],
            'VW_Price_Getting_Expensive': [
                {'keywords': ['getting expensive', 'starting to expensive', 'bit expensive']},
                {'question_type': 'numeric_open'},
            ],
            'VW_Price_Too_Expensive': [
                {'keywords': ['too expensive', 'prohibitively expensive', 'cannot afford']},
                {'question_type': 'numeric_open'},
            ],
        }
    
    def detect_labels_in_question(self, question: Dict) -> List[str]:
        """Detect applicable labels for a single question (deterministic)"""
        detected = []
        q_text = question.get('text', '').lower()
        q_type = question.get('type', '')
        q_options = question.get('options', [])
        
        for label_name, patterns in self.patterns.items():
            if self._matches_patterns(q_text, q_type, q_options, patterns):
                detected.append(label_name)
        
        return detected
    
    def _matches_patterns(self, text: str, q_type: str, options: List, 
                         patterns: List[Dict]) -> bool:
        """Check if question matches all pattern requirements"""
        for pattern in patterns:
            # Keyword matching
            if 'keywords' in pattern:
                if not any(kw in text for kw in pattern['keywords']):
                    return False
            
            # Negative keywords (must NOT be present)
            if 'negative_keywords' in pattern:
                if any(kw in text for kw in pattern['negative_keywords']):
                    return False
            
            # Question type matching
            if 'question_type' in pattern:
                if q_type != pattern['question_type']:
                    return False
            
            # Context keywords (additional required terms)
            if 'context' in pattern:
                if not any(ctx in text for ctx in pattern['context']):
                    return False
            
            # Minimum options count
            if 'min_options' in pattern:
                if len(options) < pattern['min_options']:
                    return False
        
        return True
    
    def detect_labels_in_section(self, section: Dict) -> Set[str]:
        """Detect all labels in a section"""
        all_labels = set()
        for question in section.get('questions', []):
            labels = self.detect_labels_in_question(question)
            all_labels.update(labels)
        return all_labels
    
    def detect_labels_in_survey(self, survey: Dict) -> Dict[int, Set[str]]:
        """Detect labels across entire survey, grouped by section"""
        section_labels = {}
        for section in survey.get('sections', []):
            section_id = section.get('id')
            section_labels[section_id] = self.detect_labels_in_section(section)
        return section_labels
```

### 3. Survey Structure Validator (Non-Blocking)
**File: `src/services/survey_structure_validator.py`**

Validation that flags issues but never blocks:

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class IssueSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    severity: IssueSeverity
    section_id: Optional[int]
    label: str
    message: str
    suggestion: str
    
@dataclass
class StructureValidationReport:
    """Non-blocking validation report"""
    survey_id: str
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    section_scores: Dict[int, float]
    detected_labels: Dict[int, Set[str]]
    missing_required_labels: Dict[int, List[str]]
    
    def is_high_quality(self) -> bool:
        """Check if survey meets quality threshold (non-blocking)"""
        return self.overall_score >= 0.85
    
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues (for flagging)"""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)
    
    def get_summary(self) -> str:
        """Human-readable summary"""
        if self.overall_score >= 0.90:
            return f"✅ Excellent structure ({self.overall_score:.0%})"
        elif self.overall_score >= 0.75:
            return f"⚠️ Good structure with minor issues ({self.overall_score:.0%})"
        elif self.overall_score >= 0.60:
            return f"⚠️ Acceptable structure with issues ({self.overall_score:.0%})"
        else:
            return f"❌ Poor structure - review recommended ({self.overall_score:.0%})"

class SurveyStructureValidator:
    """Non-blocking survey structure validation"""
    
    def __init__(self, db_session):
        self.taxonomy = QNRLabelTaxonomy()
        self.detector = QuestionLabelDetector(self.taxonomy)
    
    async def validate_structure(self, survey_json: Dict, 
                                 rfq_context: Dict) -> StructureValidationReport:
        """
        Validate survey structure - NEVER blocks generation
        Returns quality score and flagged issues
        """
        issues = []
        section_scores = {}
        detected_labels = self.detector.detect_labels_in_survey(survey_json)
        missing_required = {}
        
        # Extract context
        methodology = rfq_context.get('methodology_tags', [])
        industry = rfq_context.get('industry')
        
        # Validate each section
        for section in survey_json.get('sections', []):
            section_id = section.get('id')
            section_issues, section_score, missing = self._validate_section(
                section, detected_labels.get(section_id, set()), 
                methodology, industry
            )
            issues.extend(section_issues)
            section_scores[section_id] = section_score
            if missing:
                missing_required[section_id] = missing
        
        # Methodology-specific validation
        if 'van_westendorp' in [m.lower() for m in methodology]:
            vw_issues, vw_score = self._validate_van_westendorp(detected_labels)
            issues.extend(vw_issues)
            section_scores[5] = min(section_scores.get(5, 1.0), vw_score)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(section_scores, issues)
        
        return StructureValidationReport(
            survey_id=survey_json.get('id', 'unknown'),
            overall_score=overall_score,
            issues=issues,
            section_scores=section_scores,
            detected_labels=detected_labels,
            missing_required_labels=missing_required
        )
    
    def _validate_section(self, section: Dict, detected: Set[str],
                         methodology: List[str], industry: str) -> tuple:
        """Validate a single section"""
        issues = []
        section_id = section.get('id')
        
        # Get required labels for this section
        required_labels = self.taxonomy.get_required_labels(
            section_id, methodology, industry
        )
        
        # Check for missing required labels
        missing = []
        for label_def in required_labels:
            if label_def.name not in detected:
                missing.append(label_def.name)
                
                # Determine severity
                if label_def.name in ['Recent_Participation', 'Conflict_Of_Interest_Check']:
                    severity = IssueSeverity.CRITICAL
                elif label_def.name.startswith('VW_Price_'):
                    severity = IssueSeverity.ERROR
                else:
                    severity = IssueSeverity.WARNING
                
                issues.append(ValidationIssue(
                    severity=severity,
                    section_id=section_id,
                    label=label_def.name,
                    message=f"Missing required label: {label_def.name}",
                    suggestion=f"Add question for: {label_def.description}"
                ))
        
        # Calculate section score
        if required_labels:
            score = 1.0 - (len(missing) / len(required_labels))
        else:
            score = 1.0
        
        return issues, score, missing
    
    def _validate_van_westendorp(self, detected_labels: Dict[int, Set[str]]) -> tuple:
        """Validate Van Westendorp 4-price requirement"""
        issues = []
        
        required_vw = [
            'VW_Price_Too_Cheap',
            'VW_Price_Bargain',
            'VW_Price_Getting_Expensive',
            'VW_Price_Too_Expensive'
        ]
        
        # Check methodology section (id=5)
        methodology_labels = detected_labels.get(5, set())
        missing_vw = [vw for vw in required_vw if vw not in methodology_labels]
        
        if missing_vw:
            issues.append(ValidationIssue(
                severity=IssueSeverity.CRITICAL,
                section_id=5,
                label='Van_Westendorp_Complete',
                message=f"Van Westendorp requires 4 price questions. Missing: {', '.join(missing_vw)}",
                suggestion="Add all 4 Van Westendorp price sensitivity questions in Methodology section"
            ))
            score = len(required_vw) - len(missing_vw)) / len(required_vw)
        else:
            score = 1.0
        
        return issues, score
    
    def _calculate_overall_score(self, section_scores: Dict[int, float], 
                                 issues: List[ValidationIssue]) -> float:
        """Calculate overall structure quality score"""
        # Average section scores
        if section_scores:
            avg_score = sum(section_scores.values()) / len(section_scores)
        else:
            avg_score = 1.0
        
        # Penalty for critical issues
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        
        penalty = (critical_count * 0.15) + (error_count * 0.05)
        
        return max(0.0, avg_score - penalty)
```

### 4. Workflow Integration (Non-Blocking)
**File: `src/workflows/nodes.py` - Update ValidationAgent**

```python
class ValidationAgent:
    def __init__(self, db: Session):
        self.db = db
        self.structure_validator = SurveyStructureValidator(db)
        # ... existing validators
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """Validation that NEVER blocks generation"""
        validation_results = {
            'passed': True,  # ALWAYS True - never block
            'issues': []
        }
        
        # Run existing validation
        # ... existing code ...
        
        # NEW: Structure validation (non-blocking)
        try:
            structure_report = await self.structure_validator.validate_structure(
                survey_json=state.generated_survey,
                rfq_context={
                    'methodology_tags': state.methodology_tags or [],
                    'industry': state.industry_category,
                    'respondent_type': getattr(state, 'respondent_type', None)
                }
            )
            
            validation_results['structure_validation'] = {
                'score': structure_report.overall_score,
                'summary': structure_report.get_summary(),
                'issues': [
                    {
                        'severity': issue.severity.value,
                        'section_id': issue.section_id,
                        'label': issue.label,
                        'message': issue.message,
                        'suggestion': issue.suggestion
                    }
                    for issue in structure_report.issues
                ],
                'section_scores': structure_report.section_scores,
                'detected_labels': {
                    k: list(v) for k, v in structure_report.detected_labels.items()
                }
            }
            
            # Flag for review if critical issues (but don't block)
            if structure_report.has_critical_issues():
                validation_results['flagged_for_review'] = True
                validation_results['flag_reason'] = 'Critical structural issues detected'
            
        except Exception as e:
            logger.error(f"Structure validation failed: {e}")
            # If validation fails, don't block - just log
            validation_results['structure_validation'] = {
                'error': str(e),
                'score': None
            }
        
        # IMPORTANT: Always return passed=True
        return {
            "validation_results": validation_results,
            "passed": True  # NEVER block generation
        }
```

### 5. Enhanced Prompt (Minimal Addition)
**File: `src/services/prompt_builder.py`**

Add ~800 chars of section requirements:

```python
def build_section_requirements_section(self) -> PromptSection:
    """Build enhanced section requirements"""
    content = [
        "## SECTION-SPECIFIC REQUIREMENTS:",
        "",
        "### Section 2 - Screener:",
        "- Recent participation check (market research in last 6 months)",
        "- Conflict of interest screening (industry employment, competitors)",
        "- Basic demographics (age, gender)",
        "- Category usage qualification",
        "SEQUENCING: General → Specific, terminate early if disqualified",
        "",
        "### Section 3 - Brand/Product Awareness (if brand study):",
        "- Unaided brand recall (top-of-mind brands)",
        "- Brand awareness funnel: Aware → Considered → Purchased → Continue → Preferred",
        "- Product satisfaction ratings",
        "- Usage frequency and patterns",
        "",
        "### Section 5 - Methodology:",
        "**Van Westendorp (if pricing study):**",
        "- Too cheap price point",
        "- Bargain/good value price point",
        "- Getting expensive price point",
        "- Too expensive price point",
        "",
        "**Gabor Granger (if pricing study):**",
        "- Sequential price acceptance questions",
        ""
    ]
    return PromptSection("section_requirements", content, order=2.5)
```

## Implementation Phases

### Phase 1: Core Services (3 days)
1. ✅ Create `QNRLabelTaxonomy` - Load CSV data with standardized names
2. ✅ Create `QuestionLabelDetector` - Deterministic pattern matching
3. ✅ Create `SurveyStructureValidator` - Non-blocking validation
4. ✅ Add unit tests for label detection accuracy

### Phase 2: Integration (2 days)
1. ✅ Integrate into ValidationAgent (non-blocking)
2. ✅ Add structure validation to API responses
3. ✅ Enhance prompt with section requirements (+800 chars)
4. ✅ Test end-to-end workflow

### Phase 3: UI & Reporting (2 days)
1. ✅ Structure validation report component
2. ✅ Label badges in annotation UI
3. ✅ Quality score display in survey preview
4. ✅ Flagged survey list/filter

## Success Criteria

### Accuracy (Deterministic)
- ✅ Label detection is 100% reproducible (same input = same output)
- ✅ Van Westendorp detection: >95% precision
- ✅ Screener label detection: >90% precision
- ✅ No false positives for critical labels (CoI, Recent Participation)

### Non-Blocking
- ✅ Validation NEVER stops survey generation
- ✅ All surveys complete workflow regardless of structure score
- ✅ Issues are flagged, not blocked

### Quality Scoring
- ✅ Structure score correlates with manual quality ratings
- ✅ Critical issues (missing VW questions) clearly flagged
- ✅ Good surveys score >0.85
- ✅ Bad surveys score <0.60

### Simplicity
- ✅ Rule-based patterns are maintainable
- ✅ No LLM calls added
- ✅ Clear error messages with actionable suggestions
- ✅ <500ms validation time per survey

## Files to Create

**New Files:**
- `src/services/qnr_label_taxonomy.py` (200 lines)
- `src/services/question_label_detector.py` (300 lines)
- `src/services/survey_structure_validator.py` (250 lines)
- `migrations/020_add_qnr_label_taxonomy.sql` (100 lines)
- `tests/test_label_detection.py` (200 lines)
- `tests/test_structure_validation.py` (150 lines)
- `frontend/src/components/StructureValidationReport.tsx` (150 lines)

**Modified Files:**
- `src/workflows/nodes.py` - Add structure validation (+50 lines)
- `src/services/prompt_builder.py` - Add section requirements (+30 lines)
- `src/api/survey.py` - Include structure validation in responses (+20 lines)
- `frontend/src/components/SurveyPreview.tsx` - Show structure score (+30 lines)

**Total:** ~1,500 new lines, ~130 modified lines

## Example Output

### Good Survey (Score: 0.92)
```
✅ Excellent structure (92%)

Detected Labels:
- Section 2 (Screener): Recent_Participation, Conflict_Of_Interest_Check, Demographics_Basic ✅
- Section 3 (Brand): Brand_Recall_Unaided, Brand_Awareness_Funnel, Product_Satisfaction ✅
- Section 5 (Methodology): VW_Price_Too_Cheap, VW_Price_Bargain, VW_Price_Getting_Expensive, VW_Price_Too_Expensive ✅

Issues: None
```

### Flagged Survey (Score: 0.68)
```
⚠️ Acceptable structure with issues (68%)

Detected Labels:
- Section 2 (Screener): Recent_Participation, Demographics_Basic ✅
- Section 5 (Methodology): VW_Price_Too_Expensive, VW_Price_Bargain ⚠️

Issues:
❌ CRITICAL: Missing Conflict_Of_Interest_Check in Screener
   → Add question about industry employment or competitor affiliation

❌ ERROR: Van Westendorp incomplete - Missing: VW_Price_Too_Cheap, VW_Price_Getting_Expensive
   → Add all 4 Van Westendorp price sensitivity questions

⚠️ WARNING: Missing Brand_Awareness_Funnel in Brand section
   → Consider adding brand funnel questions (Aware → Consider → Purchase → Prefer)
```

## To-dos

- [ ] Create QNRLabelTaxonomy service with standardized label names
- [ ] Build QuestionLabelDetector with deterministic pattern matching
- [ ] Implement SurveyStructureValidator with non-blocking validation
- [ ] Add section requirements to prompt builder (~800 chars)
- [ ] Create migration for qnr_label_definitions table
- [ ] Integrate structure validation into ValidationAgent (non-blocking)
- [ ] Build StructureValidationReport UI component
- [ ] Add label badges to annotation UI
- [ ] Create API endpoint for structure validation
- [ ] Write comprehensive tests for label detection accuracy


