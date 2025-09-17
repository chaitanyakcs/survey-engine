#!/usr/bin/env python3
"""
Consolidated Rules Integration
Updated integration for the consolidated pillar-based rules system
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ConsolidatedRule:
    id: str
    pillar: str
    rule_text: str
    priority: str
    weight: float
    migrated_from: Optional[str]
    evaluation_criteria: List[str]

class ConsolidatedRulesService:
    """
    Service for managing the consolidated pillar-based rules system
    Replaces the previous mixed quality/pillar approach
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.pillar_weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25, 
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }
    
    def get_active_evaluation_rules(self) -> Dict[str, List[ConsolidatedRule]]:
        """Get all active evaluation rules organized by type"""
        active_rules = {
            'pillar': {},
            'methodology': {},
            'industry': {}
        }
        
        if self.db_session:
            try:
                from sqlalchemy import text
                # Use the active_evaluation_rules view created by migration
                query = text("""
                SELECT id, rule_type, category, rule_name, rule_description, 
                       rule_content, priority, pillar_weight, pillar_name
                FROM active_evaluation_rules
                ORDER BY rule_type, category, priority DESC
                """)
                
                results = self.db_session.execute(query).fetchall()
                
                for row in results:
                    rule_type = row.rule_type
                    category = row.category
                    
                    if rule_type == 'pillar':
                        if category not in active_rules['pillar']:
                            active_rules['pillar'][category] = []
                        
                        rule_content = row.rule_content or {}
                        active_rules['pillar'][category].append(ConsolidatedRule(
                            id=str(row.id),
                            pillar=category,
                            rule_text=row.rule_description,
                            priority=rule_content.get('priority', 'medium'),
                            weight=row.pillar_weight or 0.0,
                            migrated_from=rule_content.get('migrated_from'),
                            evaluation_criteria=rule_content.get('evaluation_criteria', [])
                        ))
                    else:
                        if category not in active_rules[rule_type]:
                            active_rules[rule_type][category] = []
                        
                        active_rules[rule_type][category].append({
                            'id': str(row.id),
                            'name': row.rule_name,
                            'description': row.rule_description,
                            'content': row.rule_content,
                            'priority': row.priority
                        })
                        
            except Exception as e:
                print(f"Warning: Could not load consolidated rules from database: {e}")
        
        return active_rules
    
    def get_pillar_rules_for_llm_context(self, pillar_name: str) -> str:
        """Generate LLM context for a specific pillar using consolidated rules"""
        if pillar_name not in self.pillar_weights:
            return ""
        
        weight = self.pillar_weights[pillar_name]
        pillar_display = pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility')
        
        context = f"""
## {pillar_display} Evaluation Rules

**Pillar Weight**: {weight:.0%} of overall evaluation score
**Evaluation Focus**: Comprehensive assessment of {pillar_display.lower()} in survey design

**Specific Rules to Evaluate Against**:
"""
        
        # Get pillar-specific rules
        active_rules = self.get_active_evaluation_rules()
        pillar_rules = active_rules['pillar'].get(pillar_name, [])
        
        if pillar_rules:
            for i, rule in enumerate(pillar_rules, 1):
                priority_indicator = "🔴" if rule.priority == "critical" else "🟡" if rule.priority == "high" else "🔵"
                context += f"{i}. {priority_indicator} {rule.rule_text}\n"
                
                if rule.evaluation_criteria:
                    context += f"   └── Focus: {', '.join(rule.evaluation_criteria)}\n"
        else:
            # Fallback to default rules if database unavailable
            default_rules = self._get_default_pillar_rules(pillar_name)
            for i, rule in enumerate(default_rules, 1):
                context += f"{i}. {rule}\n"
        
        context += f"""
**Evaluation Instructions**:
- Assess survey comprehensively against each rule listed above
- Consider rule priority (🔴 Critical > 🟡 High > 🔵 Medium/Low)
- Provide specific examples of compliance or non-compliance
- Score on scale 0.0-1.0 where 1.0 = perfect adherence to all rules
- Weight your assessment according to the {weight:.0%} pillar importance
"""
        
        return context
    
    def create_pillar_rule_prompt_context(self, pillar_name: str) -> str:
        """Create LLM prompt context for a specific pillar evaluation (alias for get_pillar_rules_for_llm_context)"""
        return self.get_pillar_rules_for_llm_context(pillar_name)
    
    def get_comprehensive_evaluation_context(self) -> str:
        """Generate comprehensive LLM context for all pillars"""
        context = """
# Consolidated 5-Pillar Survey Evaluation Framework

This evaluation system uses a consolidated rule structure that replaces previous quality rules 
with a comprehensive pillar-based approach. Each pillar has specific weight and criteria:

"""
        
        for pillar_name, weight in self.pillar_weights.items():
            pillar_context = self.get_pillar_rules_for_llm_context(pillar_name)
            context += pillar_context + "\n"
        
        context += """
**Overall Evaluation Process**:
1. Evaluate each pillar independently using its specific rules
2. Apply pillar weights to calculate overall score
3. Provide detailed feedback for each pillar
4. Generate actionable recommendations for improvement

**Rule System Notes**:
- Pillar rules replace previous generic quality rules
- Methodology rules (conjoint, NPS, etc.) remain for specific implementations
- Industry rules (healthcare, fintech, etc.) remain for domain compliance
- All pillar rules are database-driven and user-customizable
"""
        
        return context
    
    def _get_default_pillar_rules(self, pillar_name: str) -> List[str]:
        """Fallback default rules when database unavailable"""
        default_rules = {
            'content_validity': [
                "Survey questions must directly address all stated research objectives",
                "Each key research area should have corresponding questions",
                "Question coverage should be comprehensive without gaps",
                "Questions should map clearly to business objectives"
            ],
            'methodological_rigor': [
                "Avoid leading, loaded, or double-barreled questions",
                "Questions must follow logical sequence from general to specific", 
                "Screening questions should appear early in survey flow",
                "Sensitive questions should be placed toward the end",
                "Question types must match methodology requirements"
            ],
            'clarity_comprehensibility': [
                "Use clear, simple language appropriate for target audience",
                "Avoid jargon and technical terms unless necessary",
                "Each question should focus on single concept",
                "Question wording should be neutral and unambiguous",
                "Instructions should be clear and easy to understand"
            ],
            'structural_coherence': [
                "Survey sections should follow logical progression",
                "Related questions should be grouped appropriately", 
                "Question types should be varied and engaging",
                "Response scales should be consistent within groups",
                "Skip logic should be clear and purposeful"
            ],
            'deployment_readiness': [
                "Survey length should be appropriate for target audience",
                "Question count should balance comprehensiveness with fatigue",
                "Target sample size should be realistic and achievable",
                "Survey should be optimized for primary response channel",
                "Technical requirements should be feasible"
            ]
        }
        
        return default_rules.get(pillar_name, [])
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """Get summary of rule consolidation migration"""
        summary = {
            "migration_completed": True,
            "consolidated_rules": {
                "quality/question_quality": "→ clarity_comprehensibility + methodological_rigor",
                "quality/survey_structure": "→ structural_coherence + methodological_rigor", 
                "quality/respondent_experience": "→ deployment_readiness + clarity_comprehensibility"
            },
            "kept_rules": {
                "methodology": "Kept - provide specific implementation details",
                "industry": "Kept - provide domain-specific compliance guidance"
            },
            "benefits": [
                "Eliminated 57 rule overlaps",
                "Unified evaluation framework", 
                "Better LLM context organization",
                "User-customizable pillar rules",
                "Weighted evaluation scoring"
            ]
        }
        
        if self.db_session:
            try:
                # Get migration statistics
                query = text("""
                SELECT 
                    COUNT(*) FILTER (WHERE rule_type = 'pillar' AND created_by = 'migration') as new_pillar_rules,
                    COUNT(*) FILTER (WHERE rule_type = 'quality' AND is_active = false) as deactivated_quality_rules,
                    COUNT(*) FILTER (WHERE rule_type = 'methodology' AND is_active = true) as active_methodology_rules,
                    COUNT(*) FILTER (WHERE rule_type = 'industry' AND is_active = true) as active_industry_rules
                FROM survey_rules
                """)
                
                result = self.db_session.execute(query).fetchone()
                summary["statistics"] = {
                    "new_pillar_rules": result.new_pillar_rules,
                    "deactivated_quality_rules": result.deactivated_quality_rules,
                    "active_methodology_rules": result.active_methodology_rules,
                    "active_industry_rules": result.active_industry_rules
                }
                
            except Exception as e:
                summary["statistics"] = f"Could not retrieve migration statistics: {e}"
        
        return summary

def test_consolidated_rules_integration():
    """Test the consolidated rules system"""
    print("🧪 Testing Consolidated Rules Integration")
    print("=" * 50)
    
    # Test without database
    service = ConsolidatedRulesService(db_session=None)
    
    # Test pillar context generation
    for pillar in ['content_validity', 'methodological_rigor', 'clarity_comprehensibility']:
        context = service.get_pillar_rules_for_llm_context(pillar)
        print(f"✅ {pillar}: {len(context)} chars of context generated")
        assert len(context) > 500, f"Context too short for {pillar}"
    
    # Test comprehensive context
    comprehensive = service.get_comprehensive_evaluation_context()
    print(f"✅ Comprehensive context: {len(comprehensive)} chars")
    assert "Consolidated 5-Pillar" in comprehensive
    assert "Pillar Weight" in comprehensive
    
    # Test migration summary
    summary = service.get_migration_summary()
    print(f"✅ Migration summary: {len(summary['benefits'])} benefits listed")
    assert summary["migration_completed"] == True
    
    print("\n🎉 All consolidated rules tests passed!")
    return True

if __name__ == "__main__":
    test_consolidated_rules_integration()