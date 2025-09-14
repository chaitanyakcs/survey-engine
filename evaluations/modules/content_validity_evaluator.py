#!/usr/bin/env python3
"""
Content Validity Evaluator - LLM-based Analysis
Evaluates how well the questionnaire captures the intended research objectives
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ContentValidityResult:
    score: float  # 0.0 - 1.0
    objective_coverage: float
    topic_comprehensiveness: float
    research_goal_alignment: float
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]

class ContentValidityEvaluator:
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
        
    async def evaluate_content_validity(self, survey: Dict[str, Any], rfq_text: str) -> ContentValidityResult:
        """
        Evaluate content validity using LLM-based analysis
        
        Args:
            survey: Generated survey dictionary
            rfq_text: Original RFQ text
            
        Returns:
            ContentValidityResult with comprehensive analysis
        """
        
        # Extract survey questions for analysis
        questions = survey.get("questions", [])
        survey_title = survey.get("title", "")
        survey_description = survey.get("description", "")
        
        # Perform LLM-based analysis
        objective_coverage = await self._analyze_objective_coverage(rfq_text, questions)
        topic_comprehensiveness = await self._analyze_topic_comprehensiveness(rfq_text, questions)
        research_goal_alignment = await self._analyze_research_goal_alignment(rfq_text, survey_title, survey_description)
        
        # Calculate weighted overall score
        overall_score = (
            objective_coverage * 0.4 +
            topic_comprehensiveness * 0.4 +
            research_goal_alignment * 0.2
        )
        
        # Generate detailed analysis
        detailed_analysis = await self._generate_detailed_analysis(
            rfq_text, survey, objective_coverage, topic_comprehensiveness, research_goal_alignment
        )
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(detailed_analysis, overall_score)
        
        return ContentValidityResult(
            score=overall_score,
            objective_coverage=objective_coverage,
            topic_comprehensiveness=topic_comprehensiveness,
            research_goal_alignment=research_goal_alignment,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations
        )
    
    async def _analyze_objective_coverage(self, rfq_text: str, questions: List[Dict]) -> float:
        """Analyze how well questions cover RFQ objectives using LLM with pillar rules"""
        
        # Get pillar-specific rules context
        rules_context = ""
        if self.pillar_rules_service:
            rules_context = self.pillar_rules_service.create_pillar_rule_prompt_context("content_validity")
        
        prompt = f"""
        {rules_context}
        
        Analyze how well the survey questions cover the research objectives stated in the RFQ based on the Content Validity rules specified above.
        
        RFQ Text:
        {rfq_text}
        
        Survey Questions:
        {json.dumps([q.get('text', '') for q in questions], indent=2)}
        
        Evaluate specifically against the rules listed above:
        1. Are all key research objectives from the RFQ addressed by questions?
        2. Are there critical gaps where objectives are not covered?
        3. Do questions directly map to stated research goals?
        4. Is the coverage comprehensive without significant gaps?
        
        Provide specific examples of how each rule is met or violated.
        
        Respond with a JSON object containing:
        {{
            "coverage_score": <float 0.0-1.0>,
            "covered_objectives": [<list of objectives that are well covered>],
            "missing_objectives": [<list of objectives not covered>],
            "gap_analysis": "<detailed analysis of coverage gaps>",
            "rule_compliance_analysis": "<specific analysis against pillar rules>"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("coverage_score", 0.5)
            else:
                # Fallback basic analysis
                return self._basic_objective_coverage_analysis(rfq_text, questions)
        except Exception as e:
            print(f"LLM analysis failed for objective coverage: {e}")
            return self._basic_objective_coverage_analysis(rfq_text, questions)
    
    async def _analyze_topic_comprehensiveness(self, rfq_text: str, questions: List[Dict]) -> float:
        """Analyze topic comprehensiveness using LLM"""
        
        prompt = f"""
        Evaluate how comprehensively the survey covers all necessary aspects of the research topic.
        
        RFQ Text:
        {rfq_text}
        
        Survey Questions:
        {json.dumps([q.get('text', '') for q in questions], indent=2)}
        
        Assess:
        1. Does the survey cover all relevant dimensions of the topic?
        2. Are there important subtopics missing?
        3. Is there appropriate depth vs breadth balance?
        4. Does question coverage match the scope implied in the RFQ?
        
        Respond with a JSON object:
        {{
            "comprehensiveness_score": <float 0.0-1.0>,
            "covered_topics": [<list of well-covered topic areas>],
            "missing_topics": [<list of important missing topics>],
            "depth_analysis": "<analysis of topic depth and coverage balance>"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("comprehensiveness_score", 0.5)
            else:
                return self._basic_topic_comprehensiveness_analysis(rfq_text, questions)
        except Exception as e:
            print(f"LLM analysis failed for topic comprehensiveness: {e}")
            return self._basic_topic_comprehensiveness_analysis(rfq_text, questions)
    
    async def _analyze_research_goal_alignment(self, rfq_text: str, title: str, description: str) -> float:
        """Analyze research goal alignment using LLM"""
        
        prompt = f"""
        Evaluate how well the survey title and description align with the research goals stated in the RFQ.
        
        RFQ Text:
        {rfq_text}
        
        Survey Title: {title}
        Survey Description: {description}
        
        Assess:
        1. Does the survey title accurately reflect the RFQ's research intent?
        2. Does the description properly frame the research objectives?
        3. Is there clear alignment between RFQ goals and survey positioning?
        4. Would participants understand the research purpose from the survey framing?
        
        Respond with a JSON object:
        {{
            "alignment_score": <float 0.0-1.0>,
            "title_relevance": <float 0.0-1.0>,
            "description_clarity": <float 0.0-1.0>,
            "alignment_analysis": "<detailed analysis of goal alignment>"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                result = json.loads(response)
                return result.get("alignment_score", 0.5)
            else:
                return self._basic_research_goal_alignment_analysis(rfq_text, title, description)
        except Exception as e:
            print(f"LLM analysis failed for research goal alignment: {e}")
            return self._basic_research_goal_alignment_analysis(rfq_text, title, description)
    
    async def _generate_detailed_analysis(self, rfq_text: str, survey: Dict, 
                                        obj_coverage: float, topic_comp: float, goal_align: float) -> Dict[str, Any]:
        """Generate comprehensive detailed analysis using LLM"""
        
        prompt = f"""
        Generate a detailed content validity analysis report.
        
        RFQ: {rfq_text}
        Survey: {json.dumps(survey, indent=2)}
        
        Scores:
        - Objective Coverage: {obj_coverage:.2f}
        - Topic Comprehensiveness: {topic_comp:.2f}
        - Research Goal Alignment: {goal_align:.2f}
        
        Provide detailed analysis in JSON format:
        {{
            "strengths": [<list of content validity strengths>],
            "weaknesses": [<list of content validity weaknesses>],
            "coverage_gaps": [<specific gaps in coverage>],
            "quality_indicators": {{
                "question_relevance": <float 0.0-1.0>,
                "scope_appropriateness": <float 0.0-1.0>,
                "objective_mapping": <float 0.0-1.0>
            }},
            "narrative_summary": "<comprehensive narrative analysis>"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._basic_detailed_analysis(obj_coverage, topic_comp, goal_align)
        except Exception as e:
            print(f"LLM analysis failed for detailed analysis: {e}")
            return self._basic_detailed_analysis(obj_coverage, topic_comp, goal_align)
    
    async def _generate_recommendations(self, analysis: Dict[str, Any], overall_score: float) -> List[str]:
        """Generate actionable recommendations using LLM"""
        
        prompt = f"""
        Based on the content validity analysis, generate specific actionable recommendations for improving the survey.
        
        Analysis: {json.dumps(analysis, indent=2)}
        Overall Score: {overall_score:.2f}
        
        Generate 3-5 specific, actionable recommendations that would improve content validity.
        Focus on:
        - Questions to add for better coverage
        - Questions to modify for better alignment
        - Structural changes to improve validity
        - Methodological improvements
        
        Return as a JSON array of strings:
        ["recommendation 1", "recommendation 2", ...]
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._basic_recommendations(overall_score)
        except Exception as e:
            print(f"LLM analysis failed for recommendations: {e}")
            return self._basic_recommendations(overall_score)
    
    # Fallback methods for when LLM is not available
    def _basic_objective_coverage_analysis(self, rfq_text: str, questions: List[Dict]) -> float:
        """Basic fallback analysis for objective coverage"""
        if not questions:
            return 0.0
        
        # Simple keyword-based analysis
        rfq_words = set(rfq_text.lower().split())
        question_words = set()
        for q in questions:
            question_words.update(q.get('text', '').lower().split())
        
        overlap = len(rfq_words & question_words)
        return min(overlap / len(rfq_words), 1.0) if rfq_words else 0.5
    
    def _basic_topic_comprehensiveness_analysis(self, rfq_text: str, questions: List[Dict]) -> float:
        """Basic fallback analysis for topic comprehensiveness"""
        base_score = 0.6
        if len(questions) >= 10:
            base_score += 0.2
        if len(questions) >= 15:
            base_score += 0.1
        return min(base_score, 1.0)
    
    def _basic_research_goal_alignment_analysis(self, rfq_text: str, title: str, description: str) -> float:
        """Basic fallback analysis for research goal alignment"""
        score = 0.5
        if title and len(title) > 10:
            score += 0.2
        if description and len(description) > 50:
            score += 0.2
        return min(score, 1.0)
    
    def _basic_detailed_analysis(self, obj_coverage: float, topic_comp: float, goal_align: float) -> Dict[str, Any]:
        """Basic fallback detailed analysis"""
        return {
            "strengths": ["Survey generated successfully", "Questions are structured"],
            "weaknesses": ["Limited LLM analysis available"],
            "coverage_gaps": ["Detailed gap analysis requires LLM"],
            "quality_indicators": {
                "question_relevance": obj_coverage,
                "scope_appropriateness": topic_comp,
                "objective_mapping": goal_align
            },
            "narrative_summary": f"Content validity analysis completed with scores: Objective Coverage {obj_coverage:.2f}, Topic Comprehensiveness {topic_comp:.2f}, Goal Alignment {goal_align:.2f}"
        }
    
    def _basic_recommendations(self, overall_score: float) -> List[str]:
        """Basic fallback recommendations"""
        if overall_score < 0.6:
            return [
                "Review survey questions for better alignment with RFQ objectives",
                "Add questions to cover missing research areas",
                "Improve question wording for clarity and relevance"
            ]
        elif overall_score < 0.8:
            return [
                "Fine-tune question ordering for better flow",
                "Add depth to high-priority research areas",
                "Review question types for methodology alignment"
            ]
        else:
            return [
                "Survey demonstrates strong content validity",
                "Consider minor refinements based on specific feedback",
                "Maintain current structure and approach"
            ]