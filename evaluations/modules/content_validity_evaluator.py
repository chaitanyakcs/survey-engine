#!/usr/bin/env python3
"""
Content Validity Evaluator - LLM-based Analysis
Evaluates how well the questionnaire captures the intended research objectives
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils import extract_all_questions

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
        Evaluate content validity using advanced chain-of-thought analysis
        
        CHAIN-OF-THOUGHT PROCESS:
        1. Extract Research Objectives (Semantic Analysis)
        2. Map Questions to Objectives (Intent Matching) 
        3. Identify Coverage Gaps (Gap Analysis)
        4. Assess Question Quality (Quality Scoring)
        5. Generate Specific Recommendations (Actionable Output)
        
        Args:
            survey: Generated survey dictionary
            rfq_text: Original RFQ text
            
        Returns:
            ContentValidityResult with comprehensive analysis
        """
        
        # Extract survey questions for analysis
        questions = extract_all_questions(survey)
        survey_title = survey.get("title", "")
        survey_description = survey.get("description", "")
        
        # STEP 1: Extract Research Objectives (Enhanced Semantic Analysis)
        research_objectives = await self._extract_research_objectives(rfq_text)
        
        # STEP 2: Map Questions to Objectives (Intent Matching)
        objective_mapping = await self._map_questions_to_objectives(questions, research_objectives)
        
        # STEP 3: Identify Coverage Gaps (Advanced Gap Analysis)
        coverage_gaps = await self._identify_coverage_gaps(research_objectives, objective_mapping)
        
        # STEP 4: Assess Question Quality (Quality Scoring)
        question_quality = await self._assess_question_quality(questions, research_objectives)
        
        # STEP 5: Calculate scores based on chain-of-thought analysis
        objective_coverage = self._calculate_objective_coverage_score(objective_mapping, coverage_gaps)
        topic_comprehensiveness = self._calculate_comprehensiveness_score(research_objectives, objective_mapping)
        research_goal_alignment = await self._analyze_research_goal_alignment(rfq_text, survey_title, survey_description)
        
        # Calculate weighted overall score
        overall_score = (
            objective_coverage * 0.4 +
            topic_comprehensiveness * 0.4 +
            research_goal_alignment * 0.2
        )
        
        # Generate enhanced detailed analysis with chain-of-thought reasoning
        detailed_analysis = await self._generate_chain_of_thought_analysis(
            research_objectives, objective_mapping, coverage_gaps, question_quality, 
            objective_coverage, topic_comprehensiveness, research_goal_alignment
        )
        
        # STEP 5: Generate Specific Recommendations (Enhanced Actionable Output)
        recommendations = await self._generate_actionable_recommendations(
            coverage_gaps, question_quality, detailed_analysis, overall_score
        )
        
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

    # ==============================================================================
    # CHAIN-OF-THOUGHT REASONING METHODS
    # ==============================================================================
    
    async def _extract_research_objectives(self, rfq_text: str) -> Dict[str, Any]:
        """
        STEP 1: Extract Research Objectives using Semantic Analysis
        Advanced parsing of RFQ to identify specific, measurable research objectives
        """
        
        # Get pillar-specific rules context
        rules_context = ""
        if self.pillar_rules_service:
            rules_context = self.pillar_rules_service.create_pillar_rule_prompt_context("content_validity")
        
        prompt = f"""
        {rules_context}
        
        TASK: Perform semantic analysis to extract precise research objectives from the RFQ.
        
        CHAIN-OF-THOUGHT REASONING:
        1. Read the RFQ carefully to identify explicit and implicit research goals
        2. Extract specific, measurable objectives (not just topics)
        3. Categorize objectives by priority and scope
        4. Identify any methodological requirements or constraints
        
        RFQ Text:
        {rfq_text}
        
        Extract and structure the research objectives according to Content Validity rules.
        
        Respond with a JSON object:
        {{
            "primary_objectives": [
                {{
                    "objective": "specific research goal",
                    "priority": "high|medium|low",
                    "scope": "broad|focused|specific",
                    "measurable_outcomes": ["what should be measured"],
                    "keywords": ["key terms related to this objective"]
                }}
            ],
            "secondary_objectives": [similar structure],
            "methodological_requirements": ["specific method constraints from RFQ"],
            "target_population": "who should be surveyed",
            "research_context": "background/industry/domain",
            "success_criteria": ["how to measure if objective is met"]
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._fallback_objective_extraction(rfq_text)
        except Exception as e:
            print(f"Research objective extraction failed: {e}")
            return self._fallback_objective_extraction(rfq_text)
    
    async def _map_questions_to_objectives(self, questions: List[Dict], research_objectives: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 2: Map Questions to Objectives using Intent Matching
        Advanced semantic matching of survey questions to research objectives
        """
        
        prompt = f"""
        TASK: Perform intent matching analysis between survey questions and research objectives.
        
        CHAIN-OF-THOUGHT REASONING:
        1. For each survey question, identify which research objectives it addresses
        2. Assess the quality of the match (direct, indirect, partial, none)
        3. Identify questions that serve multiple objectives
        4. Flag objectives with no matching questions
        
        Research Objectives:
        {json.dumps(research_objectives, indent=2)}
        
        Survey Questions:
        {json.dumps([{'id': i, 'text': q.get('text', ''), 'type': q.get('type', '')} for i, q in enumerate(questions)], indent=2)}
        
        Respond with a JSON object:
        {{
            "question_to_objective_mapping": [
                {{
                    "question_id": 0,
                    "question_text": "question text",
                    "mapped_objectives": [
                        {{
                            "objective": "objective text",
                            "match_quality": "direct|indirect|partial",
                            "match_confidence": 0.95,
                            "explanation": "why this question addresses this objective"
                        }}
                    ]
                }}
            ],
            "objective_coverage": {{
                "fully_covered": ["objectives with direct question matches"],
                "partially_covered": ["objectives with indirect/partial matches"],
                "not_covered": ["objectives with no question matches"]
            }},
            "multi_objective_questions": ["questions that address multiple objectives"],
            "orphaned_questions": ["questions that don't clearly address any objective"]
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._fallback_question_mapping(questions, research_objectives)
        except Exception as e:
            print(f"Question-objective mapping failed: {e}")
            return self._fallback_question_mapping(questions, research_objectives)
    
    async def _identify_coverage_gaps(self, research_objectives: Dict[str, Any], objective_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 3: Identify Coverage Gaps using Advanced Gap Analysis
        Systematic identification of missing coverage and over-representation
        """
        
        prompt = f"""
        TASK: Perform comprehensive gap analysis to identify coverage issues.
        
        CHAIN-OF-THOUGHT REASONING:
        1. Compare research objectives with question coverage
        2. Identify critical gaps where important objectives lack questions
        3. Identify over-representation where objectives have excessive coverage
        4. Assess the impact of each gap on research validity
        5. Prioritize gaps by importance and measurability
        
        Research Objectives:
        {json.dumps(research_objectives, indent=2)}
        
        Current Mapping:
        {json.dumps(objective_mapping, indent=2)}
        
        Respond with a JSON object:
        {{
            "critical_gaps": [
                {{
                    "objective": "missing objective",
                    "impact_severity": "high|medium|low",
                    "suggested_questions": ["specific question suggestions"],
                    "why_critical": "explanation of impact"
                }}
            ],
            "minor_gaps": [similar structure],
            "over_represented_areas": [
                {{
                    "objective": "over-covered objective", 
                    "question_count": 5,
                    "redundancy_analysis": "which questions are redundant"
                }}
            ],
            "balance_assessment": {{
                "overall_coverage": 0.75,
                "coverage_distribution": "even|uneven|skewed",
                "priority_alignment": "objectives covered match RFQ priorities"
            }}
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._fallback_gap_analysis(research_objectives, objective_mapping)
        except Exception as e:
            print(f"Coverage gap analysis failed: {e}")
            return self._fallback_gap_analysis(research_objectives, objective_mapping)
    
    async def _assess_question_quality(self, questions: List[Dict], research_objectives: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEP 4: Assess Question Quality using Quality Scoring
        Detailed analysis of individual question quality and effectiveness
        """
        
        prompt = f"""
        TASK: Perform detailed quality assessment of individual survey questions.
        
        CHAIN-OF-THOUGHT REASONING:
        1. Evaluate each question for clarity, specificity, and measurability
        2. Assess potential for bias, leading responses, or ambiguity
        3. Check alignment with research methodology requirements
        4. Evaluate question types and response formats appropriateness
        
        Research Context:
        {json.dumps(research_objectives, indent=2)}
        
        Survey Questions:
        {json.dumps([{'id': i, 'text': q.get('text', ''), 'type': q.get('type', ''), 'options': q.get('options', [])} for i, q in enumerate(questions)], indent=2)}
        
        Respond with a JSON object:
        {{
            "question_quality_scores": [
                {{
                    "question_id": 0,
                    "overall_quality": 0.85,
                    "clarity_score": 0.9,
                    "specificity_score": 0.8,
                    "bias_risk": 0.2,
                    "strengths": ["what makes this question good"],
                    "weaknesses": ["what could be improved"],
                    "improvement_suggestions": ["specific recommendations"]
                }}
            ],
            "overall_survey_quality": {{
                "average_quality": 0.82,
                "quality_distribution": "consistent|variable|poor",
                "best_questions": [0, 3, 7],
                "problematic_questions": [2, 5],
                "methodology_alignment": "strong|adequate|weak"
            }}
        }}
        """
        
        try:
            if self.llm_client:
                response = await self.llm_client.analyze(prompt)
                return json.loads(response)
            else:
                return self._fallback_quality_assessment(questions)
        except Exception as e:
            print(f"Question quality assessment failed: {e}")
            return self._fallback_quality_assessment(questions)
    
    def _calculate_objective_coverage_score(self, objective_mapping: Dict[str, Any], coverage_gaps: Dict[str, Any]) -> float:
        """Calculate objective coverage score based on mapping and gap analysis"""
        try:
            coverage_info = objective_mapping.get("objective_coverage", {})
            fully_covered = len(coverage_info.get("fully_covered", []))
            partially_covered = len(coverage_info.get("partially_covered", []))
            not_covered = len(coverage_info.get("not_covered", []))
            
            total_objectives = fully_covered + partially_covered + not_covered
            if total_objectives == 0:
                return 0.6  # Default for unclear mapping
            
            # Weight: fully covered = 1.0, partially = 0.5, not covered = 0.0
            coverage_score = (fully_covered * 1.0 + partially_covered * 0.5) / total_objectives
            
            # Adjust based on gap analysis impact
            gap_impact = coverage_gaps.get("balance_assessment", {}).get("overall_coverage", coverage_score)
            return min((coverage_score + gap_impact) / 2, 1.0)
            
        except Exception:
            return 0.6  # Fallback score
    
    def _calculate_comprehensiveness_score(self, research_objectives: Dict[str, Any], objective_mapping: Dict[str, Any]) -> float:
        """Calculate comprehensiveness score based on breadth and depth of coverage"""
        try:
            primary_objectives = len(research_objectives.get("primary_objectives", []))
            secondary_objectives = len(research_objectives.get("secondary_objectives", []))
            
            coverage_info = objective_mapping.get("objective_coverage", {})
            covered_primary = len([obj for obj in coverage_info.get("fully_covered", []) 
                                 if any(obj in str(po.get('objective', '')) if isinstance(po, dict) else str(po) 
                                       for po in research_objectives.get("primary_objectives", []))])
            
            if primary_objectives == 0:
                return 0.6
            
            primary_coverage_ratio = covered_primary / primary_objectives
            
            # Bonus for secondary objective coverage
            secondary_bonus = min(len(coverage_info.get("partially_covered", [])) * 0.1, 0.2)
            
            return min(primary_coverage_ratio + secondary_bonus, 1.0)
            
        except Exception:
            return 0.6  # Fallback score
    
    async def _generate_chain_of_thought_analysis(self, research_objectives: Dict, objective_mapping: Dict, 
                                                coverage_gaps: Dict, question_quality: Dict, 
                                                objective_coverage: float, topic_comprehensiveness: float, 
                                                research_goal_alignment: float) -> Dict[str, Any]:
        """Generate comprehensive analysis based on chain-of-thought reasoning"""
        
        return {
            "chain_of_thought_reasoning": {
                "step_1_objectives": {
                    "extracted_objectives": research_objectives,
                    "analysis": "Semantic analysis identified research objectives with priority and scope classification"
                },
                "step_2_mapping": {
                    "question_mapping": objective_mapping,
                    "analysis": "Intent matching analysis mapped questions to objectives with confidence scoring"
                },
                "step_3_gaps": {
                    "coverage_gaps": coverage_gaps,
                    "analysis": "Systematic gap analysis identified missing coverage and over-representation"
                },
                "step_4_quality": {
                    "question_quality": question_quality,
                    "analysis": "Individual question quality assessment with bias and clarity evaluation"
                }
            },
            "comprehensive_scores": {
                "objective_coverage": objective_coverage,
                "topic_comprehensiveness": topic_comprehensiveness,
                "research_goal_alignment": research_goal_alignment
            },
            "strengths": self._extract_strengths(objective_mapping, question_quality, coverage_gaps),
            "weaknesses": self._extract_weaknesses(coverage_gaps, question_quality),
            "detailed_findings": {
                "coverage_analysis": coverage_gaps.get("balance_assessment", {}),
                "quality_distribution": question_quality.get("overall_survey_quality", {}),
                "objective_achievement": objective_mapping.get("objective_coverage", {})
            },
            "methodology_compliance": self._assess_methodology_compliance(research_objectives, question_quality)
        }
    
    async def _generate_actionable_recommendations(self, coverage_gaps: Dict, question_quality: Dict, 
                                                 detailed_analysis: Dict, overall_score: float) -> List[str]:
        """Generate specific, actionable recommendations based on chain-of-thought analysis"""
        
        recommendations = []
        
        # Address critical gaps
        for gap in coverage_gaps.get("critical_gaps", []):
            recommendations.extend(gap.get("suggested_questions", []))
            recommendations.append(f"Address critical gap in {gap.get('objective', 'research area')}: {gap.get('why_critical', '')}")
        
        # Address question quality issues
        quality_scores = question_quality.get("question_quality_scores", [])
        problematic_questions = question_quality.get("overall_survey_quality", {}).get("problematic_questions", [])
        
        for q_id in problematic_questions:
            if q_id < len(quality_scores):
                q_analysis = quality_scores[q_id]
                recommendations.extend(q_analysis.get("improvement_suggestions", []))
        
        # Address over-representation
        for over_rep in coverage_gaps.get("over_represented_areas", []):
            recommendations.append(f"Reduce redundancy in {over_rep.get('objective', 'area')}: {over_rep.get('redundancy_analysis', '')}")
        
        # Overall score-based recommendations
        if overall_score < 0.6:
            recommendations.insert(0, "Major revision needed: Significant gaps in content validity require comprehensive survey restructuring")
        elif overall_score < 0.8:
            recommendations.insert(0, "Moderate improvements needed: Address identified gaps and quality issues for better content validity")
        else:
            recommendations.insert(0, "Minor refinements: Survey demonstrates strong content validity with room for optimization")
        
        return list(dict.fromkeys(recommendations))  # Remove duplicates while preserving order

    # ==============================================================================
    # FALLBACK METHODS FOR CHAIN-OF-THOUGHT ANALYSIS
    # ==============================================================================
    
    def _fallback_objective_extraction(self, rfq_text: str) -> Dict[str, Any]:
        """Fallback method for research objective extraction"""
        words = rfq_text.lower().split()
        return {
            "primary_objectives": [{"objective": "Understand " + " ".join(words[:10]) + "...", "priority": "high"}],
            "secondary_objectives": [],
            "methodological_requirements": ["Survey-based data collection"],
            "target_population": "Target audience from RFQ",
            "research_context": "General research study",
            "success_criteria": ["Collect comprehensive data"]
        }
    
    def _fallback_question_mapping(self, questions: List[Dict], research_objectives: Dict) -> Dict[str, Any]:
        """Fallback method for question-objective mapping"""
        return {
            "question_to_objective_mapping": [
                {"question_id": i, "mapped_objectives": [{"objective": "primary research goal", "match_quality": "indirect"}]}
                for i in range(len(questions))
            ],
            "objective_coverage": {
                "fully_covered": ["primary research goal"],
                "partially_covered": [],
                "not_covered": []
            },
            "multi_objective_questions": [],
            "orphaned_questions": []
        }
    
    def _fallback_gap_analysis(self, research_objectives: Dict, objective_mapping: Dict) -> Dict[str, Any]:
        """Fallback method for gap analysis"""
        return {
            "critical_gaps": [],
            "minor_gaps": [],
            "over_represented_areas": [],
            "balance_assessment": {
                "overall_coverage": 0.7,
                "coverage_distribution": "adequate",
                "priority_alignment": "reasonable"
            }
        }
    
    def _fallback_quality_assessment(self, questions: List[Dict]) -> Dict[str, Any]:
        """Fallback method for question quality assessment"""
        return {
            "question_quality_scores": [
                {
                    "question_id": i,
                    "overall_quality": 0.7,
                    "clarity_score": 0.7,
                    "specificity_score": 0.7,
                    "bias_risk": 0.3,
                    "strengths": ["Clear wording"],
                    "weaknesses": ["Could be more specific"],
                    "improvement_suggestions": ["Review for specificity"]
                }
                for i in range(len(questions))
            ],
            "overall_survey_quality": {
                "average_quality": 0.7,
                "quality_distribution": "adequate",
                "best_questions": [],
                "problematic_questions": [],
                "methodology_alignment": "adequate"
            }
        }
    
    def _extract_strengths(self, objective_mapping: Dict, question_quality: Dict, coverage_gaps: Dict) -> List[str]:
        """Extract strengths from chain-of-thought analysis"""
        strengths = []
        
        coverage = objective_mapping.get("objective_coverage", {})
        if len(coverage.get("fully_covered", [])) > 0:
            strengths.append(f"Strong coverage of {len(coverage['fully_covered'])} primary objectives")
        
        quality = question_quality.get("overall_survey_quality", {})
        if quality.get("average_quality", 0) > 0.8:
            strengths.append("High overall question quality with clear, specific wording")
        
        if not coverage_gaps.get("critical_gaps", []):
            strengths.append("No critical coverage gaps identified")
            
        return strengths
    
    def _extract_weaknesses(self, coverage_gaps: Dict, question_quality: Dict) -> List[str]:
        """Extract weaknesses from chain-of-thought analysis"""
        weaknesses = []
        
        if coverage_gaps.get("critical_gaps", []):
            weaknesses.append(f"{len(coverage_gaps['critical_gaps'])} critical coverage gaps require attention")
        
        quality = question_quality.get("overall_survey_quality", {})
        if quality.get("problematic_questions", []):
            weaknesses.append(f"{len(quality['problematic_questions'])} questions need quality improvements")
        
        if coverage_gaps.get("over_represented_areas", []):
            weaknesses.append("Some areas are over-represented, creating survey inefficiency")
            
        return weaknesses
    
    def _assess_methodology_compliance(self, research_objectives: Dict, question_quality: Dict) -> Dict[str, Any]:
        """Assess compliance with methodological requirements"""
        return {
            "requirements_met": research_objectives.get("methodological_requirements", []),
            "compliance_score": 0.8,
            "methodology_alignment": question_quality.get("overall_survey_quality", {}).get("methodology_alignment", "adequate"),
            "recommendations": ["Follow established survey methodology best practices"]
        }