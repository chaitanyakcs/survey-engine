#!/usr/bin/env python3
"""
Pillar Rules Integration
Extends the existing rules system to support 5-pillar evaluation framework
"""

from typing import Dict, List, Any, Optional
import json

# Define pillar-based rule categories
PILLAR_RULE_CATEGORIES = {
    "content_validity": {
        "name": "Content Validity Rules",
        "description": "Rules for evaluating how well the questionnaire captures intended research objectives",
        "weight": 0.20,
        "default_rules": [
            "Survey questions must directly address all stated research objectives from the RFQ",
            "Each key research area mentioned in the RFQ should have corresponding questions",
            "Question coverage should be comprehensive without significant gaps in topic areas",
            "Survey scope should align with the research goals and target audience specified",
            "Questions should demonstrate clear mapping to business objectives or research hypotheses"
        ]
    },
    "methodological_rigor": {
        "name": "Methodological Rigor Rules", 
        "description": "Rules for evaluating adherence to market research best practices and bias avoidance",
        "weight": 0.25,
        "default_rules": [
            "Questions must follow logical sequence from general to specific",
            "Avoid leading, loaded, or double-barreled questions that introduce bias",
            "Screening questions should appear early in the survey flow",
            "Sensitive or personal questions should be placed toward the end",
            "Question types must be appropriate for the methodology being implemented",
            "Sample size and targeting must align with statistical requirements",
            "Include proper randomization and bias mitigation techniques where applicable"
        ]
    },
    "clarity_comprehensibility": {
        "name": "Clarity & Comprehensibility Rules",
        "description": "Rules for ensuring language accessibility and question wording effectiveness", 
        "weight": 0.25,
        "default_rules": [
            "Use clear, simple language appropriate for the target audience",
            "Avoid jargon, technical terms, and industry-specific language unless necessary",
            "Each question should focus on a single concept or idea",
            "Question wording should be neutral and unambiguous",
            "Instructions and context should be clear and easy to understand",
            "Reading level should be appropriate for the target demographic",
            "Use inclusive language that avoids cultural bias or assumptions"
        ]
    },
    "structural_coherence": {
        "name": "Structural Coherence Rules",
        "description": "Rules for evaluating logical flow and appropriate question organization",
        "weight": 0.20, 
        "default_rules": [
            "Survey sections should follow logical progression and organization",
            "Related questions should be grouped together appropriately",
            "Question types should be varied and engaging throughout the survey",
            "Response scales should be consistent within question groups",
            "Skip logic and branching should be clear and purposeful",
            "Question order should minimize response bias and priming effects",
            "Overall survey structure should support the research methodology"
        ]
    },
    "deployment_readiness": {
        "name": "Deployment Readiness Rules",
        "description": "Rules for ensuring practical deployment considerations are met",
        "weight": 0.10,
        "default_rules": [
            "Survey length should be appropriate for the target audience (typically 10-25 minutes)",
            "Question count should balance comprehensiveness with respondent fatigue", 
            "Target sample size should be realistic and achievable for the audience",
            "Survey complexity should match the incentive and value proposition",
            "Technical requirements should be feasible for the deployment platform",
            "Compliance and privacy requirements should be addressed",
            "Survey should be optimized for the primary response channel (web, mobile, phone)"
        ]
    }
}

# SQL migration to add pillar-based rules
PILLAR_RULES_MIGRATION = """
-- Add pillar-based rule categories to the existing survey_rules table
-- This extends the current system with 5-pillar framework rules

-- Content Validity Rules
INSERT INTO survey_rules (rule_type, category, rule_name, rule_description, rule_content, priority, is_active, created_by) VALUES
('pillar', 'content_validity', 'RFQ Objective Coverage', 'Survey questions must directly address all stated research objectives from the RFQ', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "evaluation_criteria": ["objective_alignment", "topic_comprehensiveness", "research_goal_mapping"]}', 
 9, true, 'system'),

('pillar', 'content_validity', 'Research Scope Alignment', 'Survey scope should align with the research goals and target audience specified', 
 '{"pillar": "content_validity", "weight": 0.20, "priority": "high", "evaluation_criteria": ["scope_appropriateness", "audience_targeting", "goal_alignment"]}', 
 9, true, 'system'),

-- Methodological Rigor Rules  
('pillar', 'methodological_rigor', 'Bias Prevention', 'Avoid leading, loaded, or double-barreled questions that introduce bias', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "critical", "evaluation_criteria": ["bias_detection", "question_neutrality", "leading_language"]}', 
 10, true, 'system'),

('pillar', 'methodological_rigor', 'Question Sequencing', 'Questions must follow logical sequence from general to specific', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "high", "evaluation_criteria": ["sequence_logic", "flow_optimization", "bias_minimization"]}', 
 9, true, 'system'),

('pillar', 'methodological_rigor', 'Sample Size Appropriateness', 'Sample size and targeting must align with statistical requirements', 
 '{"pillar": "methodological_rigor", "weight": 0.25, "priority": "medium", "evaluation_criteria": ["statistical_adequacy", "methodology_alignment", "feasibility"]}', 
 8, true, 'system'),

-- Clarity & Comprehensibility Rules
('pillar', 'clarity_comprehensibility', 'Language Clarity', 'Use clear, simple language appropriate for the target audience', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["language_accessibility", "reading_level", "terminology_appropriateness"]}', 
 9, true, 'system'),

('pillar', 'clarity_comprehensibility', 'Single Concept Focus', 'Each question should focus on a single concept or idea', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["concept_clarity", "double_barreled_detection", "ambiguity_check"]}', 
 9, true, 'system'),

('pillar', 'clarity_comprehensibility', 'Neutral Wording', 'Question wording should be neutral and unambiguous', 
 '{"pillar": "clarity_comprehensibility", "weight": 0.25, "priority": "high", "evaluation_criteria": ["wording_neutrality", "ambiguity_assessment", "cultural_sensitivity"]}', 
 9, true, 'system'),

-- Structural Coherence Rules
('pillar', 'structural_coherence', 'Logical Organization', 'Survey sections should follow logical progression and organization', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "high", "evaluation_criteria": ["section_logic", "progression_flow", "organizational_structure"]}', 
 9, true, 'system'),

('pillar', 'structural_coherence', 'Question Grouping', 'Related questions should be grouped together appropriately', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "evaluation_criteria": ["topic_grouping", "thematic_organization", "cognitive_flow"]}', 
 8, true, 'system'),

('pillar', 'structural_coherence', 'Response Scale Consistency', 'Response scales should be consistent within question groups', 
 '{"pillar": "structural_coherence", "weight": 0.20, "priority": "medium", "evaluation_criteria": ["scale_consistency", "format_uniformity", "user_experience"]}', 
 8, true, 'system'),

-- Deployment Readiness Rules
('pillar', 'deployment_readiness', 'Survey Length Optimization', 'Survey length should be appropriate for the target audience (typically 10-25 minutes)', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "high", "evaluation_criteria": ["length_appropriateness", "audience_tolerance", "completion_feasibility"]}', 
 9, true, 'system'),

('pillar', 'deployment_readiness', 'Sample Size Feasibility', 'Target sample size should be realistic and achievable for the audience', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "evaluation_criteria": ["recruitment_feasibility", "audience_availability", "budget_alignment"]}', 
 8, true, 'system'),

('pillar', 'deployment_readiness', 'Technical Readiness', 'Technical requirements should be feasible for the deployment platform', 
 '{"pillar": "deployment_readiness", "weight": 0.10, "priority": "medium", "evaluation_criteria": ["platform_compatibility", "technical_feasibility", "user_experience"]}', 
 8, true, 'system');

-- Add comment about pillar rules
COMMENT ON TABLE survey_rules IS 'Stores survey generation rules and methodologies - includes seeded methodology, quality, industry, and pillar-based evaluation rules';
"""

class PillarRulesService:
    """Service for managing pillar-based rules and integrating them with evaluation system"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.pillar_categories = PILLAR_RULE_CATEGORIES
    
    def get_pillar_rules_for_evaluation(self, pillar_name: str) -> List[str]:
        """Get all rules for a specific pillar from database and defaults"""
        rules = []
        
        # Add default rules
        if pillar_name in self.pillar_categories:
            rules.extend(self.pillar_categories[pillar_name]["default_rules"])
        
        # Add database rules if available
        if self.db_session:
            try:
                from src.database.models import SurveyRule
                
                db_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == "pillar",
                    SurveyRule.category == pillar_name,
                    SurveyRule.is_active == True
                ).all()
                
                for rule in db_rules:
                    rules.append(rule.rule_description)
                    
            except Exception as e:
                print(f"Warning: Could not load pillar rules from database: {e}")
        
        return rules
    
    def get_all_pillar_rules(self) -> Dict[str, List[str]]:
        """Get all pillar rules organized by category"""
        all_rules = {}
        
        for pillar_name in self.pillar_categories.keys():
            all_rules[pillar_name] = self.get_pillar_rules_for_evaluation(pillar_name)
        
        return all_rules
    
    def create_pillar_rule_prompt_context(self, pillar_name: str) -> str:
        """Create LLM prompt context for a specific pillar evaluation"""
        if pillar_name not in self.pillar_categories:
            return ""
        
        pillar_info = self.pillar_categories[pillar_name]
        rules = self.get_pillar_rules_for_evaluation(pillar_name)
        
        context = f"""
## {pillar_info['name']} Evaluation Criteria

**Description**: {pillar_info['description']}
**Framework Weight**: {pillar_info['weight']:.0%}

**Specific Rules to Evaluate Against**:
"""
        
        for i, rule in enumerate(rules, 1):
            context += f"{i}. {rule}\n"
        
        context += f"""
**Evaluation Instructions**:
- Assess the survey comprehensively against each rule listed above
- Provide specific examples of compliance or non-compliance
- Consider the context of the RFQ and target audience
- Score on a scale of 0.0 to 1.0 where 1.0 indicates perfect adherence to all rules
- Identify the most critical issues that impact {pillar_info['name'].lower()}
"""
        
        return context
    
    def create_comprehensive_pillar_context(self) -> str:
        """Create comprehensive LLM context including all pillar rules"""
        context = """
# 5-Pillar Survey Evaluation Framework

This evaluation system assesses surveys across 5 key pillars with specific weights:

"""
        
        for pillar_name, pillar_info in self.pillar_categories.items():
            rules = self.get_pillar_rules_for_evaluation(pillar_name)
            
            context += f"""
## {pillar_info['name']} ({pillar_info['weight']:.0%} weight)
{pillar_info['description']}

**Rules**:
"""
            for i, rule in enumerate(rules, 1):
                context += f"  {i}. {rule}\n"
            
            context += "\n"
        
        context += """
**Overall Evaluation Guidelines**:
- Each pillar should be scored independently on a 0.0 to 1.0 scale
- The final score is calculated using the weighted average of all pillars
- Provide specific evidence and examples for each score
- Focus on actionable feedback and improvement recommendations
- Consider the RFQ context and target audience in all evaluations
"""
        
        return context

def create_pillar_rules_migration_file():
    """Create SQL migration file for pillar rules"""
    migration_content = f"""-- Migration: Add 5-Pillar Evaluation Rules
-- Created: $(date)
-- Description: Extends survey_rules table with pillar-based evaluation rules

{PILLAR_RULES_MIGRATION}
"""
    
    from pathlib import Path
    migration_file = Path(__file__).parent.parent / "migrations" / "004_add_pillar_rules.sql"
    
    with open(migration_file, 'w') as f:
        f.write(migration_content)
    
    print(f"✅ Created pillar rules migration: {migration_file}")
    return migration_file

if __name__ == "__main__":
    # Test the pillar rules service
    service = PillarRulesService()
    
    print("🏛️  Testing Pillar Rules Integration")
    print("=" * 50)
    
    # Test individual pillar rules
    for pillar_name in PILLAR_RULE_CATEGORIES.keys():
        rules = service.get_pillar_rules_for_evaluation(pillar_name)
        print(f"\n📋 {pillar_name}: {len(rules)} rules")
    
    # Test context generation
    print(f"\n🔍 Content Validity Context Length: {len(service.create_pillar_rule_prompt_context('content_validity'))} chars")
    print(f"🔍 Comprehensive Context Length: {len(service.create_comprehensive_pillar_context())} chars")
    
    # Create migration file
    create_pillar_rules_migration_file()
    
    print("\n✅ Pillar Rules Integration Ready!")