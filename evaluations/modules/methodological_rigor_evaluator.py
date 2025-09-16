#!/usr/bin/env python3
"""
Methodological Rigor Evaluator - LLM-based Analysis
Evaluates adherence to market research best practices, question sequencing, bias avoidance
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import extract_all_questions

@dataclass
class MethodologicalRigorResult:
    score: float  # 0.0 - 1.0
    question_sequencing: float
    bias_detection: float
    sampling_considerations: float
    methodology_implementation: float
    detailed_analysis: Dict[str, Any]
    bias_indicators: List[str]
    recommendations: List[str]

class MethodologicalRigorEvaluator:
    def __init__(self, llm_client=None, db_session=None):
        """Initialize with LLM client and database session for analysis"""
        self.llm_client = llm_client
        self.db_session = db_session
        
        # Initialize pillar rules service
        try:
            from ..consolidated_rules_integration import ConsolidatedRulesService
            self.pillar_rules_service = ConsolidatedRulesService(db_session)
        except ImportError:
            self.pillar_rules_service = None
        
    async def evaluate_methodological_rigor(self, survey: Dict[str, Any], rfq_text: str) -> MethodologicalRigorResult:
        """
        Evaluate methodological rigor using LLM-based analysis
        
        Args:
            survey: Generated survey dictionary
            rfq_text: Original RFQ text
            
        Returns:
            MethodologicalRigorResult with comprehensive analysis
        """
        
        questions = extract_all_questions(survey)
        methodologies = survey.get("metadata", {}).get("methodology", [])
        
        # Perform LLM-based analysis
        question_sequencing = await self._analyze_question_sequencing(questions)
        bias_detection = await self._analyze_bias_patterns(questions)
        sampling_considerations = await self._analyze_sampling_adequacy(survey, rfq_text)
        methodology_implementation = await self._analyze_methodology_implementation(questions, methodologies, rfq_text)
        
        # Calculate weighted overall score
        overall_score = (
            question_sequencing * 0.3 +
            bias_detection * 0.3 +
            sampling_considerations * 0.2 +
            methodology_implementation * 0.2
        )
        
        # Generate detailed analysis and bias indicators
        detailed_analysis = await self._generate_detailed_analysis(
            questions, methodologies, question_sequencing, bias_detection, 
            sampling_considerations, methodology_implementation
        )
        
        bias_indicators = await self._identify_bias_indicators(questions)
        recommendations = await self._generate_recommendations(detailed_analysis, overall_score, bias_indicators)
        
        return MethodologicalRigorResult(
            score=overall_score,
            question_sequencing=question_sequencing,
            bias_detection=bias_detection,
            sampling_considerations=sampling_considerations,
            methodology_implementation=methodology_implementation,
            detailed_analysis=detailed_analysis,
            bias_indicators=bias_indicators,
            recommendations=recommendations
        )
    
    async def _analyze_question_sequencing(self, questions: List[Dict]) -> float:
        """Analyze question flow and sequencing using LLM"""
        
        questions_text = []
        for i, q in enumerate(questions):
            questions_text.append(f"{i+1}. {q.get('text', '')} (Type: {q.get('type', 'unknown')})")
        
        prompt = f"""
        Analyze the logical flow and sequencing of these survey questions for methodological rigor.
        
        Questions in order:
        {chr(10).join(questions_text)}
        
        Evaluate:
        1. Is there logical progression from general to specific questions?
        2. Are sensitive/personal questions appropriately placed (later in survey)?
        3. Do earlier questions avoid biasing later responses?
        4. Is there proper warm-up with easier questions first?
        5. Are related questions grouped appropriately?
        6. Does the flow follow market research best practices?
        
        Consider standard survey methodology principles:
        - Screening questions first
        - Build rapport with easier questions
        - Sensitive questions toward end
        - Avoid question order bias
        - Logical topic grouping
        
        Respond with JSON:
        {{
            "sequencing_score": <float 0.0-1.0>,
            "flow_analysis": "<analysis of question flow quality>",
            "sequencing_issues": [<list of specific sequencing problems>],
            "best_practices_adherence": <float 0.0-1.0>
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("sequencing_score", 0.5)
            else:
                return self._basic_question_sequencing_analysis(questions)
        except Exception as e:
            print(f"LLM analysis failed for question sequencing: {e}")
            return self._basic_question_sequencing_analysis(questions)
    
    async def _analyze_bias_patterns(self, questions: List[Dict]) -> float:
        """Detect various types of bias in questions using LLM with pillar rules"""
        
        questions_text = [q.get('text', '') for q in questions]
        
        # Get pillar-specific rules context
        rules_context = ""
        if self.pillar_rules_service:
            rules_context = self.pillar_rules_service.create_pillar_rule_prompt_context("methodological_rigor")
        
        prompt = f"""
        {rules_context}
        
        Analyze these survey questions for various types of bias based on the Methodological Rigor rules specified above.
        
        Questions:
        {json.dumps(questions_text, indent=2)}
        
        Check specifically for bias types that violate the rules above:
        1. Leading questions (suggesting desired answers)
        2. Loaded questions (emotional language or assumptions)
        3. Double-barreled questions (asking multiple things at once)
        4. Acquiescence bias (yes-saying tendency)
        5. Social desirability bias (pressure to answer acceptably)
        6. Confirmation bias (questions that confirm assumptions)
        7. Response order bias (answer option ordering issues)
        8. Framing effects (how questions are presented)
        
        For each rule listed above, evaluate compliance and provide specific examples.
        
        Respond with JSON:
        {{
            "bias_score": <float 0.0-1.0, where 1.0 = no bias detected>,
            "bias_analysis": {{
                "leading_questions": [<list of question indices with leading bias>],
                "double_barreled": [<list of question indices with multiple concepts>],
                "loaded_language": [<list of question indices with emotional/loaded terms>],
                "social_desirability": [<list of questions that might trigger social desirability bias>],
                "other_bias_types": [<other identified bias issues>]
            }},
            "overall_bias_assessment": "<comprehensive bias analysis>",
            "neutrality_score": <float 0.0-1.0>,
            "rule_compliance_analysis": "<specific analysis against methodological rigor rules>"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("bias_score", 0.5)
            else:
                return self._basic_bias_analysis(questions)
        except Exception as e:
            print(f"LLM analysis failed for bias detection: {e}")
            return self._basic_bias_analysis(questions)
    
    async def _analyze_sampling_adequacy(self, survey: Dict[str, Any], rfq_text: str) -> float:
        """Analyze sampling considerations and target adequacy using LLM"""
        
        target_responses = survey.get("target_responses", 0)
        estimated_time = survey.get("estimated_time", 0)
        methodology = survey.get("metadata", {}).get("methodology", [])
        
        prompt = f"""
        Analyze the sampling considerations for methodological adequacy.
        
        RFQ Requirements:
        {rfq_text}
        
        Survey Details:
        - Target Responses: {target_responses}
        - Estimated Time: {estimated_time} minutes
        - Methodologies: {methodology}
        
        Evaluate:
        1. Is the target sample size appropriate for the research objectives?
        2. Does the methodology require specific sample size considerations?
        3. Is the survey length appropriate for the target respondents?
        4. Are there adequate screening/qualification questions?
        5. Does the approach match statistical requirements for chosen methods?
        
        Consider:
        - Conjoint analysis typically needs 200+ responses
        - MaxDiff usually requires 150+ responses  
        - Simple surveys may need fewer responses
        - B2B surveys can be smaller but harder to recruit
        - Consumer surveys need larger samples
        
        Respond with JSON:
        {{
            "sampling_score": <float 0.0-1.0>,
            "sample_size_adequacy": <float 0.0-1.0>,
            "methodology_alignment": <float 0.0-1.0>,
            "sampling_analysis": "<detailed sampling assessment>",
            "recommendations": [<sampling improvement recommendations>]
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("sampling_score", 0.5)
            else:
                return self._basic_sampling_analysis(survey, rfq_text)
        except Exception as e:
            print(f"LLM analysis failed for sampling analysis: {e}")
            return self._basic_sampling_analysis(survey, rfq_text)
    
    async def _analyze_methodology_implementation(self, questions: List[Dict], 
                                                methodologies: List[str], rfq_text: str) -> float:
        """Analyze how well declared methodologies are implemented using LLM"""
        
        questions_with_methods = []
        for q in questions:
            if q.get('methodology'):
                questions_with_methods.append({
                    'text': q.get('text', ''),
                    'type': q.get('type', ''),
                    'methodology': q.get('methodology', ''),
                    'options': q.get('options', [])
                })
        
        prompt = f"""
        Analyze how well the declared research methodologies are implemented in the survey questions.
        
        RFQ Context:
        {rfq_text}
        
        Declared Methodologies: {methodologies}
        
        Questions with Methodology Tags:
        {json.dumps(questions_with_methods, indent=2)}
        
        Evaluate:
        1. Are the declared methodologies properly implemented in questions?
        2. Do question types match methodology requirements?
        3. Are methodology-specific best practices followed?
        4. Is there adequate coverage of each declared methodology?
        
        Methodology Implementation Standards:
        - Conjoint Analysis: Choice tasks with attribute trade-offs
        - MaxDiff: Best-worst scaling with item sets
        - Van Westendorp PSM: Price sensitivity with 4 price points
        - Gabor-Granger: Price acceptance at different levels
        - TURF: Total Unduplicated Reach & Frequency analysis
        - Brand Perception: Perceptual mapping questions
        
        Respond with JSON:
        {{
            "implementation_score": <float 0.0-1.0>,
            "methodology_analysis": {{
                "properly_implemented": [<list of well-implemented methodologies>],
                "poorly_implemented": [<list of poorly implemented methodologies>],
                "missing_implementation": [<declared but not implemented methodologies>]
            }},
            "implementation_quality": "<detailed analysis of methodology implementation>",
            "best_practices_adherence": <float 0.0-1.0>
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("implementation_score", 0.5)
            else:
                return self._basic_methodology_implementation_analysis(questions, methodologies)
        except Exception as e:
            print(f"LLM analysis failed for methodology implementation: {e}")
            return self._basic_methodology_implementation_analysis(questions, methodologies)
    
    async def _identify_bias_indicators(self, questions: List[Dict]) -> List[str]:
        """Identify specific bias indicators using LLM"""
        
        questions_text = [f"{i+1}. {q.get('text', '')}" for i, q in enumerate(questions)]
        
        prompt = f"""
        Identify specific bias indicators in these survey questions.
        
        Questions:
        {chr(10).join(questions_text)}
        
        Identify specific instances of:
        1. Leading language ("Don't you think...", "How satisfied are you...")
        2. Loaded terms (emotional, judgmental language)
        3. Assumptions embedded in questions
        4. Double-barreled constructs
        5. Acquiescence-prone phrasing
        
        Return a JSON array of specific bias indicators found:
        [
            "Question 3: Contains leading phrase 'Don't you agree that...'",
            "Question 7: Double-barreled - asks about both price AND quality",
            ...
        ]
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._basic_bias_indicators(questions)
        except Exception as e:
            print(f"LLM analysis failed for bias indicators: {e}")
            return self._basic_bias_indicators(questions)
    
    async def _generate_detailed_analysis(self, questions: List[Dict], methodologies: List[str],
                                        seq_score: float, bias_score: float, 
                                        sampling_score: float, method_score: float) -> Dict[str, Any]:
        """Generate comprehensive methodological rigor analysis using LLM"""
        
        prompt = f"""
        Generate a comprehensive methodological rigor analysis report.
        
        Survey Details:
        - Questions: {len(questions)}
        - Methodologies: {methodologies}
        
        Component Scores:
        - Question Sequencing: {seq_score:.2f}
        - Bias Detection: {bias_score:.2f}
        - Sampling Adequacy: {sampling_score:.2f}
        - Methodology Implementation: {method_score:.2f}
        
        Provide detailed analysis in JSON format:
        {{
            "methodological_strengths": [<list of methodology strengths>],
            "methodological_weaknesses": [<list of methodology weaknesses>],
            "rigor_assessment": {{
                "question_quality": <float 0.0-1.0>,
                "methodology_adherence": <float 0.0-1.0>,
                "bias_control": <float 0.0-1.0>,
                "sampling_appropriateness": <float 0.0-1.0>
            }},
            "best_practices_analysis": "<analysis of adherence to market research best practices>",
            "improvement_areas": [<specific areas needing improvement>]
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._basic_detailed_analysis(seq_score, bias_score, sampling_score, method_score)
        except Exception as e:
            print(f"LLM analysis failed for detailed analysis: {e}")
            return self._basic_detailed_analysis(seq_score, bias_score, sampling_score, method_score)
    
    async def _generate_recommendations(self, analysis: Dict[str, Any], 
                                      overall_score: float, bias_indicators: List[str]) -> List[str]:
        """Generate methodological improvement recommendations using LLM"""
        
        prompt = f"""
        Generate specific recommendations to improve methodological rigor.
        
        Analysis: {json.dumps(analysis, indent=2)}
        Overall Score: {overall_score:.2f}
        Bias Indicators: {bias_indicators}
        
        Generate 3-5 specific, actionable recommendations focusing on:
        - Question rewording to reduce bias
        - Sequence improvements
        - Methodology implementation enhancements
        - Sampling strategy improvements
        
        Return as JSON array:
        ["recommendation 1", "recommendation 2", ...]
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._basic_recommendations(overall_score, bias_indicators)
        except Exception as e:
            print(f"LLM analysis failed for recommendations: {e}")
            return self._basic_recommendations(overall_score, bias_indicators)
    
    # Fallback methods for when LLM is not available
    def _basic_question_sequencing_analysis(self, questions: List[Dict]) -> float:
        """Basic fallback analysis for question sequencing"""
        if not questions:
            return 0.0
        
        score = 0.6  # Base score
        
        # Check if screening questions are first
        first_few = questions[:3]
        if any(q.get('category') == 'screening' for q in first_few):
            score += 0.2
        
        # Check for reasonable length
        if len(questions) > 5:
            score += 0.1
        
        return min(score, 1.0)
    
    def _basic_bias_analysis(self, questions: List[Dict]) -> float:
        """Basic fallback analysis for bias detection"""
        bias_keywords = ['don\'t you', 'wouldn\'t you', 'how satisfied', 'agree that']
        bias_count = 0
        
        for q in questions:
            text = q.get('text', '').lower()
            if any(keyword in text for keyword in bias_keywords):
                bias_count += 1
        
        if not questions:
            return 0.5
        
        bias_rate = bias_count / len(questions)
        return max(0.0, 1.0 - bias_rate)
    
    def _basic_sampling_analysis(self, survey: Dict[str, Any], rfq_text: str) -> float:
        """Basic fallback analysis for sampling adequacy"""
        target_responses = survey.get("target_responses", 0)
        
        if target_responses >= 200:
            return 0.9
        elif target_responses >= 100:
            return 0.7
        elif target_responses >= 50:
            return 0.6
        else:
            return 0.4
    
    def _basic_methodology_implementation_analysis(self, questions: List[Dict], methodologies: List[str]) -> float:
        """Basic fallback analysis for methodology implementation"""
        if not methodologies:
            return 0.7
        
        method_questions = sum(1 for q in questions if q.get('methodology'))
        coverage_rate = method_questions / len(methodologies) if methodologies else 0
        
        return min(coverage_rate, 1.0)
    
    def _basic_bias_indicators(self, questions: List[Dict]) -> List[str]:
        """Basic fallback bias indicator identification"""
        indicators = []
        bias_patterns = {
            'leading': ['don\'t you', 'wouldn\'t you', 'surely you'],
            'loaded': ['obviously', 'clearly', 'naturally'],
            'double_barreled': [' and ', ' or ', ' as well as']
        }
        
        for i, q in enumerate(questions):
            text = q.get('text', '').lower()
            for bias_type, patterns in bias_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        indicators.append(f"Question {i+1}: Potential {bias_type} bias - '{pattern}'")
        
        return indicators
    
    def _basic_detailed_analysis(self, seq_score: float, bias_score: float, 
                               sampling_score: float, method_score: float) -> Dict[str, Any]:
        """Basic fallback detailed analysis"""
        return {
            "methodological_strengths": ["Structured question format", "Multiple methodologies attempted"],
            "methodological_weaknesses": ["Limited bias analysis", "Basic sequencing validation"],
            "rigor_assessment": {
                "question_quality": seq_score,
                "methodology_adherence": method_score,
                "bias_control": bias_score,
                "sampling_appropriateness": sampling_score
            },
            "best_practices_analysis": "Basic adherence to survey methodology principles",
            "improvement_areas": ["Enhanced bias detection", "Improved question flow", "Better methodology implementation"]
        }
    
    def _basic_recommendations(self, overall_score: float, bias_indicators: List[str]) -> List[str]:
        """Basic fallback recommendations"""
        recommendations = []
        
        if overall_score < 0.6:
            recommendations.extend([
                "Review question wording to eliminate potential bias",
                "Reorder questions for better logical flow",
                "Ensure methodology implementation matches declared approaches"
            ])
        
        if bias_indicators:
            recommendations.append("Address identified bias indicators in question phrasing")
        
        if overall_score >= 0.8:
            recommendations.append("Methodological rigor is strong - maintain current approach")
        
        return recommendations if recommendations else ["Continue following current methodology practices"]