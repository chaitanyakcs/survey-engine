# Survey Generation Engine - Executable Specification

## 🎯 Project Overview
Transform RFQs into researcher-ready surveys, reducing cleanup time from 3-4 hours to <30 minutes using AI with golden standard examples and methodology compliance.

## 🏗️ System Architecture

### Tech Stack Requirements
- **Backend**: FastAPI with Python 3.11+, UV for installation.
- **Database**: PostgreSQL 15+ with pgvector extension
- **AI/ML**: OpenAI API (GPT-4/5), Sentence Transformers, FAISS
- **Orchestration**: LangGraph for agent workflows
- **Infrastructure**: Docker, Redis for caching

### Core Components
1. **RAG Retrieval System**: Multi-tier golden standards → methodology blocks → templates
2. **LangGraph Workflow**: RFQ → Golden Retrieval → Context Building → Generation → Validation → Human Review
3. **Validation Engine**: Schema + methodology compliance + golden similarity scoring
4. **Training Pipeline**: Capture edits for SFT/RLHF progression

## 📊 Data Model Specification

### Core Entities
```sql
-- Golden Standards (Priority Tier 1)
CREATE TABLE golden_rfq_survey_pairs (
    id UUID PRIMARY KEY,
    rfq_text TEXT NOT NULL,
    rfq_embedding VECTOR(1536),
    survey_json JSONB NOT NULL,
    methodology_tags TEXT[],
    industry_category TEXT,
    research_goal TEXT,
    quality_score DECIMAL(3,2), -- 0.00-1.00
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT now()
);

-- RFQs and Generated Surveys
CREATE TABLE rfqs (
    id UUID PRIMARY KEY,
    title TEXT,
    description TEXT NOT NULL,
    product_category TEXT,
    target_segment TEXT,
    research_goal TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE surveys (
    id UUID PRIMARY KEY,
    rfq_id UUID REFERENCES rfqs(id),
    status TEXT CHECK (status IN ('draft','validated','edited','final')),
    raw_output JSONB,
    final_output JSONB,
    golden_similarity_score DECIMAL(3,2),
    used_golden_examples UUID[],
    cleanup_minutes_actual INT,
    model_version TEXT,
    created_at TIMESTAMP DEFAULT now()
);

-- Edit Tracking for Training
CREATE TABLE edits (
    id UUID PRIMARY KEY,
    survey_id UUID REFERENCES surveys(id),
    edit_type TEXT, -- add, delete, modify
    edit_reason TEXT, -- clarity, methodology, redundancy
    before_text TEXT,
    after_text TEXT,
    annotation JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

## 🔄 LangGraph Workflow Specification

### Node Definitions
1. **RFQNode**: Parse RFQ, extract research goals and methodologies, generate embedding
2. **GoldenRetrieverNode**: Multi-tier retrieval (golden pairs → methodology blocks → templates)
3. **ContextBuilderNode**: Assemble hierarchical context with golden examples as few-shot prompts
4. **GeneratorAgent**: GPT-4/5 generation with golden-enhanced prompts
5. **GoldenValidatorNode**: Validate against schema, methodology rules, and golden similarity
6. **ResearcherNode**: Human review interface with golden benchmarks displayed

### Workflow Logic
```python
# Simplified workflow definition
workflow = StateGraph(SurveyGenerationState)

workflow.add_node("parse_rfq", RFQNode())
workflow.add_node("retrieve_golden", GoldenRetrieverNode())
workflow.add_node("build_context", ContextBuilderNode()) 
workflow.add_node("generate", GeneratorAgent())
workflow.add_node("validate", GoldenValidatorNode())
workflow.add_node("human_review", ResearcherNode())

# Flow with retry logic
workflow.add_edge("parse_rfq", "retrieve_golden")
workflow.add_edge("retrieve_golden", "build_context")
workflow.add_edge("build_context", "generate")
workflow.add_edge("generate", "validate")

# Conditional edges for validation
workflow.add_conditional_edges(
    "validate",
    lambda x: "retry" if not x["validation_results"]["quality_gate_passed"] else "human_review",
    {"retry": "generate", "human_review": "human_review"}
)
```

## 🎯 Golden Standards Integration Points

### Retrieval Strategy
1. **Tier 1**: Exact golden RFQ-survey pairs (semantic similarity + methodology match)
2. **Tier 2**: Methodology blocks extracted from golden surveys  
3. **Tier 3**: Individual template questions (fallback)

### Validation Criteria
- **Schema Compliance**: JSON structure validation
- **Methodology Rules**: 
  - VW = exactly 4 pricing questions (too expensive, too cheap, getting expensive, good deal)
  - GG = price ladder with 5-8 incremental price points
  - Conjoint = max 15 attributes, balanced design
- **Golden Similarity**: Minimum 0.75 similarity score to golden examples
- **Quality Gate**: All criteria must pass before human handoff

### Prompt Enhancement
```
GOLDEN STANDARD EXAMPLES:
Example 1: [RFQ] → [Survey Structure] → [Key Principles]
Example 2: [RFQ] → [Survey Structure] → [Key Principles]

CURRENT RFQ: {rfq_text}
REQUIRED METHODOLOGIES: {methodologies}
STRUCTURAL GUIDANCE: {section_flow_from_golden}

Generate survey following golden quality standards.
```

## 📊 Evaluation Framework

### Immediate Metrics (Phase 1)
- **Golden Similarity Score**: Semantic + structural similarity to golden examples
- **Methodology Compliance Rate**: % surveys passing methodology validation  
- **Quality Gate Pass Rate**: % surveys requiring no retry
- **Cleanup Time Reduction**: Measured vs baseline and golden benchmarks

### Training Data Collection
- Capture `(RFQ + golden_context + draft → final_edited)` tuples
- Classify edit reasons: methodology, clarity, tone, redundancy
- Track golden example effectiveness (usage_count, success correlation)

## 🚀 Implementation Phases

### Phase 1 (MVP - Months 0-6)
**Deliverables:**
- FastAPI backend with PostgreSQL + pgvector
- LangGraph workflow with 6 core nodes
- Golden standards retrieval and validation system
- Basic human annotation interface
- Docker deployment setup

**Success Criteria:**
- 60%+ reduction in cleanup time vs raw GPT-4 output
- 80%+ methodology compliance rate
- Golden similarity scores >0.7 average

### Phase 2 (Months 6-12) 
**Deliverables:**
- SFT model using accumulated training data
- Enhanced critic/revision loops
- A/B testing framework for model comparison
- Advanced analytics dashboard

### Phase 3 (Months 12+)
**Deliverables:**
- RLHF implementation with reward models
- Model distillation for cost optimization
- Enterprise deployment features

## 🛠️ Development Requirements

### Environment Setup
```yaml
# Key environment variables with decision-based defaults
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5432/survey_engine_db
REDIS_URL=redis://localhost:6379

# Model configuration - Phase 1 defaults
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Change to text-embedding-3-large for high quality
GENERATION_MODEL=gpt-4-turbo-preview  # Fallback: gpt-3.5-turbo-instruct for cost savings
GOLDEN_SIMILARITY_THRESHOLD=0.75  # Relaxable to 0.65 under volume pressure
MAX_GOLDEN_EXAMPLES=3  # Increase to 5 for complex RFQs

# Validation configuration
METHODOLOGY_VALIDATION_STRICT=true  # false for initial deployment
ENABLE_EDIT_TRACKING=true  # Day 1 requirement
EDIT_GRANULARITY_LEVEL=2  # 1=basic, 2=detailed, 3=comprehensive
QUALITY_GATE_THRESHOLD=50  # Scoring threshold (30-70 range)

# Training trigger thresholds
MIN_EDITS_FOR_SFT_PREP=100
MIN_GOLDEN_PAIRS_FOR_SIMILARITY=10
EDIT_COLLECTION_PRIORITY=question_text,question_type,additions,deletions
```

### API Endpoints Required with Decision Context
```
# Core workflow endpoints
POST /rfq - Submit new RFQ for survey generation
  └── Returns: survey_id, estimated_completion_time, golden_examples_used

GET /survey/{id} - Retrieve generated survey
  └── Include: golden_similarity_score, validation_results, edit_suggestions

PUT /survey/{id}/edit - Submit human edits
  └── Granularity: Based on EDIT_GRANULARITY_LEVEL setting
  └── Required fields: edit_type, edit_reason, before_text, after_text

POST /survey/{id}/validate - Re-run validation with different parameters
  └── Parameters: methodology_strict_mode, golden_similarity_threshold

# Golden standards management
GET /golden-pairs - List available golden standards with usage stats
POST /golden-pairs - Add new golden standard (requires quality_score)
PUT /golden-pairs/{id}/validate - Expert validation of golden pair

# Training data and analytics
GET /training-data/status - Current collection status vs thresholds
GET /analytics/quality-trends - Cleanup time, edit density trends
POST /analytics/model-performance - A/B test different model configurations
```

### Configuration Decision Matrix

| Configuration | Low Volume (<50/month) | Medium Volume (50-500/month) | High Volume (>500/month) | Enterprise |
|---------------|------------------------|------------------------------|---------------------------|------------|
| **Generation Model** | gpt-4-turbo-preview | gpt-4-turbo-preview | gpt-3.5-turbo-instruct | Azure OpenAI GPT-4 |
| **Similarity Threshold** | 0.8 (high quality) | 0.75 (balanced) | 0.65 (efficiency) | 0.75 (compliance) |
| **Edit Tracking Level** | 3 (comprehensive) | 2 (detailed) | 2 (detailed) | 3 (audit trail) |
| **Validation Strictness** | Medium | Strict | Medium | Strict |
| **Retry Attempts** | 3 | 2 | 1 | 2 |
| **Quality Gate Threshold** | 60 | 50 | 40 | 55 |

### Training Data Collection Rules Engine

```yaml
# Configuration-driven collection rules
edit_tracking_rules:
  question_text_changes:
    enabled: true
    min_edit_distance: 5  # Character threshold
    priority: critical
    training_weight: 1.0
  
  question_additions:
    enabled: true
    context_required: true  # Must include reasoning
    priority: critical
    training_weight: 1.2
  
  methodology_corrections:
    enabled: true
    expert_validation: required
    priority: critical
    training_weight: 1.5
  
  tone_adjustments:
    enabled: false  # Start Week 4
    semantic_threshold: 0.3
    priority: low
    training_weight: 0.5

quality_thresholds:
  min_surveys_before_analysis: 20
  min_edits_per_category: 10
  inter_annotator_agreement: 0.7
  cleanup_time_correlation: 0.6  # R² with golden similarity
```

### Testing Strategy
- **Unit Tests**: Each LangGraph node, validation functions, retrieval logic
- **Integration Tests**: Full workflow end-to-end with sample RFQs  
- **Golden Standard Tests**: Validate that golden pairs produce expected quality scores
- **Performance Tests**: Response time <30 seconds, concurrent request handling

## 📋 Success Definition
A survey generation request should:
1. Complete in <30 seconds end-to-end
2. Achieve >0.75 golden similarity score
3. Pass all methodology validation rules
4. Require <30 minutes human cleanup (vs 3-4 hours baseline)
5. Generate structured edit annotations for training

This specification provides the blueprint for Claude Code to implement the complete Ira system with clear success criteria and measurable outcomes.