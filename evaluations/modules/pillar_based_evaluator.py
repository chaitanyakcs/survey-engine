#!/usr/bin/env python3
"""
Pillar-Based Evaluator - Weighted Scoring System
Implements the 5-pillar evaluation framework with proper weightings
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Import the pillar evaluators
from .content_validity_evaluator import ContentValidityEvaluator, ContentValidityResult
from .methodological_rigor_evaluator import MethodologicalRigorEvaluator, MethodologicalRigorResult

@dataclass
class PillarScores:
    content_validity: float
    methodological_rigor: float
    clarity_comprehensibility: float
    structural_coherence: float
    deployment_readiness: float

@dataclass
class PillarEvaluationResult:
    overall_score: float
    pillar_scores: PillarScores
    weighted_breakdown: Dict[str, float]
    detailed_results: Dict[str, Any]
    recommendations: List[str]
    evaluation_metadata: Dict[str, Any]

class PillarBasedEvaluator:
    """
    Main evaluator implementing the 5-pillar framework from Eval_Framework.xlsx
    """
    
    # Pillar weights as defined in the Excel framework
    PILLAR_WEIGHTS = {
        'content_validity': 0.20,           # 20%
        'methodological_rigor': 0.25,      # 25%
        'clarity_comprehensibility': 0.25,  # 25%
        'structural_coherence': 0.20,      # 20%
        'deployment_readiness': 0.10        # 10%
    }
    
    def __init__(self, llm_client=None):
        """Initialize with LLM client for comprehensive analysis"""
        self.llm_client = llm_client
        
        # Initialize pillar evaluators
        self.content_validity_evaluator = ContentValidityEvaluator(llm_client)
        self.methodological_rigor_evaluator = MethodologicalRigorEvaluator(llm_client)
        
    async def evaluate_survey(self, survey: Dict[str, Any], rfq_text: str) -> PillarEvaluationResult:
        """
        Perform comprehensive 5-pillar evaluation of the survey
        
        Args:
            survey: Generated survey dictionary
            rfq_text: Original RFQ text
            
        Returns:
            PillarEvaluationResult with weighted scores and detailed analysis
        """
        
        print("🔍 Starting 5-pillar evaluation...")
        
        # Evaluate each pillar
        print("📊 Evaluating Pillar 1: Content Validity (20%)")
        content_validity_result = await self.content_validity_evaluator.evaluate_content_validity(survey, rfq_text)
        
        print("🔬 Evaluating Pillar 2: Methodological Rigor (25%)")
        methodological_rigor_result = await self.methodological_rigor_evaluator.evaluate_methodological_rigor(survey, rfq_text)
        
        print("📝 Evaluating Pillar 3: Clarity & Comprehensibility (25%)")
        clarity_score = await self._evaluate_clarity_comprehensibility(survey, rfq_text)
        
        print("🏗️ Evaluating Pillar 4: Structural Coherence (20%)")
        structural_score = await self._evaluate_structural_coherence(survey, rfq_text)
        
        print("🚀 Evaluating Pillar 5: Deployment Readiness (10%)")
        deployment_score = await self._evaluate_deployment_readiness(survey, rfq_text)
        
        # Create pillar scores
        pillar_scores = PillarScores(
            content_validity=content_validity_result.score,
            methodological_rigor=methodological_rigor_result.score,
            clarity_comprehensibility=clarity_score,
            structural_coherence=structural_score,
            deployment_readiness=deployment_score
        )
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(pillar_scores)
        
        # Create weighted breakdown
        weighted_breakdown = {
            'content_validity': pillar_scores.content_validity * self.PILLAR_WEIGHTS['content_validity'],
            'methodological_rigor': pillar_scores.methodological_rigor * self.PILLAR_WEIGHTS['methodological_rigor'],
            'clarity_comprehensibility': pillar_scores.clarity_comprehensibility * self.PILLAR_WEIGHTS['clarity_comprehensibility'],
            'structural_coherence': pillar_scores.structural_coherence * self.PILLAR_WEIGHTS['structural_coherence'],
            'deployment_readiness': pillar_scores.deployment_readiness * self.PILLAR_WEIGHTS['deployment_readiness']
        }
        
        # Compile detailed results
        detailed_results = {
            'content_validity': asdict(content_validity_result),
            'methodological_rigor': asdict(methodological_rigor_result),
            'clarity_comprehensibility': await self._get_clarity_detailed_analysis(survey, rfq_text),
            'structural_coherence': await self._get_structural_detailed_analysis(survey, rfq_text),
            'deployment_readiness': await self._get_deployment_detailed_analysis(survey, rfq_text)
        }
        
        # Generate comprehensive recommendations
        recommendations = await self._generate_comprehensive_recommendations(
            pillar_scores, detailed_results, content_validity_result.recommendations, 
            methodological_rigor_result.recommendations
        )
        
        # Create evaluation metadata
        evaluation_metadata = {
            'evaluation_timestamp': datetime.now().isoformat(),
            'pillar_weights_used': self.PILLAR_WEIGHTS,
            'evaluation_version': '1.0-llm-based',
            'total_questions': len(survey.get('questions', [])),
            'declared_methodologies': survey.get('metadata', {}).get('methodology', []),
            'estimated_completion_time': survey.get('estimated_time', 0)
        }
        
        print(f"✅ Evaluation complete! Overall Score: {overall_score:.2f}")
        
        return PillarEvaluationResult(
            overall_score=overall_score,
            pillar_scores=pillar_scores,
            weighted_breakdown=weighted_breakdown,
            detailed_results=detailed_results,
            recommendations=recommendations,
            evaluation_metadata=evaluation_metadata
        )
    
    def _calculate_weighted_score(self, pillar_scores: PillarScores) -> float:
        """Calculate the weighted overall score using pillar weights"""
        return (
            pillar_scores.content_validity * self.PILLAR_WEIGHTS['content_validity'] +
            pillar_scores.methodological_rigor * self.PILLAR_WEIGHTS['methodological_rigor'] +
            pillar_scores.clarity_comprehensibility * self.PILLAR_WEIGHTS['clarity_comprehensibility'] +
            pillar_scores.structural_coherence * self.PILLAR_WEIGHTS['structural_coherence'] +
            pillar_scores.deployment_readiness * self.PILLAR_WEIGHTS['deployment_readiness']
        )
    
    async def _evaluate_clarity_comprehensibility(self, survey: Dict[str, Any], rfq_text: str) -> float:
        """Evaluate clarity and comprehensibility (Pillar 3) using LLM"""
        
        questions = survey.get("questions", [])
        questions_text = [q.get('text', '') for q in questions]
        
        prompt = f"""
        Evaluate the clarity and comprehensibility of this survey focusing on language accessibility, 
        question wording effectiveness, and absence of ambiguous or double-barreled questions.
        
        Survey Questions:
        {json.dumps(questions_text, indent=2)}
        
        Evaluate:
        1. Language Accessibility - Are questions written in clear, accessible language?
        2. Question Wording Effectiveness - Are questions well-worded and unambiguous?
        3. Absence of Double-barreled Questions - Does each question focus on one concept?
        4. Reading Level Appropriateness - Is the language appropriate for target audience?
        5. Cultural Sensitivity - Are questions culturally appropriate and inclusive?
        
        Standards:
        - Use simple, clear language
        - Avoid jargon unless necessary
        - One concept per question
        - Appropriate reading level (typically 8th grade or below)
        - Neutral, inclusive tone
        
        Respond with JSON:
        {{
            "clarity_score": <float 0.0-1.0>,
            "language_accessibility": <float 0.0-1.0>,
            "question_wording_quality": <float 0.0-1.0>,
            "ambiguity_check": <float 0.0-1.0>,
            "reading_level_appropriateness": <float 0.0-1.0>
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("clarity_score", 0.5)
            else:
                return self._basic_clarity_analysis(questions)
        except Exception as e:
            print(f"LLM analysis failed for clarity evaluation: {e}")
            return self._basic_clarity_analysis(questions)
    
    async def _evaluate_structural_coherence(self, survey: Dict[str, Any], rfq_text: str) -> float:
        """Evaluate structural coherence (Pillar 4) using LLM"""
        
        questions = survey.get("questions", [])
        
        prompt = f"""
        Evaluate the structural coherence of this survey focusing on logical flow, 
        appropriate question types, and proper use of scales and response formats.
        
        Survey Structure:
        {json.dumps([{
            'order': i+1,
            'text': q.get('text', ''),
            'type': q.get('type', ''),
            'category': q.get('category', ''),
            'options': len(q.get('options', [])) if q.get('options') else 0
        } for i, q in enumerate(questions)], indent=2)}
        
        Evaluate:
        1. Logical Flow - Do questions follow a logical progression?
        2. Question Type Appropriateness - Are question types suitable for their purpose?
        3. Scale Usage - Are rating scales used appropriately and consistently?
        4. Response Format Consistency - Are similar questions formatted consistently?
        5. Section Organization - Are questions well-organized into logical sections?
        
        Standards:
        - Screening questions first
        - Logical topic grouping
        - Consistent scale usage
        - Appropriate question types for data needed
        - Clear section divisions
        
        Respond with JSON:
        {{
            "structural_score": <float 0.0-1.0>,
            "logical_flow": <float 0.0-1.0>,
            "question_type_appropriateness": <float 0.0-1.0>,
            "scale_consistency": <float 0.0-1.0>,
            "organization_quality": <float 0.0-1.0>
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("structural_score", 0.5)
            else:
                return self._basic_structural_analysis(questions)
        except Exception as e:
            print(f"LLM analysis failed for structural evaluation: {e}")
            return self._basic_structural_analysis(questions)
    
    async def _evaluate_deployment_readiness(self, survey: Dict[str, Any], rfq_text: str) -> float:
        """Evaluate deployment readiness (Pillar 5) using LLM"""
        
        estimated_time = survey.get("estimated_time", 0)
        target_responses = survey.get("target_responses", 0)
        questions_count = len(survey.get("questions", []))
        
        prompt = f"""
        Evaluate the deployment readiness of this survey focusing on practical considerations 
        like length, completion time, and stakeholder requirements alignment.
        
        Survey Specifications:
        - Estimated Completion Time: {estimated_time} minutes
        - Target Responses: {target_responses}
        - Number of Questions: {questions_count}
        - Survey Title: {survey.get('title', 'N/A')}
        
        RFQ Context:
        {rfq_text}
        
        Evaluate:
        1. Survey Length Appropriateness - Is the survey an appropriate length?
        2. Completion Time Reasonableness - Is estimated time realistic and acceptable?
        3. Target Response Alignment - Does target sample size match research needs?
        4. Stakeholder Requirements - Does survey meet stated requirements?
        5. Practical Feasibility - Can this survey be realistically deployed?
        
        Standards:
        - Consumer surveys: typically 10-20 minutes
        - B2B surveys: can be longer (15-25 minutes)
        - Target responses should match methodology needs
        - Clear value proposition for respondents
        
        Respond with JSON:
        {{
            "deployment_score": <float 0.0-1.0>,
            "length_appropriateness": <float 0.0-1.0>,
            "time_reasonableness": <float 0.0-1.0>,
            "feasibility_assessment": <float 0.0-1.0>,
            "requirements_alignment": <float 0.0-1.0>
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("deployment_score", 0.5)
            else:
                return self._basic_deployment_analysis(survey)
        except Exception as e:
            print(f"LLM analysis failed for deployment evaluation: {e}")
            return self._basic_deployment_analysis(survey)
    
    # Helper methods for detailed analysis
    async def _get_clarity_detailed_analysis(self, survey: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """Get detailed clarity analysis"""
        return {
            "evaluation_focus": "Language accessibility and question wording effectiveness",
            "key_metrics": ["language_accessibility", "question_wording_quality", "ambiguity_check"],
            "analysis_method": "LLM-based clarity assessment"
        }
    
    async def _get_structural_detailed_analysis(self, survey: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """Get detailed structural analysis"""
        return {
            "evaluation_focus": "Logical flow and question type appropriateness",
            "key_metrics": ["logical_flow", "question_type_appropriateness", "scale_consistency"],
            "analysis_method": "LLM-based structural assessment"
        }
    
    async def _get_deployment_detailed_analysis(self, survey: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """Get detailed deployment analysis"""
        return {
            "evaluation_focus": "Practical deployment considerations",
            "key_metrics": ["length_appropriateness", "time_reasonableness", "feasibility_assessment"],
            "analysis_method": "LLM-based deployment assessment"
        }
    
    async def _generate_comprehensive_recommendations(self, pillar_scores: PillarScores, 
                                                    detailed_results: Dict[str, Any],
                                                    content_recs: List[str], 
                                                    method_recs: List[str]) -> List[str]:
        """Generate comprehensive recommendations across all pillars"""
        
        recommendations = []
        
        # Add pillar-specific recommendations
        recommendations.extend(content_recs)
        recommendations.extend(method_recs)
        
        # Add recommendations based on pillar scores
        if pillar_scores.clarity_comprehensibility < 0.7:
            recommendations.append("Improve question wording for better clarity and comprehensibility")
        
        if pillar_scores.structural_coherence < 0.7:
            recommendations.append("Enhance survey structure and question flow for better coherence")
        
        if pillar_scores.deployment_readiness < 0.7:
            recommendations.append("Adjust survey length or complexity for better deployment feasibility")
        
        # Overall recommendations based on weighted score
        overall_score = self._calculate_weighted_score(pillar_scores)
        if overall_score >= 0.8:
            recommendations.append("Excellent overall quality - survey is ready for deployment")
        elif overall_score >= 0.6:
            recommendations.append("Good quality with room for targeted improvements")
        else:
            recommendations.append("Significant improvements needed before deployment")
        
        return recommendations
    
    # Fallback methods for when LLM is not available
    def _basic_clarity_analysis(self, questions: List[Dict]) -> float:
        """Basic fallback clarity analysis"""
        if not questions:
            return 0.0
        
        # Simple heuristics for clarity
        score = 0.6
        avg_length = sum(len(q.get('text', '')) for q in questions) / len(questions)
        
        # Penalize very long questions
        if avg_length < 100:
            score += 0.2
        elif avg_length > 200:
            score -= 0.1
        
        return min(score, 1.0)
    
    def _basic_structural_analysis(self, questions: List[Dict]) -> float:
        """Basic fallback structural analysis"""
        if not questions:
            return 0.0
        
        score = 0.6
        
        # Check for question type diversity
        types = set(q.get('type', '') for q in questions)
        if len(types) > 2:
            score += 0.2
        
        # Check for categories
        categories = set(q.get('category', '') for q in questions if q.get('category'))
        if categories:
            score += 0.1
        
        return min(score, 1.0)
    
    def _basic_deployment_analysis(self, survey: Dict[str, Any]) -> float:
        """Basic fallback deployment analysis"""
        score = 0.6
        
        estimated_time = survey.get("estimated_time", 0)
        questions_count = len(survey.get("questions", []))
        
        # Check reasonable survey length
        if 10 <= estimated_time <= 25:
            score += 0.2
        
        # Check reasonable question count
        if 8 <= questions_count <= 20:
            score += 0.1
        
        # Check if target responses is set
        if survey.get("target_responses", 0) > 0:
            score += 0.1
        
        return min(score, 1.0)