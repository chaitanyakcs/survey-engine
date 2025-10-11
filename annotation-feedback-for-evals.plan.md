# Annotation Feedback Loop - Survey Generation First, Then Evaluations

## Strategy: Immediate Value → Long-term Intelligence

**Priority:** Improve survey generation quality using annotation feedback (immediate visible results), then improve evaluations once we have enough data.

**Current State:** <10 annotated surveys, annotation system exists but not connected to generation or evaluation.

---

## Phase 0: Quick Wins - Immediate Generation Improvements (Week 1-2)

**Goal:** Use existing 5-10 annotations to immediately improve survey generation

**Why Start Here:** Provides immediate visible value, works with minimal data, builds momentum for annotation campaign.

### Implementation Tasks:

1. **Annotation-Weighted Golden Example Retrieval** (2 days)
   - File: `src/services/retrieval_service.py`
   - **Survey-level**: Add annotation score lookup in `retrieve_golden_pairs()`
   - **Question-level**: Extract and weight individual questions by their annotation scores
   - **Section-level**: Extract and weight sections by their annotation scores
   - Boost high-quality examples (score ≥4.0) by 1.3x similarity
   - Penalize low-quality examples (score <3.0) by 0.5x similarity
   - Filter out any examples with score <2.5

2. **Extract High-Quality Patterns** (2 days)
   - File: `src/services/annotation_insights_service.py` (NEW)
   - **Survey-level**: Analyze surveys with pillar scores ≥4
   - **Question-level**: Extract patterns from individual high-scoring questions
   - **Section-level**: Extract patterns from high-scoring sections
   - Extract: avg question length, phrasing patterns, scale designs, section structure
   - Create "quality guidelines" from patterns

3. **Extract Low-Quality Patterns** (2 days)
   - Analyze surveys/questions/sections with scores <3
   - Mine annotation comments for issues: "leading", "confusing", "too long"
   - Create "avoid these patterns" list
   - Detect: bias words, double-barreled questions, unclear scales

4. **Update Generation Prompts** (1 day)
   - File: `src/services/prompt_service.py`
   - Add annotation insights section to system prompt
   - Include: high-quality patterns, issues to avoid, common feedback themes
   - **Question-level examples**: "Use this 5-point satisfaction question format"
   - **Section-level examples**: "Follow this screening section structure"

5. **Simple Dashboard** (1 day)
   - Show: annotation statistics, high-quality examples, common issues
   - Display question-level and section-level golden examples
   - Validate improvements are working

**Deliverables:**
- Annotation-weighted retrieval (survey, question, section level)
- Insights service extracting patterns at all levels
- Enhanced prompts with quality guidelines and examples
- Basic dashboard showing granular improvements

**Success Criteria:**
- New surveys show 10-15% improvement when annotated
- High-quality questions and sections used more frequently
- Annotators report seeing improvements in specific question types

**Data Needed:** 5-10 annotations (you have this!)

---

## Phase 1: Systematic Feedback Loop (Weeks 3-6)

**Goal:** Build systematic feedback from annotations to generation

**Data Needed:** 20-50 annotations (collect during Phase 0-1)

### Implementation Tasks:

1. **Question Quality Database** (1 week)
   - File: `src/services/question_quality_service.py` (NEW)
   - Store question-level annotations with scores
   - Query: "Show me 5-point scale questions about satisfaction with score ≥4"
   - Track which question types succeed
   - **Database table**: `golden_questions` with question text, type, scale, score

2. **Section Quality Database** (1 week)
   - File: `src/services/section_quality_service.py` (NEW)
   - Store section-level annotations with scores
   - Query: "Show me screening sections with score ≥4"
   - Track which section structures succeed
   - **Database table**: `golden_sections` with section title, questions, score

3. **Dynamic Prompt Assembly** (1 week)
   - File: `src/services/prompt_service.py` (enhance)
   - Select relevant high-quality examples per RFQ
   - Match by: methodology, industry, question type, section type
   - Include 2-3 exemplar questions AND sections in prompt

4. **A/B Testing Framework** (1 week)
   - File: `src/services/generation_experiment_service.py` (NEW)
   - 50% with annotation-enhanced prompts, 50% without
   - Track which performs better
   - Measure statistical significance

5. **Impact Dashboard** (3 days)
   - Component: `frontend/src/components/AnnotationImpact.tsx` (NEW)
   - Show annotators: "Your feedback improved X surveys"
   - Display: quality trends, improvement metrics
   - Show question-level and section-level impact

**Deliverables:**
- Question and section quality databases
- Dynamic prompt system with granular examples
- A/B testing showing improvements
- Impact visualization

**Success Criteria:**
- 20% improvement in annotation scores vs baseline
- A/B test shows p<0.05 significance
- Template usage in 60%+ of surveys

---

## Phase 2: Predictive Quality System (Weeks 7-12)

**Goal:** Predict quality before survey finalization, enable iterative improvement

**Data Needed:** 50-100 annotations

### Implementation Tasks:

1. **Real-Time Quality Prediction** (2 weeks)
   - File: `src/services/quality_prediction_service.py` (NEW)
   - Train Random Forest on survey features
   - **Question-level prediction**: Predict individual question scores
   - **Section-level prediction**: Predict section scores
   - **Survey-level prediction**: Predict overall survey score
   - Integration: after generation, before finalization

2. **Iterative Generation** (2 weeks)
   - File: `src/services/generation_service.py` (enhance)
   - If predicted score <3.5, trigger improvement
   - **Question-level refinement**: Regenerate low-scoring questions
   - **Section-level refinement**: Regenerate weak sections
   - Retry up to 2 times

3. **Smart Quality Branching** (1 week)
   - File: `src/workflows/nodes.py` add `QualityCheckAgent` (NEW)
   - Path A (≥4.0): Finalize immediately
   - Path B (3.0-3.9): Light refinement
   - Path C (<3.0): Major revision

4. **User-Facing Quality Scores** (1 week)
   - Display: "Predicted quality: 4.2/5 (High confidence)"
   - Show question-level and section-level predictions
   - Track prediction accuracy

**Deliverables:**
- Quality prediction service (survey, question, section level)
- Iterative generation workflow
- Smart quality branching
- Confidence scores

**Success Criteria:**
- Predictions correlate >0.7 with actual annotations
- Iterative improvement raises scores by 0.5 points
- Path A surveys get 4.0+ annotations 80% of time

---

## Phase 3: Advanced Generation Intelligence (Weeks 13-18)

**Goal:** Sophisticated learning from annotation patterns

**Data Needed:** 100-200 annotations

### Implementation Tasks:

1. **NLP Comment Analysis** (2 weeks)
   - File: `src/services/comment_analyzer_service.py` (NEW)
   - Use spaCy/transformers to extract insights
   - Categorize: clarity, bias, length, structure issues
   - Track frequency and severity
   - **Question-level analysis**: Why specific questions scored low
   - **Section-level analysis**: Why specific sections scored low

2. **Question Improvement Suggestions** (2 weeks)
   - File: `src/services/question_improvement_service.py` (NEW)
   - Analyze why questions scored low
   - Generate specific suggestions
   - Allow one-click regeneration
   - Use golden question examples as templates

3. **Methodology-Specific Models** (2 weeks)
   - Train separate models per methodology
   - Route to appropriate model based on RFQ
   - **Question-type specific**: Different models for satisfaction vs NPS vs rating

4. **Template Library** (1 week)
   - Extract questions with score ≥4.5 as templates
   - Extract sections with score ≥4.5 as templates
   - Parameterize and categorize
   - Use as generation starting points

**Deliverables:**
- NLP-powered comment analysis
- Automated improvement suggestions
- Methodology-specific models
- Template library (100+ question templates, 50+ section templates)

**Success Criteria:**
- 30-40% improvement vs baseline
- Methodology models improve accuracy by 25%
- Templates score 4.2+ average

---

## Phase 4: Now Improve Evaluations (Weeks 19-26)

**Goal:** With 150-300 annotations collected, calibrate evaluators to match human judgment

**Data Needed:** 150-300 annotations

### Implementation Tasks:

1. **Evaluation Calibration** (2 weeks)
   - File: `src/services/evaluation_calibration_service.py` (NEW)
   - Compare eval scores vs annotation scores
   - Calculate per-pillar correlations
   - Apply calibration factors
   - **Question-level calibration**: Calibrate question evaluators
   - **Section-level calibration**: Calibrate section evaluators

2. **Annotation-Informed Eval Prompts** (2 weeks)
   - Files: `evaluations/modules/*_evaluator.py` (enhance)
   - Include concrete examples from annotations
   - Show what each score level (1-5) looks like
   - Use golden question and section examples

3. **Hybrid LLM + ML Evaluation** (2 weeks)
   - Train ML model to predict annotations
   - Combine: 70% LLM + 30% ML
   - Use as sanity check

4. **Active Learning** (2 weeks)
   - File: `src/services/active_annotation_service.py` (NEW)
   - Identify surveys where evaluator is uncertain
   - Prioritize for annotation

**Deliverables:**
- Calibrated evaluators
- Annotation-informed prompts
- Hybrid evaluation
- Active learning system

**Success Criteria:**
- Eval-annotation correlation >0.80
- Per-pillar correlation all >0.75
- Active learning reduces annotation needs by 35%

---

## Phase 5: Full RLHF Loop (Weeks 27+)

**Goal:** Reinforcement learning from human feedback, self-improving system

**Data Needed:** 300-500+ annotations

### Implementation Tasks:

1. **Reward Model Training** (3 weeks)
   - File: `src/services/reward_model_service.py` (NEW)
   - Predict human preferences between survey pairs
   - Use annotation scores as rewards
   - **Question-level rewards**: Learn from question preferences
   - **Section-level rewards**: Learn from section preferences

2. **RLHF for Generation** (3 weeks)
   - Optimize prompts to maximize annotation scores
   - A/B test RLHF vs rule-based

3. **Continuous Learning Pipeline** (3 weeks)
   - File: `src/services/continuous_learning_pipeline.py` (NEW)
   - Auto-retrain when threshold reached
   - Monitor quality, detect degradation
   - Deploy without human intervention

**Deliverables:**
- Reward model (>80% accuracy)
- RLHF-optimized generation
- Automated pipeline

**Success Criteria:**
- New surveys: 4.0+ average annotation score
- Eval-annotation correlation: >0.85
- Minimal human oversight needed

---

## Database Schema Changes

### New Tables for Granular Golden Examples:

```sql
-- Question-level golden examples
CREATE TABLE golden_questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    scale_design JSONB,
    annotation_score DECIMAL(3,1),
    comment TEXT,
    methodology VARCHAR(50),
    industry VARCHAR(50),
    survey_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Section-level golden examples  
CREATE TABLE golden_sections (
    id SERIAL PRIMARY KEY,
    section_title VARCHAR(200),
    questions JSONB, -- Array of question texts
    annotation_score DECIMAL(3,1),
    comment TEXT,
    methodology VARCHAR(50),
    industry VARCHAR(50),
    survey_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Question templates (from Phase 3)
CREATE TABLE question_templates (
    id SERIAL PRIMARY KEY,
    template_text TEXT NOT NULL,
    parameters JSONB, -- Parameterizable parts
    question_type VARCHAR(50),
    methodology VARCHAR(50),
    avg_score DECIMAL(3,1),
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Quick Start Guide

### Week 1-2 (START HERE with 5-10 annotations):

1. **Day 1-2:** Modify `retrieval_service.py` - weight by annotation scores (survey, question, section level)
2. **Day 3-4:** Create `annotation_insights_service.py` - extract patterns at all levels
3. **Day 5-6:** Update `prompt_service.py` - add quality guidelines and examples
4. **Day 7-8:** Build simple dashboard, validate improvements

### Expected Result:
Generate 5-10 new surveys → annotate them → should score 10-15% higher

### Parallel: Annotation Campaign
- While implementing Phase 0, collect 10-20 more annotations
- Focus on question-level and section-level annotations
- Enables Phase 1 by Week 3

---

## Key Files by Phase

**Phase 0 (2 weeks, 5-10 annotations):**
- Modify: `src/services/retrieval_service.py` (add question/section level weighting)
- Modify: `src/services/prompt_service.py` (add granular examples)
- Create: `src/services/annotation_insights_service.py` (extract patterns at all levels)

**Phase 1 (4 weeks, 20-50 annotations):**
- Create: `src/services/question_quality_service.py`
- Create: `src/services/section_quality_service.py`
- Create: `src/services/generation_experiment_service.py`
- Create: `frontend/src/components/AnnotationImpact.tsx`

**Phase 2 (6 weeks, 50-100 annotations):**
- Create: `src/services/quality_prediction_service.py` (multi-level prediction)
- Modify: `src/services/generation_service.py` (iterative improvement)
- Create: `src/workflows/nodes.py.QualityCheckAgent`

**Phase 3 (6 weeks, 100-200 annotations):**
- Create: `src/services/comment_analyzer_service.py`
- Create: `src/services/question_improvement_service.py`
- Create: Database tables `question_templates`, `golden_questions`, `golden_sections`

**Phase 4 (8 weeks, 150-300 annotations):**
- Create: `src/services/evaluation_calibration_service.py`
- Modify: `evaluations/modules/*_evaluator.py`
- Create: `frontend/src/components/EvaluationAccuracy.tsx`

**Phase 5 (ongoing, 300-500+ annotations):**
- Create: `src/services/reward_model_service.py`
- Create: `src/services/continuous_learning_pipeline.py`

---

## Success Metrics - Generation First!

### Phase-by-Phase:
- **Phase 0:** +10-15% annotation score improvement (immediate!)
- **Phase 1:** +20% improvement (systematic feedback)
- **Phase 2:** +30% improvement (predictive quality)
- **Phase 3:** +40% improvement (advanced intelligence)
- **Phase 4:** Eval correlation >0.80 (calibrated evaluators)
- **Phase 5:** Eval correlation >0.85, self-improving system

### Business Impact:
- Survey quality: 3.2/5 baseline → 4.2+/5 by Phase 3
- Iteration cycles: 2-3 revisions → <1 revision
- User satisfaction: 3.5/5 → 4.5+/5
- Annotation efficiency: -35% workload via active learning

---

## Annotation Collection Strategy

### Pace (parallel with implementation):
- **Week 1-2:** Use existing 5-10 → see Phase 0 results
- **Week 3-6:** Collect 20-30 total → enables Phase 1
- **Week 7-12:** Collect 70-90 total → enables Phase 2
- **Week 13-18:** Collect 150-180 total → enables Phase 3
- **Week 19-26:** Collect 280+ total → enables Phase 4
- **Week 27+:** Continuous flow 300-500+ → enables Phase 5

### Strategy:
- **Question-level annotations**: Rate individual questions (not just surveys)
- **Section-level annotations**: Rate individual sections
- Annotate newly generated surveys to validate improvements
- Prioritize diverse coverage (methodologies, industries)
- Encourage detailed comments (enables Phase 3 NLP)

### Virtuous Cycle:
Better generation → Better surveys → Easier annotation → More data → Even better generation

---

## Risk Mitigation

**Risk:** Not enough annotation data
- **Mitigation:** Phase 0-1 work with 5-50 annotations, provide immediate value

**Risk:** Poor annotation quality
- **Mitigation:** Create clear guidelines, track inter-annotator agreement

**Risk:** Improvements don't show up in annotations
- **Mitigation:** A/B testing in Phase 1 validates improvements objectively

**Risk:** Overfitting to small dataset
- **Mitigation:** Use cross-validation, start simple (Phase 2+)

---

## Benefits of Question/Section Level Approach

### 1. **More Precise Learning**
- Learn from individual good questions, not just good surveys
- Avoid bad questions even in good surveys
- Mix and match: good screening section + good product questions

### 2. **Faster Implementation**
- Can start with just a few high-quality questions
- Don't need complete surveys to be annotated
- More data points from same annotation effort

### 3. **Better Pattern Matching**
- Match question type, not just overall survey topic
- Reuse specific question formats that work
- Learn section structure patterns

### 4. **Granular Feedback**
- Annotators can rate individual questions
- Get more learning from limited annotation data
- Identify specific improvement opportunities

---

## To-dos

- [ ] Phase 0 (Week 1-2): Implement annotation-weighted retrieval (survey/question/section level), extract patterns, update prompts - Works with 5-10 annotations!
- [ ] Phase 1 (Week 3-6): Build question and section quality databases, dynamic prompts, A/B testing - Needs 20-50 annotations
- [ ] Phase 2 (Week 7-12): Add quality prediction (multi-level), iterative generation, smart branching - Needs 50-100 annotations
- [ ] Phase 3 (Week 13-18): NLP comment analysis, improvement suggestions, templates - Needs 100-200 annotations
- [ ] Phase 4 (Week 19-26): NOW calibrate evaluators to match humans, active learning - Needs 150-300 annotations
- [ ] Phase 5 (Week 27+): Full RLHF, reward models, continuous learning pipeline - Needs 300-500+ annotations
