#!/usr/bin/env python3
"""
Advanced Methodological Rigor Evaluator - Chain-of-Thought Implementation
Implements sophisticated bias detection and methodological analysis with detailed reasoning
"""

import asyncio
import json
import re
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent directory to path for utils import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import extract_all_questions

@dataclass
class BiasAnalysis:
    """Comprehensive bias detection with specific types"""
    bias_type: str  # leading, loaded, double_barreled, etc.
    question_id: str
    question_text: str
    severity: str  # critical, high, medium, low
    specific_issue: str
    suggested_fix: str
    confidence: float  # 0.0-1.0

@dataclass
class QuestionFlowAnalysis:
    """Question sequencing and flow analysis"""
    question_id: str
    position: int
    flow_score: float  # 0.0-1.0
    sequencing_issues: List[str]
    optimal_position: Optional[int]
    reasoning: str

@dataclass
class MethodologyComplianceAnalysis:
    """Analysis of methodology implementation compliance"""
    methodology: str
    implementation_quality: float  # 0.0-1.0
    required_elements: List[str]
    missing_elements: List[str]
    compliance_issues: List[str]
    specific_recommendations: List[str]

@dataclass
class AdvancedMethodologicalRigorResult:
    """Comprehensive methodological rigor result with chain-of-thought"""
    overall_score: float
    reasoning_chain: List[str]
    bias_analysis: List[BiasAnalysis]
    question_flow_analysis: List[QuestionFlowAnalysis]
    methodology_compliance: List[MethodologyComplianceAnalysis]
    statistical_power_assessment: Dict[str, Any]
    sampling_adequacy_analysis: Dict[str, Any]
    specific_recommendations: List[Dict[str, Any]]
    confidence_score: float
    evaluation_metadata: Dict[str, Any]

class AdvancedMethodologicalRigorEvaluator:
    """
    State-of-the-art Methodological Rigor Evaluator using chain-of-thought reasoning
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
    
    async def evaluate_methodological_rigor(self, survey: Dict[str, Any], rfq_text: str, survey_id: str = None, rfq_id: str = None) -> AdvancedMethodologicalRigorResult:
        """
        Perform advanced methodological rigor evaluation using chain-of-thought reasoning
        
        REASONING CHAIN:
        Step 1: Advanced Bias Detection - Multi-type bias analysis with severity assessment
        Step 2: Question Flow Analysis - Sophisticated sequencing evaluation  
        Step 3: Methodology Compliance Analysis - Deep implementation assessment
        Step 4: Statistical Power Assessment - Sample size and methodology alignment
        Step 5: Generate Specific Recommendations - Actionable methodological improvements
        """
        
        print("🔬 Starting advanced methodological rigor evaluation with chain-of-thought reasoning...")
        
        reasoning_chain = []
        
        # Step 1: Advanced Bias Detection
        reasoning_chain.append("STEP 1: Performing advanced multi-type bias detection with severity assessment")
        bias_analysis = await self._advanced_bias_detection(extract_all_questions(survey))
        
        # Step 2: Question Flow Analysis
        reasoning_chain.append("STEP 2: Analyzing question sequencing and logical flow")
        flow_analysis = await self._question_flow_analysis(extract_all_questions(survey), rfq_text)
        
        # Step 3: Methodology Compliance Analysis
        reasoning_chain.append("STEP 3: Evaluating methodology implementation compliance")
        methodology_compliance = await self._methodology_compliance_analysis(survey, rfq_text)
        
        # Step 4: Statistical Power Assessment
        reasoning_chain.append("STEP 4: Assessing statistical power and sampling adequacy")
        power_assessment = await self._statistical_power_assessment(survey, rfq_text)
        sampling_analysis = await self._sampling_adequacy_analysis(survey, rfq_text)
        
        # Step 5: Generate Specific Recommendations
        reasoning_chain.append("STEP 5: Generating specific methodological improvement recommendations")
        recommendations = await self._generate_methodological_recommendations(
            bias_analysis, flow_analysis, methodology_compliance, power_assessment, sampling_analysis
        )
        
        # Calculate overall score using sophisticated weighting
        overall_score = await self._calculate_advanced_methodological_score(
            bias_analysis, flow_analysis, methodology_compliance, power_assessment, sampling_analysis
        )
        
        # Calculate confidence score based on analysis depth
        confidence_score = self._calculate_confidence_score(bias_analysis, flow_analysis, methodology_compliance)
        
        return AdvancedMethodologicalRigorResult(
            overall_score=overall_score,
            reasoning_chain=reasoning_chain,
            bias_analysis=bias_analysis,
            question_flow_analysis=flow_analysis,
            methodology_compliance=methodology_compliance,
            statistical_power_assessment=power_assessment,
            sampling_adequacy_analysis=sampling_analysis,
            specific_recommendations=recommendations,
            confidence_score=confidence_score,
            evaluation_metadata={
                "evaluation_timestamp": datetime.now().isoformat(),
                "llm_powered": self.llm_client is not None,
                "rules_context_used": self.pillar_rules_service is not None,
                "biases_detected": len(bias_analysis),
                "questions_analyzed": len(flow_analysis),
                "methodologies_evaluated": len(methodology_compliance)
            }
        )
    
    async def _advanced_bias_detection(self, questions: List[Dict]) -> List[BiasAnalysis]:
        """
        Perform sophisticated multi-type bias detection with severity assessment
        """
        
        # Get pillar rules context
        rules_context = ""
        if self.pillar_rules_service:
            rules_context = self.pillar_rules_service.create_pillar_rule_prompt_context("methodological_rigor")
        
        prompt = f"""
        You are an expert survey methodologist. Perform comprehensive bias detection analysis for each question.
        
        PILLAR RULES CONTEXT:
        {rules_context}
        
        QUESTIONS TO ANALYZE:
        {json.dumps([{"id": f"q{i+1}", "text": q.get("text", ""), "type": q.get("type", "")} for i, q in enumerate(questions)], indent=2)}
        
        BIAS DETECTION TASK:
        For each question, detect and analyze ALL types of bias:
        
        1. LEADING BIAS: Questions that suggest desired answers
        2. LOADED BIAS: Emotional, judgmental, or assumption-laden language
        3. DOUBLE-BARRELED BIAS: Questions asking multiple things simultaneously
        4. ACQUIESCENCE BIAS: Phrasing that encourages yes-saying
        5. SOCIAL DESIRABILITY BIAS: Questions triggering socially acceptable responses
        6. CONFIRMATION BIAS: Questions that confirm preconceived notions
        7. RESPONSE ORDER BIAS: Answer ordering that influences choices
        8. FRAMING EFFECTS: Presentation that influences interpretation
        
        For each bias detected, assess:
        - Severity: critical (will invalidate results), high (significant impact), medium (moderate impact), low (minor concern)
        - Specific issue explanation
        - Suggested fix with exact rewording
        - Confidence in detection (0.0-1.0)
        
        Respond with JSON:
        {{
            "bias_detections": [
                {{
                    "bias_type": "leading",
                    "question_id": "q1",
                    "question_text": "exact question text",
                    "severity": "critical",
                    "specific_issue": "detailed explanation of the bias",
                    "suggested_fix": "specific rewrite to eliminate bias",
                    "confidence": 0.9
                }}
            ],
            "overall_bias_assessment": "comprehensive summary of bias landscape",
            "neutrality_score": 0.75,
            "analysis_confidence": 0.85
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=2000)
                if response.success:
                    result = json.loads(response.content)
                    bias_analyses = []
                    for detection in result.get("bias_detections", []):
                        bias_analyses.append(BiasAnalysis(
                            bias_type=detection["bias_type"],
                            question_id=detection["question_id"],
                            question_text=detection["question_text"],
                            severity=detection["severity"],
                            specific_issue=detection["specific_issue"],
                            suggested_fix=detection["suggested_fix"],
                            confidence=detection["confidence"]
                        ))
                    return bias_analyses
        except Exception as e:
            print(f"🔴 LLM bias detection failed: {e}")
        
        # Fallback to basic bias detection
        return self._basic_bias_detection(questions)
    
    async def _question_flow_analysis(self, questions: List[Dict], rfq_text: str) -> List[QuestionFlowAnalysis]:
        """
        Analyze question sequencing and logical flow with optimization suggestions
        """
        
        prompt = f"""
        You are an expert survey methodologist. Analyze the logical flow and sequencing of these questions.
        
        RFQ CONTEXT:
        {rfq_text}
        
        QUESTIONS IN SEQUENCE:
        {json.dumps([{"position": i+1, "id": f"q{i+1}", "text": q.get("text", ""), "type": q.get("type", "")} for i, q in enumerate(questions)], indent=2)}
        
        FLOW ANALYSIS TASK:
        For each question, evaluate:
        
        1. SEQUENCING APPROPRIATENESS: Is this question in the optimal position?
        2. LOGICAL PROGRESSION: Does it follow naturally from previous questions?
        3. WARM-UP CONSIDERATIONS: Are easier questions positioned early?
        4. SENSITIVE QUESTION PLACEMENT: Are personal/sensitive questions toward the end?
        5. TOPIC GROUPING: Are related questions clustered appropriately?
        6. BIAS PREVENTION: Does earlier question order avoid influencing later responses?
        7. RESPONDENT EXPERIENCE: Does the flow maintain engagement?
        
        Best Practices to Consider:
        - Screening questions first
        - Build rapport with easy, engaging questions
        - Group related topics together
        - Place sensitive/personal questions later
        - End with demographics
        - Avoid order effects that bias responses
        
        For each question, provide:
        - Flow score (0.0-1.0) for current position
        - Specific sequencing issues
        - Optimal position recommendation
        - Detailed reasoning
        
        Respond with JSON:
        {{
            "flow_analysis": [
                {{
                    "question_id": "q1",
                    "position": 1,
                    "flow_score": 0.85,
                    "sequencing_issues": ["list of specific issues"],
                    "optimal_position": 3,
                    "reasoning": "detailed explanation of flow assessment"
                }}
            ],
            "overall_flow_score": 0.75,
            "flow_recommendations": ["specific flow improvement suggestions"]
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=1500)
                if response.success:
                    result = json.loads(response.content)
                    flow_analyses = []
                    for analysis in result.get("flow_analysis", []):
                        flow_analyses.append(QuestionFlowAnalysis(
                            question_id=analysis["question_id"],
                            position=analysis["position"],
                            flow_score=analysis["flow_score"],
                            sequencing_issues=analysis["sequencing_issues"],
                            optimal_position=analysis.get("optimal_position"),
                            reasoning=analysis["reasoning"]
                        ))
                    return flow_analyses
        except Exception as e:
            print(f"🔴 Question flow analysis failed: {e}")
        
        # Fallback to basic flow analysis
        return self._basic_flow_analysis(questions)
    
    async def _methodology_compliance_analysis(self, survey: Dict[str, Any], rfq_text: str) -> List[MethodologyComplianceAnalysis]:
        """
        Analyze compliance with declared research methodologies
        """
        
        methodologies = survey.get("metadata", {}).get("methodology", [])
        if not methodologies:
            return []
        
        questions_with_methods = []
        for i, q in enumerate(extract_all_questions(survey)):
            if q.get('methodology'):
                questions_with_methods.append({
                    'id': f'q{i+1}',
                    'text': q.get('text', ''),
                    'type': q.get('type', ''),
                    'methodology': q.get('methodology', ''),
                    'options': q.get('options', [])
                })
        
        prompt = f"""
        You are an expert in market research methodologies. Analyze compliance with declared methodologies.
        
        RFQ CONTEXT:
        {rfq_text}
        
        DECLARED METHODOLOGIES: {methodologies}
        
        METHODOLOGY-TAGGED QUESTIONS:
        {json.dumps(questions_with_methods, indent=2)}
        
        COMPLIANCE ANALYSIS TASK:
        For each declared methodology, evaluate:
        
        METHODOLOGY REQUIREMENTS:
        - Conjoint Analysis: Choice tasks with attribute trade-offs, full factorial or orthogonal design
        - MaxDiff: Best-worst scaling with item sets, balanced incomplete block design
        - Van Westendorp PSM: 4 price sensitivity questions (too cheap, cheap, expensive, too expensive)
        - Gabor-Granger: Price acceptance testing at multiple price points
        - TURF Analysis: Reach and frequency questions for portfolio optimization
        - Brand Perception: Perceptual mapping with attribute ratings
        - Concept Testing: Concept exposure with purchase intent and diagnostics
        
        For each methodology:
        1. IMPLEMENTATION QUALITY: How well is it implemented? (0.0-1.0)
        2. REQUIRED ELEMENTS: What elements should be present?
        3. MISSING ELEMENTS: What's missing from proper implementation?
        4. COMPLIANCE ISSUES: Specific problems with current implementation
        5. SPECIFIC RECOMMENDATIONS: Exact changes needed for compliance
        
        Respond with JSON:
        {{
            "methodology_compliance": [
                {{
                    "methodology": "Conjoint Analysis",
                    "implementation_quality": 0.7,
                    "required_elements": ["choice tasks", "attribute levels", "orthogonal design"],
                    "missing_elements": ["proper attribute level balance"],
                    "compliance_issues": ["insufficient choice tasks for robust analysis"],
                    "specific_recommendations": ["add 2 more choice tasks with balanced attributes"]
                }}
            ],
            "overall_compliance_score": 0.65,
            "compliance_summary": "detailed assessment of methodology implementation"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=1500)
                if response.success:
                    result = json.loads(response.content)
                    compliance_analyses = []
                    for compliance in result.get("methodology_compliance", []):
                        compliance_analyses.append(MethodologyComplianceAnalysis(
                            methodology=compliance["methodology"],
                            implementation_quality=compliance["implementation_quality"],
                            required_elements=compliance["required_elements"],
                            missing_elements=compliance["missing_elements"],
                            compliance_issues=compliance["compliance_issues"],
                            specific_recommendations=compliance["specific_recommendations"]
                        ))
                    return compliance_analyses
        except Exception as e:
            print(f"🔴 Methodology compliance analysis failed: {e}")
        
        # Fallback to basic compliance analysis
        return self._basic_compliance_analysis(survey, methodologies)
    
    async def _statistical_power_assessment(self, survey: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """
        Assess statistical power and sample size requirements
        """
        
        target_responses = survey.get("target_responses", 0)
        methodologies = survey.get("metadata", {}).get("methodology", [])
        
        prompt = f"""
        You are a statistical expert. Assess the statistical power and sample size adequacy.
        
        RFQ CONTEXT:
        {rfq_text}
        
        SURVEY DETAILS:
        - Target Responses: {target_responses}
        - Methodologies: {methodologies}
        - Number of Questions: {len(extract_all_questions(survey))}
        
        STATISTICAL POWER ANALYSIS:
        
        Consider methodology-specific requirements:
        - Conjoint Analysis: Minimum 200 responses, prefer 300+ for reliable utilities
        - MaxDiff: Minimum 150 responses, 200+ for stable scores
        - Van Westendorp PSM: Minimum 100 responses for price range estimation
        - Gabor-Granger: 150+ responses per price point tested
        - TURF Analysis: 200+ responses for portfolio optimization
        - Statistical Significance Testing: Power analysis for effect size detection
        
        Assess:
        1. SAMPLE SIZE ADEQUACY: Is the target sample sufficient?
        2. POWER CALCULATION: What effect sizes can be detected?
        3. METHODOLOGY ALIGNMENT: Do sample sizes match methodology needs?
        4. STATISTICAL VALIDITY: Will results be statistically meaningful?
        5. SEGMENTATION CAPACITY: Sufficient sample for subgroup analysis?
        
        Respond with JSON:
        {{
            "power_assessment": {{
                "overall_adequacy_score": 0.75,
                "sample_size_evaluation": "detailed assessment of sample size",
                "methodology_alignment": 0.8,
                "detectable_effect_sizes": {{"survey_metrics": "medium effects detectable"}},
                "power_recommendations": ["specific recommendations for statistical power"],
                "risk_assessment": "risks of underpowered analysis"
            }},
            "adequacy_score": 0.75
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=1000)
                if response.success:
                    result = json.loads(response.content)
                    return result.get("power_assessment", {})
        except Exception as e:
            print(f"🔴 Statistical power assessment failed: {e}")
        
        # Basic fallback assessment
        return self._basic_power_assessment(survey, methodologies)
    
    async def _sampling_adequacy_analysis(self, survey: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """
        Analyze sampling strategy adequacy
        """
        
        # Basic sampling analysis for now
        target_responses = survey.get("target_responses", 0)
        
        adequacy_score = 0.5
        if target_responses >= 300:
            adequacy_score = 0.9
        elif target_responses >= 200:
            adequacy_score = 0.8
        elif target_responses >= 100:
            adequacy_score = 0.6
        
        return {
            "adequacy_score": adequacy_score,
            "target_responses": target_responses,
            "sampling_strategy": "Random sampling assumed",
            "representativeness_concerns": [] if target_responses >= 200 else ["Low sample size may affect representativeness"],
            "sampling_recommendations": ["Ensure representative sampling across target segments"]
        }
    
    async def _generate_methodological_recommendations(self, bias_analysis: List[BiasAnalysis], 
                                                     flow_analysis: List[QuestionFlowAnalysis],
                                                     methodology_compliance: List[MethodologyComplianceAnalysis],
                                                     power_assessment: Dict[str, Any],
                                                     sampling_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate specific actionable methodological recommendations
        """
        
        recommendations = []
        
        # Critical bias recommendations
        critical_biases = [b for b in bias_analysis if b.severity == "critical"]
        for bias in critical_biases:
            recommendations.append({
                "type": "bias_fix",
                "priority": "critical",
                "issue": f"Critical {bias.bias_type} bias in {bias.question_id}",
                "current_problem": bias.specific_issue,
                "suggested_fix": bias.suggested_fix,
                "expected_impact": "high",
                "implementation_notes": f"Reword question to eliminate {bias.bias_type} bias"
            })
        
        # Flow improvement recommendations
        poor_flow_questions = [f for f in flow_analysis if f.flow_score < 0.6]
        for flow in poor_flow_questions[:3]:  # Top 3 flow issues
            recommendations.append({
                "type": "flow_improvement",
                "priority": "high",
                "issue": f"Poor question sequencing for {flow.question_id}",
                "current_position": flow.position,
                "suggested_position": flow.optimal_position,
                "reasoning": flow.reasoning,
                "expected_impact": "medium"
            })
        
        # Methodology compliance recommendations
        for compliance in methodology_compliance:
            if compliance.implementation_quality < 0.7:
                recommendations.append({
                    "type": "methodology_improvement",
                    "priority": "high",
                    "issue": f"Poor implementation of {compliance.methodology}",
                    "missing_elements": compliance.missing_elements,
                    "specific_recommendations": compliance.specific_recommendations,
                    "expected_impact": "high"
                })
        
        # Statistical power recommendations
        if power_assessment.get("adequacy_score", 0) < 0.7:
            recommendations.append({
                "type": "sample_size_adjustment",
                "priority": "medium",
                "issue": "Insufficient sample size for reliable results",
                "power_concerns": power_assessment.get("risk_assessment", ""),
                "recommendations": power_assessment.get("power_recommendations", []),
                "expected_impact": "high"
            })
        
        return recommendations
    
    async def _calculate_advanced_methodological_score(self, bias_analysis: List[BiasAnalysis], 
                                                     flow_analysis: List[QuestionFlowAnalysis],
                                                     methodology_compliance: List[MethodologyComplianceAnalysis],
                                                     power_assessment: Dict[str, Any],
                                                     sampling_analysis: Dict[str, Any]) -> float:
        """
        Calculate sophisticated overall methodological rigor score
        """
        
        # Weight factors for different aspects
        BIAS_CONTROL_WEIGHT = 0.35
        QUESTION_FLOW_WEIGHT = 0.25
        METHODOLOGY_COMPLIANCE_WEIGHT = 0.25
        STATISTICAL_POWER_WEIGHT = 0.15
        
        # Calculate bias control score (inverse of bias severity)
        bias_score = 1.0
        if bias_analysis:
            critical_penalty = len([b for b in bias_analysis if b.severity == "critical"]) * 0.3
            high_penalty = len([b for b in bias_analysis if b.severity == "high"]) * 0.15
            medium_penalty = len([b for b in bias_analysis if b.severity == "medium"]) * 0.05
            bias_score = max(0.0, 1.0 - critical_penalty - high_penalty - medium_penalty)
        
        # Calculate flow score
        flow_scores = [f.flow_score for f in flow_analysis]
        avg_flow_score = sum(flow_scores) / len(flow_scores) if flow_scores else 0.7
        
        # Calculate methodology compliance score
        compliance_scores = [c.implementation_quality for c in methodology_compliance]
        avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.8
        
        # Statistical power score
        power_score = power_assessment.get("adequacy_score", 0.7)
        
        # Weighted final score
        final_score = (
            bias_score * BIAS_CONTROL_WEIGHT +
            avg_flow_score * QUESTION_FLOW_WEIGHT +
            avg_compliance_score * METHODOLOGY_COMPLIANCE_WEIGHT +
            power_score * STATISTICAL_POWER_WEIGHT
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_confidence_score(self, bias_analysis: List[BiasAnalysis], 
                                  flow_analysis: List[QuestionFlowAnalysis],
                                  methodology_compliance: List[MethodologyComplianceAnalysis]) -> float:
        """
        Calculate confidence in the methodological evaluation based on analysis depth
        """
        
        base_confidence = 0.8 if self.llm_client else 0.5
        
        # Higher confidence with more detailed bias analysis
        bias_bonus = min(0.15, len(bias_analysis) * 0.03)
        
        # Higher confidence with detailed flow analysis
        flow_bonus = min(0.05, len([f for f in flow_analysis if len(f.sequencing_issues) > 0]) * 0.01)
        
        return min(1.0, base_confidence + bias_bonus + flow_bonus)
    
    # Fallback methods for when LLM is not available
    def _basic_bias_detection(self, questions: List[Dict]) -> List[BiasAnalysis]:
        """
        Fallback bias detection using simple pattern matching
        """
        
        bias_analyses = []
        bias_patterns = {
            'leading': ['don\'t you', 'wouldn\'t you', 'surely you', 'obviously'],
            'loaded': ['terrible', 'amazing', 'horrible', 'wonderful'],
            'double_barreled': [' and ', ' or ', ' as well as']
        }
        
        for i, question in enumerate(questions):
            text = question.get("text", "").lower()
            question_id = f"q{i+1}"
            
            for bias_type, patterns in bias_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        bias_analyses.append(BiasAnalysis(
                            bias_type=bias_type,
                            question_id=question_id,
                            question_text=question.get("text", ""),
                            severity="medium",
                            specific_issue=f"Contains {bias_type} pattern: '{pattern}'",
                            suggested_fix=f"Rewrite to eliminate '{pattern}' and use neutral language",
                            confidence=0.6
                        ))
        
        return bias_analyses
    
    def _basic_flow_analysis(self, questions: List[Dict]) -> List[QuestionFlowAnalysis]:
        """
        Fallback flow analysis using basic heuristics
        """
        
        flow_analyses = []
        for i, question in enumerate(questions):
            question_id = f"q{i+1}"
            
            # Basic flow scoring based on position
            flow_score = 0.7  # Default moderate score
            issues = []
            
            # Simple heuristics
            if i == 0:  # First question should be engaging
                if len(question.get("text", "")) < 20:
                    issues.append("First question may be too brief for engagement")
            
            flow_analyses.append(QuestionFlowAnalysis(
                question_id=question_id,
                position=i + 1,
                flow_score=flow_score,
                sequencing_issues=issues,
                optimal_position=i + 1,  # Keep current position in fallback
                reasoning="Basic heuristic analysis - LLM analysis recommended for detailed insights"
            ))
        
        return flow_analyses
    
    def _basic_compliance_analysis(self, survey: Dict[str, Any], methodologies: List[str]) -> List[MethodologyComplianceAnalysis]:
        """
        Fallback methodology compliance analysis
        """
        
        compliance_analyses = []
        for methodology in methodologies:
            compliance_analyses.append(MethodologyComplianceAnalysis(
                methodology=methodology,
                implementation_quality=0.6,  # Moderate default
                required_elements=[f"Proper {methodology} implementation"],
                missing_elements=["Detailed analysis requires LLM"],
                compliance_issues=["Cannot perform detailed compliance check without LLM"],
                specific_recommendations=[f"Review {methodology} best practices and implementation"]
            ))
        
        return compliance_analyses
    
    def _basic_power_assessment(self, survey: Dict[str, Any], methodologies: List[str]) -> Dict[str, Any]:
        """
        Basic statistical power assessment
        """
        
        target_responses = survey.get("target_responses", 0)
        
        adequacy_score = 0.5
        if target_responses >= 300:
            adequacy_score = 0.9
        elif target_responses >= 200:
            adequacy_score = 0.7
        elif target_responses >= 100:
            adequacy_score = 0.6
        
        return {
            "overall_adequacy_score": adequacy_score,
            "sample_size_evaluation": f"Target of {target_responses} responses assessed",
            "methodology_alignment": 0.7,
            "detectable_effect_sizes": {"general": "medium to large effects"},
            "power_recommendations": ["Consider larger sample size for robust results"],
            "risk_assessment": "Basic assessment - detailed power analysis requires methodology specifics",
            "adequacy_score": adequacy_score
        }
    