#!/usr/bin/env python3
"""
Advanced Content Validity Evaluator - Chain-of-Thought Implementation
Implements sophisticated LLM reasoning for content validity assessment
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
class ResearchObjective:
    """Extracted research objective with semantic analysis"""
    text: str
    category: str  # primary, secondary, exploratory
    priority: float  # 0.0-1.0
    keywords: List[str]
    semantic_intent: str

@dataclass
class QuestionMapping:
    """Question to objective mapping with analysis"""
    question_id: str
    question_text: str
    mapped_objectives: List[str]
    coverage_quality: float  # 0.0-1.0
    gaps_identified: List[str]
    improvement_suggestions: List[str]

@dataclass
class GapAnalysis:
    """Comprehensive gap analysis"""
    missing_objectives: List[ResearchObjective]
    partially_covered: List[Tuple[ResearchObjective, float]]  # objective, coverage%
    over_covered: List[ResearchObjective]
    critical_gaps: List[str]
    impact_assessment: Dict[str, float]

@dataclass
class MultiPerspectiveAnalysis:
    """Multi-stakeholder perspective analysis"""
    researcher_view: Dict[str, Any]
    respondent_view: Dict[str, Any]
    analyst_view: Dict[str, Any]
    consensus_score: float

@dataclass
class AdvancedContentValidityResult:
    """Comprehensive content validity result"""
    overall_score: float
    reasoning_chain: List[str]
    research_objectives: List[ResearchObjective]
    question_mappings: List[QuestionMapping]
    gap_analysis: GapAnalysis
    multi_perspective: MultiPerspectiveAnalysis
    specific_recommendations: List[Dict[str, Any]]
    confidence_score: float
    evaluation_metadata: Dict[str, Any]

class AdvancedContentValidityEvaluator:
    """
    State-of-the-art Content Validity Evaluator using chain-of-thought reasoning
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
    
    async def evaluate_content_validity(self, survey: Dict[str, Any], rfq_text: str, survey_id: str = None, rfq_id: str = None) -> AdvancedContentValidityResult:
        """
        Perform advanced content validity evaluation using chain-of-thought reasoning
        
        REASONING CHAIN:
        Step 1: Semantic RFQ Analysis - Extract research objectives with intent
        Step 2: Question-Objective Mapping - Map each question to objectives  
        Step 3: Coverage Gap Analysis - Identify missing/over-covered areas
        Step 4: Multi-Perspective Analysis - Evaluate from different stakeholder views
        Step 5: Generate Specific Recommendations - Actionable improvement suggestions
        """
        
        print("🔍 Starting advanced content validity evaluation with chain-of-thought reasoning...")
        
        reasoning_chain = []
        
        # Step 1: Semantic RFQ Analysis
        reasoning_chain.append("STEP 1: Extracting research objectives with semantic analysis")
        research_objectives = await self._extract_research_objectives(rfq_text, survey_id, rfq_id)
        
        # Step 2: Question-Objective Mapping
        reasoning_chain.append("STEP 2: Mapping survey questions to research objectives")
        question_mappings = await self._map_questions_to_objectives(extract_all_questions(survey), research_objectives)
        
        # Step 3: Coverage Gap Analysis
        reasoning_chain.append("STEP 3: Analyzing coverage gaps and overlaps")
        gap_analysis = await self._perform_gap_analysis(research_objectives, question_mappings)
        
        # Step 4: Multi-Perspective Analysis
        reasoning_chain.append("STEP 4: Evaluating from researcher/respondent/analyst perspectives")
        multi_perspective = await self._multi_perspective_analysis(survey, rfq_text, research_objectives)
        
        # Step 5: Generate Specific Recommendations
        reasoning_chain.append("STEP 5: Generating specific actionable recommendations")
        recommendations = await self._generate_specific_recommendations(gap_analysis, question_mappings, research_objectives)
        
        # Calculate overall score using sophisticated weighting
        overall_score = await self._calculate_advanced_score(research_objectives, question_mappings, gap_analysis, multi_perspective)
        
        # Calculate confidence score based on analysis depth
        confidence_score = self._calculate_confidence_score(research_objectives, question_mappings)
        
        return AdvancedContentValidityResult(
            overall_score=overall_score,
            reasoning_chain=reasoning_chain,
            research_objectives=research_objectives,
            question_mappings=question_mappings,
            gap_analysis=gap_analysis,
            multi_perspective=multi_perspective,
            specific_recommendations=recommendations,
            confidence_score=confidence_score,
            evaluation_metadata={
                "evaluation_timestamp": datetime.now().isoformat(),
                "llm_powered": self.llm_client is not None,
                "rules_context_used": self.pillar_rules_service is not None,
                "objectives_extracted": len(research_objectives),
                "questions_analyzed": len(question_mappings),
                "critical_gaps_found": len(gap_analysis.critical_gaps)
            }
        )
    
    async def _extract_research_objectives(self, rfq_text: str, survey_id: str = None, rfq_id: str = None) -> List[ResearchObjective]:
        """
        Extract research objectives with semantic analysis using advanced LLM reasoning
        """
        
        # Get pillar rules context
        rules_context = ""
        if self.pillar_rules_service:
            rules_context = self.pillar_rules_service.create_pillar_rule_prompt_context("content_validity")
        
        prompt = f"""
        You are an expert research methodologist. Perform semantic analysis to extract ALL research objectives from this RFQ.
        
        PILLAR RULES CONTEXT:
        {rules_context}
        
        RFQ TEXT:
        {rfq_text}
        
        TASK: Extract research objectives using this reasoning process:
        
        1. IDENTIFY EXPLICIT OBJECTIVES: Find clearly stated research goals
        2. IDENTIFY IMPLICIT OBJECTIVES: Infer unstated but implied research needs
        3. CATEGORIZE BY PRIORITY: Primary (critical), Secondary (important), Exploratory (nice-to-have)
        4. SEMANTIC INTENT ANALYSIS: What is the underlying research question?
        5. EXTRACT KEYWORDS: Key terms that questions should address
        
        Respond with JSON:
        {{
            "objectives": [
                {{
                    "text": "Complete research objective statement",
                    "category": "primary|secondary|exploratory", 
                    "priority": 0.9,  // 0.0-1.0 priority score
                    "keywords": ["key", "terms", "to", "address"],
                    "semantic_intent": "What this objective is really trying to understand"
                }}
            ],
            "analysis_confidence": 0.85,  // How confident in this analysis
            "complexity_assessment": "simple|moderate|complex"
        }}
        """
        
        try:
            if self.llm_client:
                # Evaluation prompt is now automatically logged via LLMAuditContext decorator
                
                response = await self.llm_client.analyze(prompt, max_tokens=1500)
                if response.success:
                    result = json.loads(response.content)
                    objectives = []
                    for obj_data in result.get("objectives", []):
                        objectives.append(ResearchObjective(
                            text=obj_data["text"],
                            category=obj_data["category"],
                            priority=obj_data["priority"],
                            keywords=obj_data["keywords"],
                            semantic_intent=obj_data["semantic_intent"]
                        ))
                    return objectives
        except Exception as e:
            print(f"🔴 LLM objective extraction failed: {e}")
        
        # Fallback to basic analysis
        return self._basic_objective_extraction(rfq_text)
    
    async def _map_questions_to_objectives(self, questions: List[Dict], objectives: List[ResearchObjective]) -> List[QuestionMapping]:
        """
        Map each survey question to research objectives with quality assessment
        """
        
        mappings = []
        
        for i, question in enumerate(questions):
            question_text = question.get("text", "")
            question_id = question.get("id", f"q{i+1}")
            
            # Advanced question-objective mapping
            mapping = await self._analyze_question_objective_mapping(question_text, question_id, objectives)
            mappings.append(mapping)
        
        return mappings
    
    async def _analyze_question_objective_mapping(self, question_text: str, question_id: str, objectives: List[ResearchObjective]) -> QuestionMapping:
        """
        Analyze how well a specific question maps to research objectives
        """
        
        objectives_text = "\n".join([f"- {obj.text} (Intent: {obj.semantic_intent})" for obj in objectives])
        
        prompt = f"""
        You are an expert survey methodologist. Analyze how well this question addresses the research objectives.
        
        QUESTION: {question_text}
        
        RESEARCH OBJECTIVES:
        {objectives_text}
        
        ANALYSIS TASK:
        1. Which objectives does this question address? (be specific)
        2. How well does it address each objective? (0.0-1.0 score)
        3. What gaps exist in coverage?
        4. What improvements would make it better?
        
        Respond with JSON:
        {{
            "mapped_objectives": ["objective text that this question addresses"],
            "coverage_quality": 0.75,  // Overall quality score 0.0-1.0
            "objective_scores": {{"objective_text": 0.8}},  // Individual scores
            "gaps_identified": ["specific gaps in coverage"],
            "improvement_suggestions": ["specific ways to improve this question"],
            "reasoning": "Detailed analysis of why this mapping assessment"
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt, max_tokens=800)
                if response.success:
                    result = json.loads(response.content)
                    return QuestionMapping(
                        question_id=question_id,
                        question_text=question_text,
                        mapped_objectives=result.get("mapped_objectives", []),
                        coverage_quality=result.get("coverage_quality", 0.5),
                        gaps_identified=result.get("gaps_identified", []),
                        improvement_suggestions=result.get("improvement_suggestions", [])
                    )
        except Exception as e:
            print(f"🔴 Question mapping analysis failed: {e}")
        
        # Basic fallback mapping
        return QuestionMapping(
            question_id=question_id,
            question_text=question_text,
            mapped_objectives=[],
            coverage_quality=0.5,
            gaps_identified=["Unable to perform detailed analysis"],
            improvement_suggestions=["Consider LLM-powered analysis for detailed insights"]
        )
    
    async def _perform_gap_analysis(self, objectives: List[ResearchObjective], mappings: List[QuestionMapping]) -> GapAnalysis:
        """
        Perform comprehensive gap analysis to identify coverage issues
        """
        
        # Track which objectives are covered
        covered_objectives = set()
        for mapping in mappings:
            covered_objectives.update(mapping.mapped_objectives)
        
        # Identify missing objectives
        missing_objectives = []
        for obj in objectives:
            if obj.text not in covered_objectives:
                missing_objectives.append(obj)
        
        # Identify partially covered (based on coverage quality)
        partially_covered = []
        for mapping in mappings:
            if mapping.coverage_quality < 0.7:  # Threshold for "good" coverage
                for obj in objectives:
                    if obj.text in mapping.mapped_objectives:
                        partially_covered.append((obj, mapping.coverage_quality))
        
        # Identify critical gaps (missing primary objectives)
        critical_gaps = []
        for obj in missing_objectives:
            if obj.category == "primary":
                critical_gaps.append(f"Missing primary objective: {obj.text}")
        
        return GapAnalysis(
            missing_objectives=missing_objectives,
            partially_covered=partially_covered,
            over_covered=[],  # TODO: Implement over-coverage detection
            critical_gaps=critical_gaps,
            impact_assessment={"missing_primary": len([o for o in missing_objectives if o.category == "primary"])}
        )
    
    async def _multi_perspective_analysis(self, survey: Dict, rfq_text: str, objectives: List[ResearchObjective]) -> MultiPerspectiveAnalysis:
        """
        Analyze content validity from multiple stakeholder perspectives
        """
        
        # For now, return a basic multi-perspective structure
        # TODO: Implement full multi-perspective LLM analysis
        
        return MultiPerspectiveAnalysis(
            researcher_view={
                "objectives_coverage": 0.7,
                "methodological_soundness": 0.75,
                "concerns": ["Some primary objectives not fully addressed"]
            },
            respondent_view={
                "clarity_score": 0.8,
                "relevance_score": 0.75,
                "concerns": ["Some questions may seem disconnected from stated purpose"]
            },
            analyst_view={
                "data_quality_potential": 0.8,
                "actionability_score": 0.7,
                "concerns": ["Missing questions for key decision factors"]
            },
            consensus_score=0.75
        )
    
    async def _generate_specific_recommendations(self, gap_analysis: GapAnalysis, mappings: List[QuestionMapping], objectives: List[ResearchObjective]) -> List[Dict[str, Any]]:
        """
        Generate specific, actionable recommendations
        """
        
        recommendations = []
        
        # Recommendations for missing objectives
        for missing_obj in gap_analysis.missing_objectives:
            recommendations.append({
                "type": "add_question",
                "priority": "critical" if missing_obj.category == "primary" else "high",
                "issue": f"Missing coverage for {missing_obj.category} objective",
                "objective": missing_obj.text,
                "suggested_questions": [
                    f"Question addressing: {missing_obj.semantic_intent}"
                ],
                "implementation_notes": f"Focus on keywords: {', '.join(missing_obj.keywords)}",
                "expected_impact": "high" if missing_obj.priority > 0.7 else "medium"
            })
        
        # Recommendations for poor question mappings
        for mapping in mappings:
            if mapping.coverage_quality < 0.6:
                recommendations.append({
                    "type": "improve_question",
                    "priority": "medium",
                    "issue": f"Question '{mapping.question_text[:50]}...' has poor objective coverage",
                    "current_question": mapping.question_text,
                    "improvements": mapping.improvement_suggestions,
                    "expected_impact": "medium"
                })
        
        return recommendations
    
    async def _calculate_advanced_score(self, objectives: List[ResearchObjective], mappings: List[QuestionMapping], gap_analysis: GapAnalysis, multi_perspective: MultiPerspectiveAnalysis) -> float:
        """
        Calculate sophisticated overall score using weighted factors
        """
        
        # Weight factors for different aspects
        OBJECTIVE_COVERAGE_WEIGHT = 0.4
        QUESTION_QUALITY_WEIGHT = 0.3
        GAP_PENALTY_WEIGHT = 0.2
        PERSPECTIVE_CONSENSUS_WEIGHT = 0.1
        
        # Calculate objective coverage score
        total_objectives = len(objectives)
        covered_objectives = total_objectives - len(gap_analysis.missing_objectives)
        coverage_score = covered_objectives / total_objectives if total_objectives > 0 else 0
        
        # Calculate average question quality
        quality_scores = [mapping.coverage_quality for mapping in mappings]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Calculate gap penalty
        critical_gap_penalty = len(gap_analysis.critical_gaps) * 0.15
        gap_score = max(0, 1.0 - critical_gap_penalty)
        
        # Multi-perspective consensus
        consensus_score = multi_perspective.consensus_score
        
        # Weighted final score
        final_score = (
            coverage_score * OBJECTIVE_COVERAGE_WEIGHT +
            avg_quality * QUESTION_QUALITY_WEIGHT +
            gap_score * GAP_PENALTY_WEIGHT +
            consensus_score * PERSPECTIVE_CONSENSUS_WEIGHT
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_confidence_score(self, objectives: List[ResearchObjective], mappings: List[QuestionMapping]) -> float:
        """
        Calculate confidence in the evaluation based on analysis depth
        """
        
        base_confidence = 0.7 if self.llm_client else 0.4
        
        # Higher confidence with more objectives identified
        objective_bonus = min(0.2, len(objectives) * 0.05)
        
        # Higher confidence with detailed mappings
        mapping_bonus = min(0.1, len([m for m in mappings if len(m.improvement_suggestions) > 0]) * 0.02)
        
        return min(1.0, base_confidence + objective_bonus + mapping_bonus)
    
    def _basic_objective_extraction(self, rfq_text: str) -> List[ResearchObjective]:
        """
        Fallback objective extraction using simple heuristics
        """
        
        # Simple pattern matching for common objective indicators
        objective_patterns = [
            r"research goal[s]?[:\s]+([^\.]+)",
            r"objective[s]?[:\s]+([^\.]+)", 
            r"understand[:\s]+([^\.]+)",
            r"determine[:\s]+([^\.]+)",
            r"measure[:\s]+([^\.]+)"
        ]
        
        objectives = []
        for pattern in objective_patterns:
            matches = re.findall(pattern, rfq_text, re.IGNORECASE)
            for match in matches:
                objectives.append(ResearchObjective(
                    text=match.strip(),
                    category="primary",
                    priority=0.7,
                    keywords=match.split()[:3],
                    semantic_intent="Basic pattern-matched objective"
                ))
        
        # If no objectives found, create generic ones
        if not objectives:
            objectives.append(ResearchObjective(
                text="General market research insights",
                category="primary",
                priority=0.5,
                keywords=["market", "research", "insights"],
                semantic_intent="Fallback objective"
            ))
        
        return objectives
    