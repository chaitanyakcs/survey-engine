from typing import Dict, List, Any, Optional
from src.config import settings
from src.database import get_db
from src.database.models import SurveyRule
import json
import logging

logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for managing system prompts and rules for survey generation
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.base_rules = self._load_base_rules()
        self.methodology_rules = {}
        self.quality_rules = {}
        self.pillar_rules = {}
        self.system_prompt = ""
        self._load_database_rules()
    
    def _load_base_rules(self) -> Dict[str, Any]:
        """Load base system rules for survey generation"""
        return {
            "role": "You are an expert survey designer and market research specialist with 15+ years of experience.",
            "expertise": [
                "Market research methodology design",
                "Question design and survey optimization", 
                "Statistical analysis and data quality",
                "Industry best practices and compliance"
            ],
            "core_principles": [
                "Always prioritize data quality and respondent experience",
                "Design surveys that are clear, unbiased, and actionable",
                "Follow established research methodologies rigorously",
                "Ensure questions are specific, measurable, and relevant",
                "Maintain logical flow and appropriate question sequencing"
            ],
            "output_requirements": [
                "Generate valid JSON following the specified schema",
                "Include proper question types and validation rules",
                "Add appropriate metadata and methodology tags",
                "Ensure questions are properly categorized and sequenced"
            ]
        }
    
    def _load_database_rules(self):
        """Load rules from database instead of hardcoded ones"""
        try:
            if self.db_session:
                # Load methodology rules
                methodology_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'methodology',
                    SurveyRule.is_active == True
                ).all()
                
                for rule in methodology_rules:
                    self.methodology_rules[rule.category] = {
                        "description": rule.rule_description,
                        "required_questions": rule.rule_content.get('required_questions', 0) if rule.rule_content else 0,
                        "validation_rules": rule.rule_content.get('validation_rules', []) if rule.rule_content else []
                    }
                
                # Load quality rules
                quality_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'quality',
                    SurveyRule.is_active == True
                ).all()
                
                for rule in quality_rules:
                    if rule.category not in self.quality_rules:
                        self.quality_rules[rule.category] = []
                    if rule.rule_content and isinstance(rule.rule_content, dict):
                        rule_text = rule.rule_content.get('rule_text', '')
                        if rule_text:
                            self.quality_rules[rule.category].append(rule_text)
                
                # Load custom rules
                custom_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'custom',
                    SurveyRule.is_active == True
                ).all()
                
                for rule in custom_rules:
                    if rule.category not in self.quality_rules:
                        self.quality_rules[rule.category] = []
                    # For custom rules, use rule_description directly
                    if rule.rule_description:
                        self.quality_rules[rule.category].append(rule.rule_description)
                
                # Load pillar rules
                pillar_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'pillar',
                    SurveyRule.is_active == True
                ).all()
                
                for rule in pillar_rules:
                    if rule.category not in self.pillar_rules:
                        self.pillar_rules[rule.category] = []
                    
                    rule_content = rule.rule_content or {}
                    self.pillar_rules[rule.category].append({
                        'id': str(rule.id),
                        'name': rule.rule_name,
                        'description': rule.rule_description,
                        'priority': rule_content.get('priority', 'medium'),
                        'evaluation_criteria': rule_content.get('evaluation_criteria', [])
                    })
                
                # Load system prompt
                system_prompt_rule = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'system_prompt',
                    SurveyRule.is_active == True
                ).first()
                
                if system_prompt_rule and system_prompt_rule.rule_description:
                    self.system_prompt = system_prompt_rule.rule_description
                else:
                    self.system_prompt = ""
                
                logger.info(f"Loaded {len(methodology_rules)} methodology rules, {len(quality_rules)} quality rules, {len(custom_rules)} custom rules, {sum(len(rules) for rules in self.pillar_rules.values())} pillar rules, and system prompt from database")
            else:
                # Fallback to hardcoded rules if no database session
                self._load_fallback_rules()
                logger.warning("No database session available, using fallback rules")
        except Exception as e:
            logger.error(f"Failed to load database rules: {e}")
            self._load_fallback_rules()
    
    def _load_fallback_rules(self):
        """Load fallback hardcoded rules if database is unavailable"""
        self.methodology_rules = {
            "van_westendorp": {
                "description": "Van Westendorp Price Sensitivity Meter",
                "required_questions": 4,
                "validation_rules": [
                    "Must have exactly 4 price questions",
                    "Questions must follow the exact Van Westendorp format",
                    "Price ranges should be logical and sequential"
                ]
            },
            "conjoint": {
                "description": "Conjoint Analysis / Choice Modeling",
                "required_questions": 6,
                "validation_rules": [
                    "Must have balanced choice sets",
                    "Attributes must be orthogonal",
                    "Include appropriate sample size calculations"
                ]
            },
            "maxdiff": {
                "description": "MaxDiff (Maximum Difference Scaling)",
                "required_questions": 8,
                "validation_rules": [
                    "Items must be balanced across choice sets",
                    "Include appropriate number of choice tasks",
                    "Ensure statistical power for analysis"
                ]
            },
            "nps": {
                "description": "Net Promoter Score",
                "required_questions": 2,
                "validation_rules": [
                    "Must use 0-10 scale",
                    "Include follow-up question for reasoning",
                    "Properly categorize promoters, passives, detractors"
                ]
            }
        }
        
        self.quality_rules = {
            "question_quality": [
                "Questions must be clear, concise, and unambiguous",
                "Avoid leading, loaded, or double-barreled questions",
                "Use appropriate question types for the data needed",
                "Include proper validation and skip logic where needed"
            ],
            "survey_structure": [
                "Start with screening questions to qualify respondents",
                "Group related questions logically",
                "Place sensitive questions near the end",
                "Include demographic questions for segmentation"
            ],
            "methodology_compliance": [
                "Follow established research methodology standards",
                "Include appropriate sample size considerations",
                "Ensure statistical validity of question design",
                "Add proper metadata for analysis"
            ],
            "respondent_experience": [
                "Keep survey length appropriate (5-15 minutes)",
                "Use clear instructions and progress indicators",
                "Avoid repetitive or redundant questions",
                "Ensure mobile-friendly question formats"
            ]
        }
    
    def build_system_prompt(
        self,
        context: Dict[str, Any],
        methodology_tags: Optional[List[str]] = None,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build comprehensive system prompt with rules and guidelines
        """
        prompt_parts = []
        
        # Base role and expertise
        prompt_parts.extend([
            f"# {self.base_rules['role']}",
            "",
            "## Your Expertise:",
            *[f"- {exp}" for exp in self.base_rules['expertise']],
            "",
            "## Core Design Principles:",
            *[f"- {principle}" for principle in self.base_rules['core_principles']],
            ""
        ])
        
        # Methodology-specific rules
        if methodology_tags:
            prompt_parts.extend([
                "## Methodology Requirements:",
                ""
            ])
            for tag in methodology_tags:
                if tag.lower() in self.methodology_rules:
                    method = self.methodology_rules[tag.lower()]
                    prompt_parts.extend([
                        f"### {method['description']}:",
                        f"- Required Questions: {method['required_questions']}",
                        f"- Validation Rules: {'; '.join(method['validation_rules'])}",
                        ""
                    ])
        
        # Quality rules
        prompt_parts.extend([
            "## Quality Standards:",
            ""
        ])
        for category, rules in self.quality_rules.items():
            prompt_parts.extend([
                f"### {category.replace('_', ' ').title()}:",
                *[f"- {rule}" for rule in rules],
                ""
            ])
        
        # Custom system prompt if available
        if self.system_prompt:
            prompt_parts.extend([
                "## Custom System Instructions:",
                self.system_prompt,
                ""
            ])
        
        # Custom rules if provided
        if custom_rules:
            prompt_parts.extend([
                "## Custom Requirements:",
                *[f"- {rule}" for rule in custom_rules.get('rules', [])],
                ""
            ])
        
        # Output format requirements
        prompt_parts.extend([
            "## Output Requirements:",
            *[f"- {req}" for req in self.base_rules['output_requirements']],
            ""
        ])
        
        return "\n".join(prompt_parts)
    
    def build_golden_enhanced_prompt(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the complete prompt with system rules, golden examples, and context
        """
        # Get methodology tags from context or golden examples
        methodology_tags = []
        if context.get("rfq_details", {}).get("methodology_tags"):
            methodology_tags.extend(context["rfq_details"]["methodology_tags"])
        
        for example in golden_examples:
            if example.get("methodology_tags"):
                methodology_tags.extend(example["methodology_tags"])
        
        # Remove duplicates and convert to lowercase
        methodology_tags = list(set([tag.lower() for tag in methodology_tags]))
        
        # Build system prompt with rules
        system_prompt = self.build_system_prompt(
            context=context,
            methodology_tags=methodology_tags,
            custom_rules=custom_rules
        )
        
        # Log the final system prompt before RAG kicks in
        logger.info("=" * 80)
        logger.info("🎯 FINAL SYSTEM PROMPT GENERATED (Before RAG)")
        logger.info("=" * 80)
        logger.info(system_prompt)
        logger.info("=" * 80)
        logger.info("🚀 Now proceeding with RAG and golden examples...")
        logger.info("=" * 80)
        
        # Build the main prompt with golden examples
        prompt_parts = [
            system_prompt,
            "",
            "## GOLDEN STANDARD EXAMPLES:",
            ""
        ]
        
        # Add golden examples as few-shot prompts
        for i, example in enumerate(golden_examples[:settings.max_golden_examples], 1):
            prompt_parts.extend([
                f"### Example {i}:",
                f"**RFQ:** {example['rfq_text'][:500]}...",
                f"**Quality Score:** {example.get('quality_score', 'N/A')}",
                f"**Methodology:** {', '.join(example.get('methodology_tags', []))}",
                f"**Survey Structure:**",
                json.dumps(example['survey_json'], indent=2)[:1000] + "...",
                ""
            ])
        
        # Add pillar rules context
        pillar_rules_context = self.get_pillar_rules_context()
        if pillar_rules_context:
            prompt_parts.extend([
                "## 5-PILLAR EVALUATION FRAMEWORK:",
                "Follow these comprehensive rules to ensure high-quality survey design:",
                pillar_rules_context,
                ""
            ])
        
        # Add methodology guidance
        if methodology_blocks:
            prompt_parts.extend([
                "## METHODOLOGY GUIDANCE:",
                ""
            ])
            for block in methodology_blocks:
                prompt_parts.extend([
                    f"### {block['methodology']}:",
                    f"**Structure:** {json.dumps(block['example_structure'], indent=2)}",
                    f"**Usage Pattern:** {json.dumps(block['usage_pattern'], indent=2)}",
                    ""
                ])
        
        # Add current RFQ context
        rfq_details = context.get("rfq_details", {})
        prompt_parts.extend([
            "## CURRENT RFQ:",
            f"**Title:** {rfq_details.get('title', 'N/A')}",
            f"**Description:** {rfq_details.get('text', '')}",
            f"**Category:** {rfq_details.get('category', 'N/A')}",
            f"**Target Segment:** {rfq_details.get('segment', 'N/A')}",
            f"**Research Goal:** {rfq_details.get('goal', 'N/A')}",
            "",
            "## TASK:",
            "Generate a complete, high-quality survey following all the rules and guidelines above.",
            "CRITICAL: Ensure compliance with the 5-Pillar Evaluation Framework rules listed above.",
            "Use the golden examples as reference for quality and structure.",
            "Ensure methodology compliance and proper question design.",
            "",
            "Return valid JSON with this exact structure:",
            json.dumps({
                "title": "Survey Title",
                "description": "Survey Description",
                "questions": [
                    {
                        "id": "q1",
                        "text": "Question text",
                        "type": "multiple_choice|text|scale|ranking",
                        "options": ["Option 1", "Option 2"],
                        "required": True,
                        "methodology": "screening|core|demographic",
                        "validation": "optional validation rules"
                    }
                ],
                "metadata": {
                    "estimated_time": 10,
                    "methodology_tags": ["tag1", "tag2"],
                    "target_responses": 100,
                    "quality_score": 0.85
                }
            }, indent=2),
            "",
            "Generate the survey JSON now:"
        ])
        
        # Join all prompt parts into final prompt
        final_prompt = "\n".join(prompt_parts)
        
        # Log the complete final prompt that will be sent to LLM
        logger.info("=" * 100)
        logger.info("🤖 COMPLETE FINAL PROMPT SENT TO LLM")
        logger.info("=" * 100)
        logger.info(final_prompt)
        logger.info("=" * 100)
        logger.info("📤 Prompt length: {} characters".format(len(final_prompt)))
        logger.info("=" * 100)
        
        return final_prompt
    
    def add_custom_rule(self, rule_type: str, rule: str) -> None:
        """Add a custom rule to the system"""
        if rule_type not in self.quality_rules:
            self.quality_rules[rule_type] = []
        self.quality_rules[rule_type].append(rule)
        logger.info(f"Added custom rule to {rule_type}: {rule}")
    
    def refresh_rules_from_database(self):
        """Refresh rules from database (useful when rules are updated)"""
        self.methodology_rules = {}
        self.quality_rules = {}
        self._load_database_rules()
        logger.info("Rules refreshed from database")
    
    def get_methodology_guidelines(self, methodology: str) -> Optional[Dict[str, Any]]:
        """Get specific guidelines for a methodology"""
        return self.methodology_rules.get(methodology.lower())
    
    def get_pillar_rules_context(self) -> str:
        """Get pillar rules formatted for LLM prompt context"""
        if not self.pillar_rules:
            return ""
        
        context_parts = []
        pillar_weights = {
            'content_validity': 0.20,
            'methodological_rigor': 0.25,
            'clarity_comprehensibility': 0.25,
            'structural_coherence': 0.20,
            'deployment_readiness': 0.10
        }
        
        for pillar, rules in self.pillar_rules.items():
            if not rules:
                continue
                
            weight = pillar_weights.get(pillar, 0.0)
            pillar_display = pillar.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility')
            
            context_parts.append(f"\n## {pillar_display} ({weight:.0%} Weight)")
            context_parts.append("Follow these rules to ensure high-quality survey design:")
            
            for rule in rules:
                priority_indicator = "🔴" if rule['priority'] == 'critical' else "🟡" if rule['priority'] == 'high' else "🔵" if rule['priority'] == 'medium' else "⚪"
                context_parts.append(f"- {priority_indicator} {rule['description']}")
                
                # Add evaluation criteria if available
                if rule.get('evaluation_criteria'):
                    for criterion in rule['evaluation_criteria']:
                        context_parts.append(f"  • {criterion}")
        
        return "\n".join(context_parts)
    
    def validate_survey_against_rules(
        self,
        survey: Dict[str, Any],
        methodology_tags: List[str]
    ) -> Dict[str, Any]:
        """
        Validate generated survey against the rules
        """
        validation_results = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "methodology_compliance": {},
            "quality_score": 0.0
        }
        
        # Check methodology compliance
        for tag in methodology_tags:
            if tag.lower() in self.methodology_rules:
                method_rules = self.methodology_rules[tag.lower()]
                compliance = self._check_methodology_compliance(survey, method_rules)
                validation_results["methodology_compliance"][tag] = compliance
                
                if not compliance["passed"]:
                    validation_results["passed"] = False
                    validation_results["errors"].extend(compliance["errors"])
        
        # Check basic quality rules
        quality_check = self._check_quality_rules(survey)
        validation_results["quality_score"] = quality_check["score"]
        
        if quality_check["errors"]:
            validation_results["passed"] = False
            validation_results["errors"].extend(quality_check["errors"])
        
        validation_results["warnings"].extend(quality_check["warnings"])
        
        return validation_results
    
    def _check_methodology_compliance(
        self,
        survey: Dict[str, Any],
        method_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if survey complies with specific methodology rules"""
        compliance = {
            "passed": True,
            "errors": [],
            "details": {}
        }
        
        questions = survey.get("questions", [])
        
        # Check required number of questions
        if "required_questions" in method_rules:
            required = method_rules["required_questions"]
            if len(questions) < required:
                compliance["passed"] = False
                compliance["errors"].append(f"Methodology requires {required} questions, found {len(questions)}")
        
        # Check question flow patterns
        if "question_flow" in method_rules:
            # This would be more sophisticated in practice
            compliance["details"]["flow_check"] = "Basic flow validation"
        
        return compliance
    
    def _check_quality_rules(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """Check survey against quality rules"""
        quality_check = {
            "score": 0.8,  # Base score
            "errors": [],
            "warnings": []
        }
        
        questions = survey.get("questions", [])
        
        # Basic checks
        if not questions:
            quality_check["errors"].append("Survey must have questions")
            quality_check["score"] = 0.0
            return quality_check
        
        # Check question quality
        for i, question in enumerate(questions):
            if not question.get("text"):
                quality_check["errors"].append(f"Question {i+1} missing text")
                quality_check["score"] -= 0.1
            
            if not question.get("type"):
                quality_check["warnings"].append(f"Question {i+1} missing type")
                quality_check["score"] -= 0.05
        
        # Ensure score is between 0 and 1
        quality_check["score"] = max(0.0, min(1.0, quality_check["score"]))
        
        return quality_check
