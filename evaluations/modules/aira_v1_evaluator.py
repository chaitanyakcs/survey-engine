"""
AiRA v1 Enhanced SingleCall Evaluator
Implements the comprehensive AiRA v1 evaluation framework with 58 structured questions
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AiRAQuestionResult:
    """Result for individual AiRA evaluation question"""
    question_id: str
    question_text: str
    question_type: str  # yes_no, scaled, summary_yes_no, summary_scaled
    pillar: str
    score: float  # 0.0-1.0 for yes/no (0 or 1), 0.0-1.0 for scaled (1-5 normalized)
    raw_response: Any  # boolean for yes/no, 1-5 for scaled
    weight: float
    weighted_score: float

@dataclass
class AiRAPillarResult:
    """Result for individual pillar with question breakdown"""
    pillar_name: str
    pillar_score: float  # Weighted average of all questions in pillar
    pillar_weight: float  # Pillar weight in overall score
    weighted_pillar_score: float
    color_code: str  # "red", "orange", "green"
    question_results: List[AiRAQuestionResult]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

@dataclass
class AiRAEvaluationResult:
    """Complete AiRA v1 evaluation result"""
    overall_score: float  # 0.0-1.0
    overall_grade: str  # A, B, C, D, F
    overall_color: str  # "red", "orange", "green"
    pillar_results: List[AiRAPillarResult]
    summary_questions: List[AiRAQuestionResult]
    cross_pillar_insights: List[str]
    overall_recommendations: List[str]
    evaluation_metadata: Dict[str, Any]
    cost_savings: Dict[str, Any]

class AiRAV1Evaluator:
    """
    Enhanced SingleCall evaluator implementing AiRA v1 comprehensive framework
    """

    def __init__(self, llm_client=None, db_session=None):
        """Initialize with LLM client and database session"""
        self.llm_client = llm_client
        self.db_session = db_session

        # AiRA v1 pillar weights
        self.pillar_weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }

        # AiRA v1 color thresholds
        self.color_thresholds = {
            'red': 0.60,      # <60% Red
            'orange': 0.80    # 60-80% Orange, >80% Green
        }

    async def evaluate_survey(self, survey: Dict[str, Any], rfq_text: str, survey_id: str = None, rfq_id: str = None) -> AiRAEvaluationResult:
        """
        Perform comprehensive AiRA v1 evaluation in single LLM call
        """
        logger.info("🚀 Starting AiRA v1 comprehensive evaluation...")

        try:
            # Build AiRA v1 structured prompt
            prompt = await self._build_aira_v1_prompt(survey, rfq_text, survey_id, rfq_id)

            # Make single LLM call
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=6000, parent_survey_id=survey_id, parent_rfq_id=rfq_id)  # Increased for detailed response
                if response.success:
                    try:
                        result = json.loads(response.content)
                        return self._parse_aira_v1_result(result, survey_id, rfq_id)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON parsing failed: {e}")
                        # Try to extract JSON from response
                        result = self._extract_json_from_response(response.content)
                        if result:
                            return self._parse_aira_v1_result(result, survey_id, rfq_id)
                        else:
                            return await self._aira_fallback_evaluation(survey, rfq_text, survey_id, rfq_id)
                else:
                    logger.warning(f"⚠️ LLM call failed: {response.error}")
                    return await self._aira_fallback_evaluation(survey, rfq_text, survey_id, rfq_id)
            else:
                logger.warning("⚠️ No LLM client available")
                return await self._aira_fallback_evaluation(survey, rfq_text, survey_id, rfq_id)

        except Exception as e:
            logger.error(f"❌ AiRA v1 evaluation failed: {str(e)}")
            return await self._aira_fallback_evaluation(survey, rfq_text, survey_id, rfq_id)

    async def _build_aira_v1_prompt(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> str:
        """Build comprehensive AiRA v1 structured evaluation prompt"""

        # Extract questions for analysis
        try:
            from ...utils.survey_utils import extract_all_questions
            questions = extract_all_questions(survey)
        except ImportError:
            # Fallback question extraction
            questions = survey.get('questions', [])

        questions_text = "\n".join([f"{i+1}. {q.get('text', '')} (Type: {q.get('type', 'unknown')})" for i, q in enumerate(questions)])

        prompt = f"""
You are an expert survey methodologist. Perform comprehensive AiRA v1 evaluation with structured question-by-question analysis.

SURVEY TO EVALUATE:
{json.dumps(survey, indent=2)}

RFQ CONTEXT:
{rfq_text}

SURVEY QUESTIONS:
{questions_text}

AiRA v1 EVALUATION FRAMEWORK:
Answer each evaluation question individually with precise yes/no or 1-5 scale responses.

CONTENT VALIDITY (20% weight):
For each question below, respond with true/false or 1-5 scale:

CV_YN_1: Does the questionnaire cover all essential aspects of the research objectives stated in the requirement document? (true/false)
CV_YN_2: Are demographic questions appropriate and sufficient for the target audience analysis? (true/false)
CV_YN_3: Does the questionnaire include validation or consistency check questions to verify response reliability? (true/false)
CV_YN_4: Are all key stakeholder information needs addressed within the questionnaire? (true/false)
CV_YN_5: Does the questionnaire avoid including irrelevant or off-topic questions? (true/false)
CV_YN_6: Are industry-specific considerations and terminology appropriately incorporated? (true/false)

CV_SC_1: Rate the comprehensiveness of topic coverage relative to research objectives (1-5 scale)
CV_SC_2: Evaluate the alignment between questionnaire content and stated research goals (1-5 scale)
CV_SC_3: Assess the adequacy of demographic and classification questions for analysis needs (1-5 scale)
CV_SC_4: Rate the inclusion of necessary validation questions to ensure data quality (1-5 scale)
CV_SC_5: Evaluate how well the questionnaire addresses all stakeholder information requirements (1-5 scale)

METHODOLOGICAL RIGOR (25% weight):
MR_YN_1: Are questions sequenced logically from general to specific topics? (true/false)
MR_YN_2: Does the questionnaire avoid leading or biased question formulations? (true/false)
MR_YN_3: Are appropriate scale types (Likert, ranking, categorical) used consistently throughout? (true/false)
MR_YN_4: Does the questionnaire include proper screening questions to ensure qualified respondents? (true/false)
MR_YN_5: Are sensitive questions positioned appropriately (toward the end) to minimize dropout? (true/false)
MR_YN_6: Does the questionnaire follow established market research best practices for question construction? (true/false)

MR_SC_1: Rate the logical flow and sequence of questions throughout the questionnaire (1-5 scale)
MR_SC_2: Evaluate the appropriateness of scale types and response formats used (1-5 scale)
MR_SC_3: Assess the questionnaire's adherence to methodological standards for bias avoidance (1-5 scale)
MR_SC_4: Rate the effectiveness of screening and qualification questions (1-5 scale)
MR_SC_5: Evaluate the overall methodological soundness of the research design (1-5 scale)

CLARITY & COMPREHENSIBILITY (25% weight):
CC_YN_1: Are all questions written in clear, simple language appropriate for the target audience? (true/false)
CC_YN_2: Does the questionnaire avoid technical jargon or complex terminology without explanation? (true/false)
CC_YN_3: Are question instructions clear and complete for each question type? (true/false)
CC_YN_4: Does the questionnaire avoid double-barreled questions (asking multiple things at once)? (true/false)
CC_YN_5: Are all response options mutually exclusive and collectively exhaustive where appropriate? (true/false)
CC_YN_6: Is the estimated completion time reasonable for the questionnaire length? (true/false)

CC_SC_1: Rate the clarity and understandability of question wording (1-5 scale)
CC_SC_2: Evaluate the appropriateness of language level for the target audience (1-5 scale)
CC_SC_3: Assess the completeness and clarity of instructions provided to respondents (1-5 scale)
CC_SC_4: Rate the absence of ambiguous or confusing question formulations (1-5 scale)
CC_SC_5: Evaluate the overall readability and user-friendliness of the questionnaire (1-5 scale)

STRUCTURAL COHERENCE (20% weight):
SC_YN_1: Does the questionnaire have a clear introduction explaining its purpose and importance? (true/false)
SC_YN_2: Are question blocks or sections organized thematically and logically? (true/false)
SC_YN_3: Does the questionnaire include appropriate transition statements between major sections? (true/false)
SC_YN_4: Are skip patterns and routing logic implemented correctly and clearly? (true/false)
SC_YN_5: Does the questionnaire conclude with appropriate closing statements or thank you messages? (true/false)
SC_YN_6: Are open-ended and closed-ended questions balanced appropriately for the research objectives? (true/false)

SC_SC_1: Rate the overall organization and structure of the questionnaire (1-5 scale)
SC_SC_2: Evaluate the logical grouping of related questions into coherent sections (1-5 scale)
SC_SC_3: Assess the effectiveness of transitions between different topic areas (1-5 scale)
SC_SC_4: Rate the appropriateness of question type variety and distribution (1-5 scale)
SC_SC_5: Evaluate the professional presentation and formatting of the questionnaire (1-5 scale)

DEPLOYMENT READINESS (10% weight):
DR_YN_1: Is the questionnaire length appropriate for the research objectives and target audience? (true/false)
DR_YN_2: Does the questionnaire meet industry compliance and regulatory requirements? (true/false)
DR_YN_3: Are data privacy and ethical considerations properly addressed in the questionnaire design? (true/false)
DR_YN_4: Is the questionnaire technically compatible with intended distribution platforms? (true/false)
DR_YN_5: Does the questionnaire include all necessary legal disclaimers and consent statements? (true/false)
DR_YN_6: Are the resource requirements (time, cost, respondent burden) realistic for implementation? (true/false)

DR_SC_1: Rate the overall feasibility of implementing this questionnaire in the field (1-5 scale)
DR_SC_2: Evaluate the appropriateness of questionnaire length for target completion rates (1-5 scale)
DR_SC_3: Assess compliance with relevant industry standards and regulations (1-5 scale)
DR_SC_4: Rate the questionnaire's readiness for immediate deployment without modifications (1-5 scale)
DR_SC_5: Evaluate the cost-effectiveness of the questionnaire design for achieving research objectives (1-5 scale)

SUMMARY QUESTIONS:
SUM_YN_1: Would you recommend this questionnaire for deployment without major revisions? (true/false)
SUM_YN_2: Does this questionnaire meet professional market research standards? (true/false)
SUM_YN_3: Would this questionnaire likely achieve the stated research objectives? (true/false)

SUM_SC_1: Overall questionnaire quality compared to industry benchmarks (1-5 scale)
SUM_SC_2: Likelihood of achieving reliable and valid research results (1-5 scale)
SUM_SC_3: Professional confidence in recommending this questionnaire to stakeholders (1-5 scale)

RESPOND WITH JSON:
{{
    "question_responses": {{
        "CV_YN_1": true,
        "CV_YN_2": false,
        "CV_SC_1": 4,
        "CV_SC_2": 3,
        ... [all 58 questions]
    }},
    "pillar_analysis": {{
        "content_validity": {{
            "strengths": ["covers main objectives", "good alignment"],
            "weaknesses": ["missing demographics", "validation gaps"],
            "recommendations": ["add demographic section", "include validation questions"]
        }},
        ... [all 5 pillars]
    }},
    "cross_pillar_insights": [
        "Clarity issues affect content validity",
        "Strong structure supports methodology"
    ],
    "overall_recommendations": [
        "Add demographic questions",
        "Improve validation measures"
    ],
    "evaluation_metadata": {{
        "evaluation_version": "AiRA_v1",
        "timestamp": "{datetime.now().isoformat()}",
        "survey_id": "{survey_id}",
        "rfq_id": "{rfq_id}",
        "total_questions_evaluated": 58
    }}
}}

IMPORTANT: Provide specific true/false or 1-5 responses for each question ID. Be precise in your analysis.
"""

        return prompt

    def _parse_aira_v1_result(self, result: Dict[str, Any], survey_id: str, rfq_id: str) -> AiRAEvaluationResult:
        """Parse AiRA v1 evaluation result into structured format"""

        question_responses = result.get("question_responses", {})
        pillar_analysis = result.get("pillar_analysis", {})

        # Parse individual question results
        all_question_results = []
        pillar_results = []
        summary_questions = []

        # Process each pillar
        for pillar_name, pillar_weight in self.pillar_weights.items():
            pillar_questions = []

            # Get questions for this pillar (this would normally come from database)
            pillar_question_ids = self._get_pillar_question_ids(pillar_name)

            for question_id in pillar_question_ids:
                if question_id in question_responses:
                    raw_response = question_responses[question_id]

                    # Determine score based on question type
                    if question_id.endswith('_YN_'):
                        score = 1.0 if raw_response else 0.0
                        question_type = "yes_no"
                    else:
                        score = (raw_response - 1) / 4.0  # Convert 1-5 to 0.0-1.0
                        question_type = "scaled"

                    question_result = AiRAQuestionResult(
                        question_id=question_id,
                        question_text=self._get_question_text(question_id),
                        question_type=question_type,
                        pillar=pillar_name,
                        score=score,
                        raw_response=raw_response,
                        weight=1.0/len(pillar_question_ids),  # Equal weight within pillar
                        weighted_score=score * (1.0/len(pillar_question_ids))
                    )

                    pillar_questions.append(question_result)
                    all_question_results.append(question_result)

            # Calculate pillar score
            if pillar_questions:
                pillar_score = sum(q.weighted_score for q in pillar_questions)
                weighted_pillar_score = pillar_score * pillar_weight
                color_code = self._get_color_code(pillar_score)

                pillar_result = AiRAPillarResult(
                    pillar_name=pillar_name,
                    pillar_score=pillar_score,
                    pillar_weight=pillar_weight,
                    weighted_pillar_score=weighted_pillar_score,
                    color_code=color_code,
                    question_results=pillar_questions,
                    strengths=pillar_analysis.get(pillar_name, {}).get("strengths", []),
                    weaknesses=pillar_analysis.get(pillar_name, {}).get("weaknesses", []),
                    recommendations=pillar_analysis.get(pillar_name, {}).get("recommendations", [])
                )

                pillar_results.append(pillar_result)

        # Process summary questions
        summary_question_ids = ["SUM_YN_1", "SUM_YN_2", "SUM_YN_3", "SUM_SC_1", "SUM_SC_2", "SUM_SC_3"]
        for question_id in summary_question_ids:
            if question_id in question_responses:
                raw_response = question_responses[question_id]

                if question_id.startswith('SUM_YN_'):
                    score = 1.0 if raw_response else 0.0
                    question_type = "summary_yes_no"
                else:
                    score = (raw_response - 1) / 4.0
                    question_type = "summary_scaled"

                summary_question = AiRAQuestionResult(
                    question_id=question_id,
                    question_text=self._get_question_text(question_id),
                    question_type=question_type,
                    pillar="overall",
                    score=score,
                    raw_response=raw_response,
                    weight=1.0/6,  # Equal weight among summary questions
                    weighted_score=score * (1.0/6)
                )

                summary_questions.append(summary_question)

        # Calculate overall score
        overall_score = sum(pr.weighted_pillar_score for pr in pillar_results)
        overall_grade = self._calculate_grade(overall_score)
        overall_color = self._get_color_code(overall_score)

        # Calculate cost savings
        cost_savings = {
            "calls_saved": 57,  # 58 individual calls - 1 comprehensive call
            "cost_reduction_percent": 98,  # Huge savings with single call
            "estimated_cost_saved": 13.68,  # 57 calls × $0.24 per call
            "evaluation_mode": "aira_v1_single_call"
        }

        return AiRAEvaluationResult(
            overall_score=overall_score,
            overall_grade=overall_grade,
            overall_color=overall_color,
            pillar_results=pillar_results,
            summary_questions=summary_questions,
            cross_pillar_insights=result.get("cross_pillar_insights", []),
            overall_recommendations=result.get("overall_recommendations", []),
            evaluation_metadata=result.get("evaluation_metadata", {}),
            cost_savings=cost_savings
        )

    def _get_pillar_question_ids(self, pillar_name: str) -> List[str]:
        """Get question IDs for a specific pillar"""
        pillar_prefixes = {
            'content_validity': 'CV',
            'methodological_rigor': 'MR',
            'clarity_comprehensibility': 'CC',
            'structural_coherence': 'SC',
            'deployment_readiness': 'DR'
        }

        prefix = pillar_prefixes.get(pillar_name, 'CV')

        # Generate question IDs for this pillar
        question_ids = []
        for i in range(1, 7):  # 6 yes/no questions
            question_ids.append(f"{prefix}_YN_{i}")
        for i in range(1, 6):  # 5 scaled questions
            question_ids.append(f"{prefix}_SC_{i}")

        return question_ids

    def _get_question_text(self, question_id: str) -> str:
        """Get question text for a question ID (would normally come from database)"""
        # This is a simplified mapping - in practice, this would come from the database
        question_map = {
            "CV_YN_1": "Does the questionnaire cover all essential aspects of the research objectives?",
            "SUM_YN_1": "Would you recommend this questionnaire for deployment without major revisions?",
            # ... would include all 58 questions
        }
        return question_map.get(question_id, f"Question {question_id}")

    def _get_color_code(self, score: float) -> str:
        """Get color code based on AiRA v1 thresholds"""
        if score < self.color_thresholds['red']:
            return "red"
        elif score < self.color_thresholds['orange']:
            return "orange"
        else:
            return "green"

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    def _extract_json_from_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response that might have extra text"""
        # Implementation similar to original SingleCallEvaluator
        import re

        # Try to find JSON in code fences
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON block
        start_idx = response_content.find('{')
        if start_idx == -1:
            return None

        brace_count = 0
        end_idx = start_idx

        for i in range(start_idx, len(response_content)):
            char = response_content[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if brace_count == 0:
            try:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return None

    async def _aira_fallback_evaluation(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> AiRAEvaluationResult:
        """Fallback evaluation when LLM fails"""
        logger.info("🔄 Using AiRA v1 fallback evaluation")

        # Create basic fallback result
        pillar_results = []
        for pillar_name, pillar_weight in self.pillar_weights.items():
            # Generate fallback pillar result
            pillar_result = AiRAPillarResult(
                pillar_name=pillar_name,
                pillar_score=0.7,  # Default moderate score
                pillar_weight=pillar_weight,
                weighted_pillar_score=0.7 * pillar_weight,
                color_code="orange",
                question_results=[],
                strengths=["Survey structure appears reasonable"],
                weaknesses=["Detailed evaluation unavailable due to LLM failure"],
                recommendations=["Retry evaluation when LLM service is available"]
            )
            pillar_results.append(pillar_result)

        return AiRAEvaluationResult(
            overall_score=0.7,
            overall_grade="C",
            overall_color="orange",
            pillar_results=pillar_results,
            summary_questions=[],
            cross_pillar_insights=["Fallback evaluation - limited analysis available"],
            overall_recommendations=["Retry with LLM service available for comprehensive analysis"],
            evaluation_metadata={
                "evaluation_version": "AiRA_v1_fallback",
                "timestamp": datetime.now().isoformat(),
                "survey_id": survey_id,
                "rfq_id": rfq_id
            },
            cost_savings={"evaluation_mode": "fallback"}
        )