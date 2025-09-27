"""
AiRA v1 Evaluation Rule Schema
Defines the structure for storing AiRA v1 evaluation questions in SurveyRule.rule_content
"""

from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum

class QuestionType(str, Enum):
    """Types of evaluation questions"""
    YES_NO = "yes_no"
    SCALED = "scaled"
    SUMMARY_YES_NO = "summary_yes_no"
    SUMMARY_SCALED = "summary_scaled"

class PillarName(str, Enum):
    """5-Pillar evaluation categories"""
    CONTENT_VALIDITY = "content_validity"
    METHODOLOGICAL_RIGOR = "methodological_rigor"
    CLARITY_COMPREHENSIBILITY = "clarity_comprehensibility"
    STRUCTURAL_COHERENCE = "structural_coherence"
    DEPLOYMENT_READINESS = "deployment_readiness"

class AiRAEvaluationQuestion(BaseModel):
    """Structure for individual AiRA v1 evaluation question"""
    question_id: str = Field(..., description="Unique identifier for the question")
    question_type: QuestionType = Field(..., description="Type of question (yes/no or scaled)")
    pillar: PillarName = Field(..., description="Which pillar this question belongs to")
    question_text: str = Field(..., description="The evaluation question text")
    evaluation_criteria: str = Field(..., description="Specific criteria for evaluation")
    scoring_weight: float = Field(..., description="Weight of this question within the pillar")
    response_format: Literal["boolean", "1-5_scale"] = Field(..., description="Expected response format")
    llm_evaluation_prompt: str = Field(..., description="Specific prompt for LLM to evaluate this criteria")

class AiRAPillarWeights(BaseModel):
    """AiRA v1 pillar weights"""
    content_validity: float = 0.20
    methodological_rigor: float = 0.25
    clarity_comprehensibility: float = 0.25
    structural_coherence: float = 0.20
    deployment_readiness: float = 0.10

class AiRAColorThresholds(BaseModel):
    """AiRA v1 color-coded quality thresholds"""
    red_threshold: float = 0.60  # <60% Red
    orange_threshold: float = 0.80  # 60-80% Orange, >80% Green

# AiRA v1 Evaluation Questions Data
AIRA_V1_QUESTIONS = [
    # Content Validity (6 Yes/No questions)
    {
        "question_id": "cv_yn_1",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire cover all essential aspects of the research objectives stated in the requirement document?",
        "evaluation_criteria": "Check if all research objectives from RFQ are addressed by survey questions",
        "scoring_weight": 0.167,  # 1/6 of pillar
        "response_format": "boolean",
        "llm_evaluation_prompt": "Analyze if the survey questions comprehensively address ALL research objectives mentioned in the RFQ. Return true only if all objectives are covered."
    },
    {
        "question_id": "cv_yn_2",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are demographic questions appropriate and sufficient for the target audience analysis?",
        "evaluation_criteria": "Evaluate demographic question coverage for target audience analysis needs",
        "scoring_weight": 0.167,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if demographic questions are appropriate for the target audience and research objectives. Consider age, gender, income, geography, etc. as relevant."
    },
    {
        "question_id": "cv_yn_3",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire include validation or consistency check questions to verify response reliability?",
        "evaluation_criteria": "Check for validation questions, attention checks, or consistency verification",
        "scoring_weight": 0.167,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Look for validation questions, attention checks, or questions that verify response consistency and reliability."
    },
    {
        "question_id": "cv_yn_4",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are all key stakeholder information needs addressed within the questionnaire?",
        "evaluation_criteria": "Verify that questionnaire addresses information needs of all key stakeholders",
        "scoring_weight": 0.167,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Assess if the survey addresses information needs that would be important to key stakeholders mentioned in the RFQ."
    },
    {
        "question_id": "cv_yn_5",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Does the questionnaire avoid including irrelevant or off-topic questions?",
        "evaluation_criteria": "Check for questions that don't align with research objectives",
        "scoring_weight": 0.167,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Identify any questions that seem irrelevant or off-topic relative to the stated research objectives in the RFQ."
    },
    {
        "question_id": "cv_yn_6",
        "question_type": "yes_no",
        "pillar": "content_validity",
        "question_text": "Are industry-specific considerations and terminology appropriately incorporated?",
        "evaluation_criteria": "Evaluate use of appropriate industry terminology and considerations",
        "scoring_weight": 0.167,
        "response_format": "boolean",
        "llm_evaluation_prompt": "Check if the survey appropriately uses industry-specific terminology and addresses industry-specific considerations relevant to the research context."
    },

    # Content Validity (5 Scaled questions)
    {
        "question_id": "cv_sc_1",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Rate the comprehensiveness of topic coverage relative to research objectives",
        "evaluation_criteria": "Assess how comprehensively the survey covers the research topics",
        "scoring_weight": 0.20,  # 1/5 of scaled questions
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how comprehensively the survey covers all aspects of the research objectives. 1=very poor coverage, 5=excellent comprehensive coverage."
    },
    {
        "question_id": "cv_sc_2",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Evaluate the alignment between questionnaire content and stated research goals",
        "evaluation_criteria": "Assess alignment between survey content and research goals",
        "scoring_weight": 0.20,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well the questionnaire content aligns with the stated research goals. 1=very poor alignment, 5=excellent alignment."
    },
    {
        "question_id": "cv_sc_3",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Assess the adequacy of demographic and classification questions for analysis needs",
        "evaluation_criteria": "Evaluate if demographic questions support required analysis",
        "scoring_weight": 0.20,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the adequacy of demographic and classification questions for supporting the analysis needs. 1=inadequate, 5=excellent coverage."
    },
    {
        "question_id": "cv_sc_4",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Rate the inclusion of necessary validation questions to ensure data quality",
        "evaluation_criteria": "Assess presence and quality of validation questions",
        "scoring_weight": 0.20,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 the inclusion of validation questions and data quality checks. 1=no validation, 5=excellent validation measures."
    },
    {
        "question_id": "cv_sc_5",
        "question_type": "scaled",
        "pillar": "content_validity",
        "question_text": "Evaluate how well the questionnaire addresses all stakeholder information requirements",
        "evaluation_criteria": "Assess coverage of all stakeholder information needs",
        "scoring_weight": 0.20,
        "response_format": "1-5_scale",
        "llm_evaluation_prompt": "Rate 1-5 how well the questionnaire addresses information requirements of all stakeholders. 1=poor coverage, 5=excellent coverage."
    }

    # Note: This is a sample of the first pillar. The full implementation would include:
    # - Methodological Rigor: 6 Yes/No + 5 Scaled = 11 questions
    # - Clarity & Comprehensibility: 6 Yes/No + 5 Scaled = 11 questions
    # - Structural Coherence: 6 Yes/No + 5 Scaled = 11 questions
    # - Deployment Readiness: 6 Yes/No + 5 Scaled = 11 questions
    # - Summary Questions: 3 Yes/No + 3 Scaled = 6 questions
    # Total: 58 questions
]

def get_aira_v1_rule_content(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert question data to SurveyRule.rule_content format"""
    return {
        "aira_version": "v1",
        "question": AiRAEvaluationQuestion(**question_data).dict(),
        "pillar_weights": AiRAPillarWeights().dict(),
        "color_thresholds": AiRAColorThresholds().dict()
    }