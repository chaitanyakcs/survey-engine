"""
Single Call Evaluator - Cost-effective comprehensive evaluation
Performs all 5 pillars in one LLM call instead of 5 separate calls
"""

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from src.utils.json_generation_utils import parse_llm_json_response, get_json_optimized_hyperparameters, create_json_system_prompt

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
    question_annotations: List[Dict[str, Any]]
    section_annotations: List[Dict[str, Any]]
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
            
            # Evaluation prompt is now automatically logged via LLMAuditContext decorator
            
            # Make single LLM call
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=4000, parent_survey_id=survey_id, parent_rfq_id=rfq_id)
                if response.success:
                    # Try direct JSON parsing first
                    try:
                        import json
                        result = json.loads(response.content.strip())
                        logger.info(f"✅ Successfully parsed JSON directly from response")
                        logger.info(f"🔍 [SingleCallEvaluator] Parsed result keys: {list(result.keys())}")
                        logger.info(f"🔍 [SingleCallEvaluator] Has question_annotations: {'question_annotations' in result}")
                        logger.info(f"🔍 [SingleCallEvaluator] Has section_annotations: {'section_annotations' in result}")
                        if 'question_annotations' in result:
                            logger.info(f"🔍 [SingleCallEvaluator] Question annotations count: {len(result['question_annotations'])}")
                        if 'section_annotations' in result:
                            logger.info(f"🔍 [SingleCallEvaluator] Section annotations count: {len(result['section_annotations'])}")
                        return self._parse_comprehensive_result(result, survey_id, rfq_id)
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Direct JSON parsing failed: {e}")
                        # Fall back to centralized utility
                        result = parse_llm_json_response(response.content, service_name="SingleCallEvaluator")
                        
                        if result is not None:
                            logger.info(f"✅ Successfully parsed JSON using centralized utility")
                            logger.info(f"🔍 [SingleCallEvaluator] Parsed result keys: {list(result.keys())}")
                            logger.info(f"🔍 [SingleCallEvaluator] Has question_annotations: {'question_annotations' in result}")
                            logger.info(f"🔍 [SingleCallEvaluator] Has section_annotations: {'section_annotations' in result}")
                            if 'question_annotations' in result:
                                logger.info(f"🔍 [SingleCallEvaluator] Question annotations count: {len(result['question_annotations'])}")
                            if 'section_annotations' in result:
                                logger.info(f"🔍 [SingleCallEvaluator] Section annotations count: {len(result['section_annotations'])}")
                            return self._parse_comprehensive_result(result, survey_id, rfq_id)
                        else:
                            logger.warning("⚠️ Failed to extract valid JSON, using fallback")
                            logger.error(f"❌ Full response content: {response.content}")
                else:
                    logger.warning(f"⚠️ LLM response failed: {response.error}")
            
            # Fallback to basic evaluation
            logger.warning("⚠️ Single call evaluation failed, using basic fallback")
            return await self._basic_evaluation_fallback(survey, rfq_text, survey_id, rfq_id)
            
        except Exception as e:
            logger.error(f"❌ Single call evaluation failed: {str(e)}")
            return await self._basic_evaluation_fallback(survey, rfq_text, survey_id, rfq_id)
    
    async def _build_comprehensive_prompt(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> str:
        """Build comprehensive prompt for single-call evaluation"""
        
        # Extract questions for analysis
        questions = extract_all_questions(survey)
        questions_text = "\n".join([f"{i+1}. {q.get('text', '')} (Type: {q.get('type', 'unknown')})" for i, q in enumerate(questions)])
        
        # Get pillar rules from ConsolidatedRulesService (same as generation prompt uses)
        pillar_rules_context = ""
        rules_loaded = False
        rule_count = 0
        
        if self.pillar_rules_service:
            try:
                pillar_rules_context = self.pillar_rules_service.get_comprehensive_evaluation_context()
                if pillar_rules_context and pillar_rules_context.strip():
                    rules_loaded = True
                    # Count rules by counting lines that start with numbered items or priority indicators
                    rule_count = sum(1 for line in pillar_rules_context.split('\n') 
                                   if line.strip().startswith(('🔴', '🟡', '🔵')) or 
                                   (line.strip() and line.strip()[0].isdigit() and '.' in line[:3]))
                    logger.info(f"✅ [SingleCallEvaluator] Loaded pillar rules from ConsolidatedRulesService ({rule_count} rules detected)")
                else:
                    logger.warning("⚠️ [SingleCallEvaluator] ConsolidatedRulesService returned empty context, using fallback")
            except Exception as e:
                logger.warning(f"⚠️ [SingleCallEvaluator] Failed to load pillar rules from ConsolidatedRulesService: {e}, using fallback")
        
        if not rules_loaded:
            logger.info("ℹ️ [SingleCallEvaluator] Using fallback pillar descriptions (ConsolidatedRulesService unavailable)")
        
        # Build pillar section - use dynamic rules if available, otherwise fallback to hardcoded
        if rules_loaded:
            pillars_section = f"""
EVALUATION PILLARS (with weights):
1. CONTENT VALIDITY (20%) - Does the survey address research objectives?
2. METHODOLOGICAL RIGOR (25%) - Is the methodology sound and unbiased?
3. CLARITY & COMPREHENSIBILITY (25%) - Are questions clear and understandable?
4. STRUCTURAL COHERENCE (20%) - Is the structure logical and well-organized?
5. DEPLOYMENT READINESS (10%) - Is the survey ready to deploy?

PILLAR EVALUATION RULES:
{pillar_rules_context}
"""
        else:
            pillars_section = """
EVALUATION PILLARS (with weights):
1. CONTENT VALIDITY (20%) - Does the survey address research objectives?
2. METHODOLOGICAL RIGOR (25%) - Is the methodology sound and unbiased?
3. CLARITY & COMPREHENSIBILITY (25%) - Are questions clear and understandable?
4. STRUCTURAL COHERENCE (20%) - Is the structure logical and well-organized?
5. DEPLOYMENT READINESS (10%) - Is the survey ready to deploy?
"""
        
        prompt = f"""
You are an expert survey methodologist with 15+ years of experience. Perform a comprehensive 5-pillar evaluation of this survey in one analysis.

SURVEY TO EVALUATE:
{json.dumps(survey, indent=2)}

RFQ CONTEXT:
{rfq_text}

SURVEY QUESTIONS:
{questions_text}
{pillars_section}
EVALUATION PROCESS:
- Score each pillar 0.0-1.0 (1.0 = perfect adherence)
- Provide specific examples of compliance/non-compliance
- Calculate weighted overall score
- Generate actionable recommendations
- Score each individual question and section on all 5 pillars (1-5 scale)
- Provide confidence scores for AI-generated annotations (0.0-1.0)

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
    "question_annotations": [
        {{
            "question_id": "q1",
            "question_text": "What is your age group?",
            "content_validity": 4,
            "methodological_rigor": 5,
            "respondent_experience": 4,
            "analytical_value": 3,
            "business_impact": 4,
            "quality": 4,
            "relevant": 5,
            "ai_confidence": 0.85,
            "comment": "Clear demographic question with good response options"
        }},
        {{
            "question_id": "q2",
            "question_text": "How satisfied are you with our product?",
            "content_validity": 5,
            "methodological_rigor": 4,
            "respondent_experience": 4,
            "analytical_value": 5,
            "business_impact": 5,
            "quality": 4,
            "relevant": 5,
            "ai_confidence": 0.90,
            "comment": "Direct satisfaction question, well-structured"
        }}
    ],
    "section_annotations": [
        {{
            "section_id": 1,
            "section_title": "Demographics",
            "content_validity": 4,
            "methodological_rigor": 5,
            "respondent_experience": 4,
            "analytical_value": 4,
            "business_impact": 4,
            "quality": 4,
            "relevant": 5,
            "ai_confidence": 0.88,
            "comment": "Essential demographic section with appropriate questions"
        }},
        {{
            "section_id": 2,
            "section_title": "Product Satisfaction",
            "content_validity": 5,
            "methodological_rigor": 4,
            "respondent_experience": 4,
            "analytical_value": 5,
            "business_impact": 5,
            "quality": 4,
            "relevant": 5,
            "ai_confidence": 0.92,
            "comment": "Core satisfaction questions align well with research objectives"
        }}
    ],
    "evaluation_metadata": {{
        "evaluation_mode": "single_call",
        "timestamp": "{datetime.now().isoformat()}",
        "survey_id": "{survey_id}",
        "rfq_id": "{rfq_id}",
        "questions_analyzed": {len(questions)},
        "sections_analyzed": {len(survey.get('sections', []))},
        "ai_annotations_generated": true,
        "total_annotations": {len(questions) + len(survey.get('sections', []))},
        "rfq_text_length": {len(rfq_text)},
        "pillar_rules_loaded": {str(rules_loaded).lower()},
        "pillar_rules_count": {rule_count}
    }}
}}
"""
        
        return prompt

    def _extract_json_from_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response that may contain extra text"""
        import re

        logger.debug(f"🔍 Extracting JSON from response of length: {len(response_content)}")
        
        # Try to find JSON block between code fences
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_content, re.DOTALL)
        if json_match:
            logger.debug(f"🔍 Found JSON match in code fences, length: {len(json_match.group(1))}")
            try:
                result = json.loads(json_match.group(1))
                logger.debug(f"✅ Successfully parsed JSON from code fences")
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"❌ JSON parsing failed from code fences: {e}")
                pass

        # Try to find JSON block starting with {
        start_idx = response_content.find('{')
        if start_idx == -1:
            logger.debug("🔍 No opening brace found in response")
            return None

        logger.debug(f"🔍 Found opening brace at index: {start_idx}")

        # Find balanced braces
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

        logger.debug(f"🔍 Found closing brace at index: {end_idx}, balanced: {brace_count == 0}")

        if brace_count == 0:
            try:
                json_str = response_content[start_idx:end_idx]
                logger.debug(f"🔍 Extracted JSON string of length: {len(json_str)}")
                result = json.loads(json_str)
                logger.debug(f"✅ Successfully parsed JSON from balanced braces")
                return result
            except json.JSONDecodeError as e:
                logger.debug(f"❌ JSON parsing failed from balanced braces: {e}")
                pass

        logger.debug("🔍 No valid JSON found in response")
        return None

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
            question_annotations=result.get("question_annotations", []),
            section_annotations=result.get("section_annotations", []),
            evaluation_metadata=result.get("evaluation_metadata", {}),
            cost_savings=cost_savings
        )
    
    async def _basic_evaluation_fallback(self, survey: Dict[str, Any], rfq_text: str, survey_id: str, rfq_id: str) -> SingleCallEvaluationResult:
        """Basic evaluation fallback when LLM fails"""
        
        logger.warning("🔄 Using basic evaluation fallback - NO AI ANNOTATIONS WILL BE GENERATED")
        
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
            question_annotations=[],  # No AI annotations in fallback mode
            section_annotations=[],  # No AI annotations in fallback mode
            evaluation_metadata={
                "evaluation_mode": "basic_fallback",
                "timestamp": datetime.now().isoformat(),
                "survey_id": survey_id,
                "rfq_id": rfq_id,
                "questions_analyzed": len(questions),
                "sections_analyzed": len(survey.get('sections', [])),
                "ai_annotations_generated": False,
                "total_annotations": 0
            },
            cost_savings={
                "calls_saved": 0,
                "cost_reduction_percent": 0,
                "estimated_cost_saved": 0,
                "evaluation_mode": "basic_fallback"
            }
        )
    

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
