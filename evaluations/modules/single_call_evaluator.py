"""
Single Call Evaluator - Cost-effective comprehensive evaluation
Performs all 5 pillars in one LLM call instead of 5 separate calls
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SingleCallEvaluationResult:
    """Result from single comprehensive evaluation call"""
    pillar_scores: Dict[str, float]
    weighted_score: float
    overall_grade: str
    detailed_analysis: Dict[str, Any]
    cross_pillar_insights: List[str]
    overall_recommendations: List[str]
    evaluation_metadata: Dict[str, Any]
    cost_savings: Dict[str, Any]  # Track cost savings vs multi-call

class SingleCallEvaluator:
    """
    Cost-effective evaluator that performs comprehensive 5-pillar evaluation in one LLM call
    Reduces costs by 80% while maintaining quality through holistic analysis
    """
    
    def __init__(self, llm_client=None, db_session=None):
        """Initialize with LLM client and database session"""
        self.llm_client = llm_client
        self.db_session = db_session
        
        # Initialize pillar rules service
        try:
            from ..consolidated_rules_integration import ConsolidatedRulesService
            self.pillar_rules_service = ConsolidatedRulesService(db_session)
        except ImportError:
            self.pillar_rules_service = None
    
    async def evaluate_survey(self, survey: Dict[str, Any], rfq_text: str, survey_id: str = None, rfq_id: str = None) -> SingleCallEvaluationResult:
        """
        Perform comprehensive 5-pillar evaluation in single LLM call
        
        Args:
            survey: Generated survey dictionary
            rfq_text: Original RFQ text
            survey_id: Survey identifier for audit
            rfq_id: RFQ identifier for audit
            
        Returns:
            SingleCallEvaluationResult with comprehensive analysis
        """
        
        logger.info("🚀 Starting single-call comprehensive evaluation...")
        
        try:
            # Build comprehensive prompt
            prompt = await self._build_comprehensive_prompt(survey, rfq_text, survey_id, rfq_id)
            
            # Store prompt in audit system
            await self._store_evaluation_prompt_audit(
                prompt=prompt,
                prompt_type="comprehensive_evaluation",
                evaluation_context={
                    "survey_id": survey_id,
                    "rfq_id": rfq_id,
                    "rfq_text_length": len(rfq_text),
                    "survey_questions_count": len(extract_all_questions(survey)),
                    "evaluation_mode": "single_call"
                }
            )
            
            # Make single LLM call
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=4000)
                if response.success:
                    result = json.loads(response.content)
                    return self._parse_comprehensive_result(result, survey_id, rfq_id)
            
            # Fallback to basic evaluation
            logger.warning("⚠️ Single call evaluation failed, using basic fallback")
            return self._basic_evaluation_fallback(survey, rfq_text, survey_id, rfq_id)
            
        except Exception as e:
            logger.error(f"❌ Single call evaluation failed: {str(e)}")
            return self._basic_evaluation_fallback(survey, rfq_text, survey_id, rfq_id)
    
    async def _build_comprehensive_prompt(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> str:
        """Build comprehensive prompt for single-call evaluation"""
        
        # Get pillar rules context
        pillar_rules_context = ""
        if self.pillar_rules_service:
            try:
                pillar_rules_context = self.pillar_rules_service.get_pillar_rules_context()
            except Exception as e:
                logger.warning(f"⚠️ Failed to load pillar rules: {e}")
        
        # Extract questions for analysis
        questions = extract_all_questions(survey)
        questions_text = "\n".join([f"{i+1}. {q.get('text', '')} (Type: {q.get('type', 'unknown')})" for i, q in enumerate(questions)])
        
        prompt = f"""
You are an expert survey methodologist with 15+ years of experience. Perform a comprehensive 5-pillar evaluation of this survey in one analysis.

SURVEY TO EVALUATE:
{json.dumps(survey, indent=2)}

RFQ CONTEXT:
{rfq_text}

SURVEY QUESTIONS:
{questions_text}

PILLAR RULES CONTEXT:
{pillar_rules_context}

EVALUATION FRAMEWORK:
Evaluate all 5 pillars and provide scores (0.0-1.0) and detailed analysis:

1. CONTENT VALIDITY (20% weight) - Does the survey address the research objectives?
   - Objective coverage and alignment with RFQ
   - Research goal fulfillment
   - Question relevance to stated objectives
   - Coverage gaps and over-coverage areas

2. METHODOLOGICAL RIGOR (25% weight) - Is the methodology sound?
   - Bias detection and prevention (leading questions, social desirability, etc.)
   - Question sequencing and logical flow
   - Methodology compliance (screening, warm-up, sensitive questions placement)
   - Statistical power considerations and sample size alignment

3. CLARITY & COMPREHENSIBILITY (25% weight) - Are questions clear and understandable?
   - Language clarity and simplicity
   - Question wording quality and precision
   - Response format clarity and consistency
   - Accessibility considerations and readability

4. STRUCTURAL COHERENCE (20% weight) - Is the structure logical and well-organized?
   - Logical flow and progression from general to specific
   - Question type appropriateness for data needed
   - Scale consistency and response format standardization
   - Section organization and topic grouping

5. DEPLOYMENT READINESS (10% weight) - Is the survey ready to deploy?
   - Technical completeness and functionality
   - User experience quality and navigation
   - Implementation readiness and technical requirements
   - Quality assurance and testing considerations

ANALYSIS REQUIREMENTS:
- Provide specific scores (0.0-1.0) for each pillar
- Calculate weighted overall score
- Identify specific strengths and weaknesses per pillar
- Provide actionable recommendations for improvement
- Highlight cross-pillar insights and interdependencies
- Consider the target audience and research context

RESPOND WITH JSON:
{{
    "pillar_scores": {{
        "content_validity": 0.85,
        "methodological_rigor": 0.78,
        "clarity_comprehensibility": 0.82,
        "structural_coherence": 0.80,
        "deployment_readiness": 0.88
    }},
    "weighted_score": 0.82,
    "overall_grade": "B+",
    "detailed_analysis": {{
        "content_validity": {{
            "score": 0.85,
            "strengths": ["covers all research objectives", "questions align with RFQ"],
            "weaknesses": ["missing demographic questions", "some objectives under-covered"],
            "recommendations": ["add demographic section", "expand objective coverage"],
            "specific_issues": ["Q3 doesn't address objective X", "missing questions about Y"]
        }},
        "methodological_rigor": {{
            "score": 0.78,
            "strengths": ["good question sequencing", "appropriate question types"],
            "weaknesses": ["potential leading questions", "inconsistent scales"],
            "recommendations": ["revise leading questions", "standardize rating scales"],
            "specific_issues": ["Q5 is leading", "Q8 uses different scale than Q12"]
        }},
        "clarity_comprehensibility": {{
            "score": 0.82,
            "strengths": ["clear language", "good question structure"],
            "weaknesses": ["some complex wording", "unclear response options"],
            "recommendations": ["simplify complex questions", "clarify response options"],
            "specific_issues": ["Q7 has complex terminology", "Q10 response options unclear"]
        }},
        "structural_coherence": {{
            "score": 0.80,
            "strengths": ["logical flow", "good section organization"],
            "weaknesses": ["inconsistent question types", "poor scale usage"],
            "recommendations": ["standardize question types", "improve scale consistency"],
            "specific_issues": ["Q4-6 use different formats", "rating scales inconsistent"]
        }},
        "deployment_readiness": {{
            "score": 0.88,
            "strengths": ["complete survey", "good UX"],
            "weaknesses": ["missing instructions", "no progress indicators"],
            "recommendations": ["add survey instructions", "include progress bar"],
            "specific_issues": ["no welcome message", "missing completion instructions"]
        }}
    }},
    "cross_pillar_insights": [
        "Clarity issues in Q3 affect content validity score",
        "Structural coherence problems impact methodological rigor",
        "Overall survey is well-designed but needs minor improvements"
    ],
    "overall_recommendations": [
        "Add demographic questions for better segmentation",
        "Standardize rating scales across all questions",
        "Include survey instructions and progress indicators"
    ],
    "evaluation_metadata": {{
        "evaluation_mode": "single_call",
        "timestamp": "{datetime.now().isoformat()}",
        "survey_id": "{survey_id}",
        "rfq_id": "{rfq_id}",
        "questions_analyzed": {len(questions)},
        "rfq_text_length": {len(rfq_text)}
    }}
}}
"""
        
        return prompt
    
    def _parse_comprehensive_result(self, result: Dict[str, Any], survey_id: str, rfq_id: str) -> SingleCallEvaluationResult:
        """Parse comprehensive evaluation result"""
        
        # Calculate cost savings
        cost_savings = {
            "calls_saved": 4,  # 5 calls - 1 call = 4 calls saved
            "cost_reduction_percent": 80,  # 4/5 = 80%
            "estimated_cost_saved": 0.96,  # 4 calls × $0.24 per call
            "evaluation_mode": "single_call"
        }
        
        return SingleCallEvaluationResult(
            pillar_scores=result.get("pillar_scores", {}),
            weighted_score=result.get("weighted_score", 0.5),
            overall_grade=result.get("overall_grade", "C"),
            detailed_analysis=result.get("detailed_analysis", {}),
            cross_pillar_insights=result.get("cross_pillar_insights", []),
            overall_recommendations=result.get("overall_recommendations", []),
            evaluation_metadata=result.get("evaluation_metadata", {}),
            cost_savings=cost_savings
        )
    
    async def _basic_evaluation_fallback(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> SingleCallEvaluationResult:
        """Basic evaluation fallback when LLM fails"""
        
        logger.info("🔄 Using basic evaluation fallback")
        
        # Simple heuristic-based evaluation
        questions = extract_all_questions(survey)
        
        # Basic scoring based on simple heuristics
        content_validity = min(0.8, len(questions) / 10)  # More questions = better coverage
        methodological_rigor = 0.7  # Default moderate score
        clarity = 0.75  # Default moderate score
        structure = 0.8  # Default good score
        deployment = 0.9  # Default good score
        
        # Calculate weighted score
        weighted_score = (
            content_validity * 0.20 +
            methodological_rigor * 0.25 +
            clarity * 0.25 +
            structure * 0.20 +
            deployment * 0.10
        )
        
        # Determine grade
        if weighted_score >= 0.9:
            grade = "A"
        elif weighted_score >= 0.8:
            grade = "B"
        elif weighted_score >= 0.7:
            grade = "C"
        elif weighted_score >= 0.6:
            grade = "D"
        else:
            grade = "F"
        
        return SingleCallEvaluationResult(
            pillar_scores={
                "content_validity": content_validity,
                "methodological_rigor": methodological_rigor,
                "clarity_comprehensibility": clarity,
                "structural_coherence": structure,
                "deployment_readiness": deployment
            },
            weighted_score=weighted_score,
            overall_grade=grade,
            detailed_analysis={
                "content_validity": {
                    "score": content_validity,
                    "strengths": ["Basic content coverage"],
                    "weaknesses": ["Limited analysis depth"],
                    "recommendations": ["Use advanced evaluation for detailed analysis"]
                },
                "methodological_rigor": {
                    "score": methodological_rigor,
                    "strengths": ["Basic methodology"],
                    "weaknesses": ["Limited rigor analysis"],
                    "recommendations": ["Use advanced evaluation for detailed analysis"]
                },
                "clarity_comprehensibility": {
                    "score": clarity,
                    "strengths": ["Basic clarity"],
                    "weaknesses": ["Limited clarity analysis"],
                    "recommendations": ["Use advanced evaluation for detailed analysis"]
                },
                "structural_coherence": {
                    "score": structure,
                    "strengths": ["Basic structure"],
                    "weaknesses": ["Limited structural analysis"],
                    "recommendations": ["Use advanced evaluation for detailed analysis"]
                },
                "deployment_readiness": {
                    "score": deployment,
                    "strengths": ["Basic readiness"],
                    "weaknesses": ["Limited deployment analysis"],
                    "recommendations": ["Use advanced evaluation for detailed analysis"]
                }
            },
            cross_pillar_insights=["Basic evaluation used - limited cross-pillar analysis available"],
            overall_recommendations=["Use advanced evaluation mode for comprehensive analysis"],
            evaluation_metadata={
                "evaluation_mode": "basic_fallback",
                "timestamp": datetime.now().isoformat(),
                "survey_id": survey_id,
                "rfq_id": rfq_id,
                "questions_analyzed": len(questions)
            },
            cost_savings={
                "calls_saved": 0,
                "cost_reduction_percent": 0,
                "estimated_cost_saved": 0,
                "evaluation_mode": "basic_fallback"
            }
        )
    
    async def _store_evaluation_prompt_audit(self, prompt: str, prompt_type: str, evaluation_context: Dict[str, Any]) -> None:
        """Store evaluation prompt in audit table"""
        try:
            if not self.db_session:
                logger.warning("⚠️ No database session available for evaluation prompt audit")
                return
            
            # Import here to avoid circular imports
            from src.services.generation_service import GenerationService
            
            # Get survey_id and rfq_id from context if available
            survey_id = evaluation_context.get('survey_id', 'unknown')
            rfq_id = evaluation_context.get('rfq_id')
            
            await GenerationService.store_evaluation_prompt_audit(
                db_session=self.db_session,
                survey_id=survey_id,
                rfq_id=rfq_id,
                system_prompt=prompt,
                prompt_type=prompt_type,
                model_version="gpt-4o-mini",  # Default model for evaluations
                evaluation_context=evaluation_context
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to store evaluation prompt audit: {str(e)}")
            # Don't raise exception to avoid breaking evaluation flow

def extract_all_questions(survey: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all questions from survey structure"""
    questions = []
    
    # Handle both legacy and new survey formats
    if 'sections' in survey:
        for section in survey.get('sections', []):
            questions.extend(section.get('questions', []))
    elif 'questions' in survey:
        questions.extend(survey.get('questions', []))
    
    return questions
