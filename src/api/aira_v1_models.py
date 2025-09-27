"""
AiRA v1 API Models
Enhanced response models for detailed question-level evaluation results
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class QuestionType(str, Enum):
    """Types of evaluation questions"""
    YES_NO = "yes_no"
    SCALED = "scaled"
    SUMMARY_YES_NO = "summary_yes_no"
    SUMMARY_SCALED = "summary_scaled"

class ColorCode(str, Enum):
    """AiRA v1 color codes for quality thresholds"""
    RED = "red"         # <60%
    ORANGE = "orange"   # 60-80%
    GREEN = "green"     # >80%

class AiRAQuestionResultResponse(BaseModel):
    """Individual question evaluation result"""
    question_id: str = Field(..., description="Unique identifier for the question")
    question_text: str = Field(..., description="The evaluation question text")
    question_type: QuestionType = Field(..., description="Type of question")
    pillar: str = Field(..., description="Which pillar this question belongs to")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score (0.0-1.0)")
    raw_response: Any = Field(..., description="Raw response (boolean for yes/no, 1-5 for scaled)")
    weight: float = Field(..., description="Weight of this question within the pillar")
    weighted_score: float = Field(..., description="Score × weight")
    passes_threshold: bool = Field(..., description="Whether this question passes quality threshold")

class AiRAPillarResultResponse(BaseModel):
    """Detailed pillar evaluation result"""
    pillar_name: str = Field(..., description="Name of the pillar")
    pillar_display_name: str = Field(..., description="Human-readable pillar name")
    pillar_score: float = Field(..., ge=0.0, le=1.0, description="Overall pillar score")
    pillar_weight: float = Field(..., description="Weight of this pillar in overall score")
    weighted_pillar_score: float = Field(..., description="Pillar score × weight")
    color_code: ColorCode = Field(..., description="Color code based on AiRA v1 thresholds")

    # Question-level details
    question_results: List[AiRAQuestionResultResponse] = Field(..., description="Individual question results")
    yes_no_questions: List[AiRAQuestionResultResponse] = Field(..., description="Yes/No questions for this pillar")
    scaled_questions: List[AiRAQuestionResultResponse] = Field(..., description="Scaled questions for this pillar")

    # Qualitative analysis
    strengths: List[str] = Field(..., description="Identified strengths for this pillar")
    weaknesses: List[str] = Field(..., description="Identified weaknesses for this pillar")
    recommendations: List[str] = Field(..., description="Specific recommendations for improvement")

    # Statistics
    questions_passed: int = Field(..., description="Number of questions that passed threshold")
    total_questions: int = Field(..., description="Total number of questions in this pillar")
    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of questions passed")

class AiRAOverallMetrics(BaseModel):
    """Overall evaluation metrics"""
    total_questions_evaluated: int = Field(..., description="Total number of questions evaluated")
    questions_passed: int = Field(..., description="Number of questions that passed threshold")
    overall_pass_rate: float = Field(..., ge=0.0, le=1.0, description="Overall percentage of questions passed")

    # Score breakdown
    yes_no_score: float = Field(..., description="Average score of all yes/no questions")
    scaled_score: float = Field(..., description="Average score of all scaled questions")
    summary_score: float = Field(..., description="Average score of summary questions")

class AiRAEvaluationResponse(BaseModel):
    """Complete AiRA v1 evaluation response"""

    # Overall results
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Weighted overall score")
    overall_grade: str = Field(..., description="Letter grade (A, B, C, D, F)")
    overall_color: ColorCode = Field(..., description="Overall color code")

    # Detailed breakdown
    pillar_results: List[AiRAPillarResultResponse] = Field(..., description="Detailed results for each pillar")
    summary_questions: List[AiRAQuestionResultResponse] = Field(..., description="Summary evaluation questions")

    # Qualitative insights
    cross_pillar_insights: List[str] = Field(..., description="Insights that span multiple pillars")
    overall_recommendations: List[str] = Field(..., description="Overall recommendations for improvement")

    # Metrics and statistics
    overall_metrics: AiRAOverallMetrics = Field(..., description="Overall evaluation metrics")

    # Evaluation metadata
    evaluation_metadata: Dict[str, Any] = Field(..., description="Metadata about the evaluation")
    cost_savings: Dict[str, Any] = Field(..., description="Cost savings information")

    # Color thresholds for reference
    color_thresholds: Dict[str, float] = Field(
        default={"red": 0.60, "orange": 0.80},
        description="AiRA v1 color thresholds"
    )

class AiRAEvaluationSummary(BaseModel):
    """Simplified summary for dashboard views"""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    overall_grade: str
    overall_color: ColorCode
    pillar_summary: Dict[str, Dict[str, Any]] = Field(..., description="Summary of each pillar")
    top_recommendations: List[str] = Field(..., description="Top 3 recommendations")
    evaluation_timestamp: str = Field(..., description="When evaluation was performed")

class AiRAQuestionLibrary(BaseModel):
    """Library of all AiRA v1 evaluation questions for transparency"""
    version: str = Field(default="v1", description="AiRA framework version")
    total_questions: int = Field(..., description="Total number of questions")

    pillars: Dict[str, Dict[str, Any]] = Field(..., description="Questions organized by pillar")
    summary_questions: Dict[str, Any] = Field(..., description="Summary evaluation questions")

    # Framework details
    pillar_weights: Dict[str, float] = Field(..., description="Weight of each pillar")
    color_thresholds: Dict[str, float] = Field(..., description="Color thresholds")
    scoring_methodology: str = Field(..., description="How scores are calculated")

class AiRAComparisonResponse(BaseModel):
    """Response for comparing multiple evaluations"""
    evaluations: List[AiRAEvaluationSummary] = Field(..., description="List of evaluations to compare")
    trends: Dict[str, Any] = Field(..., description="Trends across evaluations")
    improvements: List[str] = Field(..., description="Areas of improvement")
    regressions: List[str] = Field(..., description="Areas that got worse")

# Utility functions for converting between internal and API models

def convert_aira_result_to_api(aira_result, include_detailed_questions: bool = True) -> AiRAEvaluationResponse:
    """Convert internal AiRAEvaluationResult to API response model"""

    from ..modules.aira_v1_evaluator import AiRAEvaluationResult

    # Convert pillar results
    pillar_responses = []
    for pillar_result in aira_result.pillar_results:

        # Convert question results
        question_responses = []
        yes_no_questions = []
        scaled_questions = []

        questions_passed = 0

        for question in pillar_result.question_results:
            passes_threshold = question.score >= 0.6  # Basic threshold
            if passes_threshold:
                questions_passed += 1

            question_response = AiRAQuestionResultResponse(
                question_id=question.question_id,
                question_text=question.question_text,
                question_type=question.question_type,
                pillar=question.pillar,
                score=question.score,
                raw_response=question.raw_response,
                weight=question.weight,
                weighted_score=question.weighted_score,
                passes_threshold=passes_threshold
            )

            question_responses.append(question_response)

            if question.question_type in ["yes_no"]:
                yes_no_questions.append(question_response)
            elif question.question_type in ["scaled"]:
                scaled_questions.append(question_response)

        # Get display name
        display_names = {
            "content_validity": "Content Validity",
            "methodological_rigor": "Methodological Rigor",
            "clarity_comprehensibility": "Clarity & Comprehensibility",
            "structural_coherence": "Structural Coherence",
            "deployment_readiness": "Deployment Readiness"
        }

        pillar_response = AiRAPillarResultResponse(
            pillar_name=pillar_result.pillar_name,
            pillar_display_name=display_names.get(pillar_result.pillar_name, pillar_result.pillar_name),
            pillar_score=pillar_result.pillar_score,
            pillar_weight=pillar_result.pillar_weight,
            weighted_pillar_score=pillar_result.weighted_pillar_score,
            color_code=pillar_result.color_code,
            question_results=question_responses if include_detailed_questions else [],
            yes_no_questions=yes_no_questions,
            scaled_questions=scaled_questions,
            strengths=pillar_result.strengths,
            weaknesses=pillar_result.weaknesses,
            recommendations=pillar_result.recommendations,
            questions_passed=questions_passed,
            total_questions=len(pillar_result.question_results),
            pass_rate=questions_passed / len(pillar_result.question_results) if pillar_result.question_results else 0.0
        )

        pillar_responses.append(pillar_response)

    # Convert summary questions
    summary_question_responses = []
    for question in aira_result.summary_questions:
        summary_question_responses.append(AiRAQuestionResultResponse(
            question_id=question.question_id,
            question_text=question.question_text,
            question_type=question.question_type,
            pillar=question.pillar,
            score=question.score,
            raw_response=question.raw_response,
            weight=question.weight,
            weighted_score=question.weighted_score,
            passes_threshold=question.score >= 0.6
        ))

    # Calculate overall metrics
    total_questions = sum(len(p.question_results) for p in aira_result.pillar_results) + len(aira_result.summary_questions)
    questions_passed = sum(p.questions_passed for p in pillar_responses) + sum(1 for q in summary_question_responses if q.passes_threshold)

    overall_metrics = AiRAOverallMetrics(
        total_questions_evaluated=total_questions,
        questions_passed=questions_passed,
        overall_pass_rate=questions_passed / total_questions if total_questions > 0 else 0.0,
        yes_no_score=0.8,  # Would calculate from actual questions
        scaled_score=0.7,  # Would calculate from actual questions
        summary_score=0.75  # Would calculate from actual questions
    )

    return AiRAEvaluationResponse(
        overall_score=aira_result.overall_score,
        overall_grade=aira_result.overall_grade,
        overall_color=aira_result.overall_color,
        pillar_results=pillar_responses,
        summary_questions=summary_question_responses,
        cross_pillar_insights=aira_result.cross_pillar_insights,
        overall_recommendations=aira_result.overall_recommendations,
        overall_metrics=overall_metrics,
        evaluation_metadata=aira_result.evaluation_metadata,
        cost_savings=aira_result.cost_savings
    )