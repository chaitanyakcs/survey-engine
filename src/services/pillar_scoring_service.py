#!/usr/bin/env python3
"""
Pillar Scoring Service
Evaluates survey adherence to the 5-pillar evaluation framework
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from src.utils.survey_utils import extract_all_questions, get_questions_count

logger = logging.getLogger(__name__)

@dataclass
class PillarScore:
    """Individual pillar score with details"""
    pillar_name: str
    score: float  # 0.0 to 1.0
    max_score: float
    weight: float
    weighted_score: float
    criteria_met: int
    total_criteria: int
    details: List[str]
    recommendations: List[str]

@dataclass
class OverallPillarScore:
    """Overall pillar adherence score"""
    total_score: float  # 0.0 to 1.0
    weighted_score: float  # 0.0 to 1.0
    pillar_scores: List[PillarScore]
    overall_grade: str  # A, B, C, D, F
    summary: str

class PillarScoringService:
    """Service for evaluating survey adherence to pillar rules"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.pillar_weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }
    
    def evaluate_survey_pillars(self, survey_data: Dict[str, Any]) -> OverallPillarScore:
        """
        Evaluate survey against all 5 pillars
        
        Args:
            survey_data: The generated survey JSON data
            
        Returns:
            OverallPillarScore with detailed breakdown
        """
        logger.info("🏛️ [PillarScoring] Starting pillar evaluation for survey")
        logger.info(f"🏛️ [PillarScoring] Survey data keys: {list(survey_data.keys()) if survey_data else 'None'}")
        logger.info(f"🏛️ [PillarScoring] Survey questions count: {get_questions_count(survey_data) if survey_data else 0}")
        
        pillar_scores = []
        total_weighted_score = 0.0
        
        # Evaluate each pillar
        for pillar_name, weight in self.pillar_weights.items():
            logger.info(f"🏛️ [PillarScoring] Evaluating pillar: {pillar_name} (weight: {weight:.1%})")
            pillar_score = self._evaluate_pillar(survey_data, pillar_name, weight)
            pillar_scores.append(pillar_score)
            total_weighted_score += pillar_score.weighted_score
            logger.info(f"🏛️ [PillarScoring] {pillar_name} score: {pillar_score.score:.1%} (grade: {pillar_score.criteria_met}/{pillar_score.total_criteria})")
        
        # Calculate overall metrics
        total_score = sum(score.score for score in pillar_scores) / len(pillar_scores)
        overall_grade = self._calculate_grade(total_weighted_score)
        summary = self._generate_summary(pillar_scores, total_weighted_score)
        
        result = OverallPillarScore(
            total_score=total_score,
            weighted_score=total_weighted_score,
            pillar_scores=pillar_scores,
            overall_grade=overall_grade,
            summary=summary
        )
        
        logger.info(f"✅ [PillarScoring] Pillar evaluation complete: {overall_grade} ({total_weighted_score:.2f})")
        logger.info(f"✅ [PillarScoring] Total score: {total_score:.2f}, Weighted score: {total_weighted_score:.2f}")
        logger.info(f"✅ [PillarScoring] Summary: {summary}")
        return result
    
    def _evaluate_pillar(self, survey_data: Dict[str, Any], pillar_name: str, weight: float) -> PillarScore:
        """Evaluate a specific pillar"""
        logger.info(f"🏛️ [PillarScoring] Evaluating pillar: {pillar_name}")
        
        # Get pillar rules from database
        pillar_rules = self._get_pillar_rules(pillar_name)
        logger.info(f"🏛️ [PillarScoring] Found {len(pillar_rules)} rules for {pillar_name}")
        
        if not pillar_rules:
            logger.warning(f"⚠️ [PillarScoring] No rules found for pillar: {pillar_name}")
            return PillarScore(
                pillar_name=pillar_name,
                score=0.0,
                max_score=1.0,
                weight=weight,
                weighted_score=0.0,
                criteria_met=0,
                total_criteria=0,
                details=["No rules available for evaluation"],
                recommendations=["Add pillar rules to enable evaluation"]
            )
        
        # Evaluate against each rule
        criteria_met = 0
        total_criteria = len(pillar_rules)
        details = []
        recommendations = []
        
        logger.info(f"🏛️ [PillarScoring] Evaluating {total_criteria} rules for {pillar_name}")
        
        for i, rule in enumerate(pillar_rules):
            logger.info(f"🏛️ [PillarScoring] Rule {i+1}/{total_criteria}: {rule['description'][:50]}...")
            rule_evaluation = self._evaluate_rule(survey_data, rule, pillar_name)
            if rule_evaluation['met']:
                criteria_met += 1
                details.append(f"✅ {rule['description']}")
                logger.info(f"🏛️ [PillarScoring] Rule {i+1} PASSED")
            else:
                details.append(f"❌ {rule['description']}")
                recommendations.extend(rule_evaluation.get('recommendations', []))
                logger.info(f"🏛️ [PillarScoring] Rule {i+1} FAILED: {rule_evaluation.get('reason', 'No reason provided')}")
        
        # Calculate scores
        score = criteria_met / total_criteria if total_criteria > 0 else 0.0
        weighted_score = score * weight
        
        logger.info(f"🏛️ [PillarScoring] {pillar_name} evaluation complete: {criteria_met}/{total_criteria} criteria met ({score:.1%})")
        
        return PillarScore(
            pillar_name=pillar_name,
            score=score,
            max_score=1.0,
            weight=weight,
            weighted_score=weighted_score,
            criteria_met=criteria_met,
            total_criteria=total_criteria,
            details=details,
            recommendations=recommendations
        )
    
    def _get_pillar_rules(self, pillar_name: str) -> List[Dict[str, Any]]:
        """Get rules for a specific pillar from database"""
        try:
            from src.database.models import SurveyRule
            
            rules = self.db_session.query(SurveyRule).filter(
                SurveyRule.rule_type == 'pillar',
                SurveyRule.category == pillar_name,
                SurveyRule.is_active == True
            ).all()
            
            return [
                {
                    'id': str(rule.id),
                    'description': rule.rule_description,
                    'priority': rule.rule_content.get('priority', 'medium') if rule.rule_content else 'medium',
                    'evaluation_criteria': rule.rule_content.get('evaluation_criteria', []) if rule.rule_content else []
                }
                for rule in rules
            ]
        except Exception as e:
            logger.error(f"Error fetching pillar rules for {pillar_name}: {e}")
            return []
    
    def _evaluate_rule(self, survey_data: Dict[str, Any], rule: Dict[str, Any], pillar_name: str) -> Dict[str, Any]:
        """Evaluate a specific rule against the survey data"""
        
        rule_description = rule['description'].lower()
        recommendations = []
        
        # Content Validity evaluation
        if pillar_name == 'content_validity':
            return self._evaluate_content_validity(survey_data, rule_description, recommendations)
        
        # Methodological Rigor evaluation
        elif pillar_name == 'methodological_rigor':
            return self._evaluate_methodological_rigor(survey_data, rule_description, recommendations)
        
        # Clarity & Comprehensibility evaluation
        elif pillar_name == 'clarity_comprehensibility':
            return self._evaluate_clarity_comprehensibility(survey_data, rule_description, recommendations)
        
        # Structural Coherence evaluation
        elif pillar_name == 'structural_coherence':
            return self._evaluate_structural_coherence(survey_data, rule_description, recommendations)
        
        # Deployment Readiness evaluation
        elif pillar_name == 'deployment_readiness':
            return self._evaluate_deployment_readiness(survey_data, rule_description, recommendations)
        
        else:
            return {'met': False, 'recommendations': ['Unknown pillar type']}
    
    def _evaluate_content_validity(self, survey_data: Dict[str, Any], rule_description: str, recommendations: List[str]) -> Dict[str, Any]:
        """Evaluate content validity rules"""
        questions = extract_all_questions(survey_data)
        
        if 'research objective' in rule_description:
            # Check if questions address research objectives
            has_objective_questions = any(
                'objective' in q.get('text', '').lower() or 
                'goal' in q.get('text', '').lower() or
                'purpose' in q.get('text', '').lower()
                for q in questions
            )
            if not has_objective_questions:
                recommendations.append("Add questions that directly address research objectives")
            return {'met': has_objective_questions, 'recommendations': recommendations}
        
        elif 'comprehensive coverage' in rule_description:
            # Check for comprehensive question coverage
            question_types = set(q.get('type', '') for q in questions)
            has_variety = len(question_types) >= 3
            if not has_variety:
                recommendations.append("Include more variety in question types for comprehensive coverage")
            return {'met': has_variety, 'recommendations': recommendations}
        
        elif 'business objective' in rule_description:
            # Check for business objective alignment
            has_business_focus = any(
                'business' in q.get('text', '').lower() or
                'customer' in q.get('text', '').lower() or
                'satisfaction' in q.get('text', '').lower()
                for q in questions
            )
            if not has_business_focus:
                recommendations.append("Include questions that translate business objectives into measurable constructs")
            return {'met': has_business_focus, 'recommendations': recommendations}
        
        return {'met': True, 'recommendations': recommendations}
    
    def _evaluate_methodological_rigor(self, survey_data: Dict[str, Any], rule_description: str, recommendations: List[str]) -> Dict[str, Any]:
        """Evaluate methodological rigor rules"""
        questions = extract_all_questions(survey_data)
        
        if 'leading' in rule_description or 'loaded' in rule_description:
            # Check for leading questions
            has_leading_questions = any(
                any(bias_word in q.get('text', '').lower() for bias_word in [
                    'don\'t you think', 'wouldn\'t you agree', 'isn\'t it true', 'obviously'
                ])
                for q in questions
            )
            if has_leading_questions:
                recommendations.append("Remove leading or loaded language from questions")
            return {'met': not has_leading_questions, 'recommendations': recommendations}
        
        elif 'logical sequence' in rule_description:
            # Check question flow
            has_flow = len(questions) > 0
            if not has_flow:
                recommendations.append("Ensure questions follow logical sequence from general to specific")
            return {'met': has_flow, 'recommendations': recommendations}
        
        elif 'screening' in rule_description:
            # Check for screening questions
            has_screening = any(
                'screening' in q.get('text', '').lower() or
                'qualify' in q.get('text', '').lower() or
                'eligible' in q.get('text', '').lower()
                for q in questions
            )
            if not has_screening:
                recommendations.append("Include screening questions early in the survey")
            return {'met': has_screening, 'recommendations': recommendations}
        
        return {'met': True, 'recommendations': recommendations}
    
    def _evaluate_clarity_comprehensibility(self, survey_data: Dict[str, Any], rule_description: str, recommendations: List[str]) -> Dict[str, Any]:
        """Evaluate clarity and comprehensibility rules"""
        questions = extract_all_questions(survey_data)
        
        if 'jargon' in rule_description or 'technical' in rule_description:
            # Check for jargon
            has_jargon = any(
                any(tech_word in q.get('text', '').lower() for tech_word in [
                    'algorithm', 'api', 'database', 'infrastructure', 'optimization'
                ])
                for q in questions
            )
            if has_jargon:
                recommendations.append("Replace technical jargon with simple, clear language")
            return {'met': not has_jargon, 'recommendations': recommendations}
        
        elif 'single concept' in rule_description:
            # Check for single-concept questions
            has_double_barreled = any(
                ' and ' in q.get('text', '') and '?' in q.get('text', '')
                for q in questions
            )
            if has_double_barreled:
                recommendations.append("Split double-barreled questions into single-concept questions")
            return {'met': not has_double_barreled, 'recommendations': recommendations}
        
        elif 'neutral' in rule_description or 'unambiguous' in rule_description:
            # Check for neutral wording
            has_biased_wording = any(
                any(bias_word in q.get('text', '').lower() for bias_word in [
                    'excellent', 'poor', 'terrible', 'amazing', 'awful'
                ])
                for q in questions
            )
            if has_biased_wording:
                recommendations.append("Use neutral, unambiguous language in questions")
            return {'met': not has_biased_wording, 'recommendations': recommendations}
        
        return {'met': True, 'recommendations': recommendations}
    
    def _evaluate_structural_coherence(self, survey_data: Dict[str, Any], rule_description: str, recommendations: List[str]) -> Dict[str, Any]:
        """Evaluate structural coherence rules"""
        questions = extract_all_questions(survey_data)
        
        if 'logical progression' in rule_description:
            # Check for logical flow
            has_sections = 'sections' in survey_data or len(questions) > 0
            if not has_sections:
                recommendations.append("Organize questions into logical sections with clear progression")
            return {'met': has_sections, 'recommendations': recommendations}
        
        elif 'grouped together' in rule_description:
            # Check for question grouping
            has_grouping = len(questions) > 0  # Basic check
            if not has_grouping:
                recommendations.append("Group related questions together")
            return {'met': has_grouping, 'recommendations': recommendations}
        
        elif 'consistent' in rule_description and 'scale' in rule_description:
            # Check for consistent response scales
            response_types = set()
            for q in questions:
                if 'options' in q:
                    response_types.add('multiple_choice')
                elif 'scale' in q.get('text', '').lower():
                    response_types.add('scale')
            
            has_consistency = len(response_types) <= 2  # Allow some variety
            if not has_consistency:
                recommendations.append("Use consistent response scales within question groups")
            return {'met': has_consistency, 'recommendations': recommendations}
        
        return {'met': True, 'recommendations': recommendations}
    
    def _evaluate_deployment_readiness(self, survey_data: Dict[str, Any], rule_description: str, recommendations: List[str]) -> Dict[str, Any]:
        """Evaluate deployment readiness rules"""
        questions = extract_all_questions(survey_data)
        
        if 'appropriate length' in rule_description:
            # Check survey length
            question_count = len(questions)
            is_appropriate_length = 5 <= question_count <= 25
            if not is_appropriate_length:
                recommendations.append(f"Adjust survey length (current: {question_count} questions, recommended: 5-25)")
            return {'met': is_appropriate_length, 'recommendations': recommendations}
        
        elif 'realistic' in rule_description and 'sample' in rule_description:
            # Check for realistic sample size considerations
            has_sample_info = any(
                'sample' in q.get('text', '').lower() or
                'respondents' in q.get('text', '').lower()
                for q in questions
            )
            if not has_sample_info:
                recommendations.append("Consider sample size requirements in survey design")
            return {'met': has_sample_info, 'recommendations': recommendations}
        
        elif 'compliance' in rule_description or 'privacy' in rule_description:
            # Check for compliance considerations
            has_compliance = any(
                'privacy' in q.get('text', '').lower() or
                'consent' in q.get('text', '').lower() or
                'confidential' in q.get('text', '').lower()
                for q in questions
            )
            if not has_compliance:
                recommendations.append("Include privacy and compliance considerations")
            return {'met': has_compliance, 'recommendations': recommendations}
        
        return {'met': True, 'recommendations': recommendations}
    
    def _calculate_grade(self, weighted_score: float) -> str:
        """Calculate letter grade based on weighted score"""
        if weighted_score >= 0.9:
            return "A"
        elif weighted_score >= 0.8:
            return "B"
        elif weighted_score >= 0.7:
            return "C"
        elif weighted_score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_summary(self, pillar_scores: List[PillarScore], total_weighted_score: float) -> str:
        """Generate summary of pillar evaluation"""
        grade = self._calculate_grade(total_weighted_score)
        
        # Find strongest and weakest pillars
        strongest = max(pillar_scores, key=lambda x: x.score)
        weakest = min(pillar_scores, key=lambda x: x.score)
        
        summary_parts = [
            f"Overall Pillar Adherence: {grade} ({total_weighted_score:.1%})",
            f"Strongest Pillar: {strongest.pillar_name.replace('_', ' ').title()} ({strongest.score:.1%})",
            f"Weakest Pillar: {weakest.pillar_name.replace('_', ' ').title()} ({weakest.score:.1%})"
        ]
        
        if total_weighted_score < 0.7:
            summary_parts.append("Recommendation: Focus on improving weakest pillars for better survey quality")
        
        return " | ".join(summary_parts)
