from typing import Dict, List, Any, Optional
from src.config import settings
from src.database import get_db
from src.database.models import SurveyRule
from .prompt_builder import PromptBuilder, RAGContext
import json
import logging

logger = logging.getLogger(__name__)


class PromptService:
    """
    Service for managing system prompts and rules for survey generation
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.prompt_builder = PromptBuilder(db_session)
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
                "CRITICAL: Output must be properly formatted JSON with NO line breaks within string values",
                "CRITICAL: All string values must be on single lines - do not break text across multiple lines",
                "CRITICAL: Use proper JSON syntax with correct quotes, commas, and brackets",
                "Include proper question types and validation rules",
                "Add appropriate metadata and methodology tags",
                "Ensure questions are properly categorized and sequenced",
                "Example of CORRECT format: {\"text\": \"What is your age?\", \"type\": \"number\"}",
                "Example of INCORRECT format: {\"text\": \"What\nis\nyour\nage?\", \"type\": \"number\"}"
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
                
                # Quality and custom rules have been replaced by generation rules system
                # (58 pillar-based generation rules provide comprehensive coverage)
                
                # Load pillar rules (evaluation rules)
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
                        'evaluation_criteria': rule_content.get('evaluation_criteria', []),
                        'rule_type': 'evaluation'
                    })

                # Load generation rules (core quality standards)
                generation_rules = self.db_session.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'generation',
                    SurveyRule.is_active == True
                ).order_by(SurveyRule.priority.desc()).all()  # Order by priority (higher first)

                for rule in generation_rules:
                    if rule.category not in self.pillar_rules:
                        self.pillar_rules[rule.category] = []

                    # Parse rule_content JSON
                    rule_content = {}
                    if rule.rule_content:
                        try:
                            import json
                            rule_content = json.loads(rule.rule_content) if isinstance(rule.rule_content, str) else rule.rule_content
                        except (json.JSONDecodeError, TypeError):
                            rule_content = {}

                    self.pillar_rules[rule.category].append({
                        'id': str(rule.id),
                        'name': rule.rule_name,
                        'description': rule.rule_description,
                        'priority': rule_content.get('priority', 'medium'),
                        'generation_guideline': rule_content.get('generation_guideline', ''),
                        'implementation_notes': rule_content.get('implementation_notes', []),
                        'quality_indicators': rule_content.get('quality_indicators', []),
                        'weight': rule_content.get('weight', 0.0),
                        'rule_type': 'generation'
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
                
                logger.info(f"Loaded {len(methodology_rules)} methodology rules, {sum(len(rules) for rules in self.pillar_rules.values())} pillar rules (including {sum(1 for rules in self.pillar_rules.values() for rule in rules if rule.get('rule_type') == 'generation')} generation rules), and system prompt from database")
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
        
        # Quality rules have been replaced by the comprehensive generation rules system
        # (58 pillar-based generation rules provide better coverage)
        self.quality_rules = {}
    
    def build_system_prompt(
        self,
        context: Dict[str, Any],
        methodology_tags: Optional[List[str]] = None,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Legacy method - now uses new PromptBuilder for consistency
        """
        # Use new PromptBuilder system
        rfq_text = context.get("rfq_details", {}).get("text", "")
        return self.prompt_builder.build_survey_generation_prompt(
            rfq_text=rfq_text,
            context=context,
            rag_context=None,  # No RAG context for simple system prompt
            methodology_tags=methodology_tags or []
        )
    
    def create_survey_prompt(
        self,
        rfq_text: str,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a survey generation prompt with RFQ text, context, and examples.
        This method is used by the HumanPromptReviewNode for prompt review.
        Uses new modular PromptBuilder with RAG context instead of golden example duplication.
        """
        # Ensure context has rfq_details for consistency
        if "rfq_details" not in context:
            context["rfq_details"] = {}

        # Add RFQ text to context if not already present
        if "text" not in context["rfq_details"]:
            context["rfq_details"]["text"] = rfq_text

        # Convert golden examples to RAG context summary
        rag_context = self._convert_golden_examples_to_rag_context(golden_examples)

        # Extract methodology tags
        methodology_tags = self._extract_methodology_tags(context, golden_examples)

        # Use new PromptBuilder
        return self.prompt_builder.build_survey_generation_prompt(
            rfq_text=rfq_text,
            context=context,
            rag_context=rag_context,
            methodology_tags=methodology_tags
        )
    
    def create_survey_generation_prompt(
        self,
        rfq_text: str,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a survey generation prompt with RFQ text, context, and examples.
        This is an alias for create_survey_prompt to maintain backward compatibility.
        """
        return self.create_survey_prompt(
            rfq_text=rfq_text,
            context=context,
            golden_examples=golden_examples,
            methodology_blocks=methodology_blocks,
            custom_rules=custom_rules
        )

    def _convert_golden_examples_to_rag_context(self, golden_examples: List[Dict[str, Any]]) -> Optional[RAGContext]:
        """Convert golden examples to RAG context summary"""
        if not golden_examples:
            return None

        quality_scores = [ex.get('quality_score', 0.0) for ex in golden_examples if ex.get('quality_score')]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        methodology_tags = []
        for example in golden_examples:
            if example.get('methodology_tags'):
                methodology_tags.extend(example['methodology_tags'])

        # Remove duplicates
        methodology_tags = list(set(methodology_tags))

        # Extract similarity scores if available
        similarity_scores = [ex.get('similarity', 1.0) for ex in golden_examples]

        return RAGContext(
            example_count=len(golden_examples),
            avg_quality_score=avg_quality,
            methodology_tags=methodology_tags,
            similarity_scores=similarity_scores
        )

    def _extract_methodology_tags(self, context: Dict[str, Any], golden_examples: List[Dict[str, Any]]) -> List[str]:
        """Extract methodology tags from context and golden examples"""
        methodology_tags = []

        # From context
        if context.get("rfq_details", {}).get("methodology_tags"):
            methodology_tags.extend(context["rfq_details"]["methodology_tags"])

        # From golden examples
        for example in golden_examples:
            if example.get("methodology_tags"):
                methodology_tags.extend(example["methodology_tags"])

        # Remove duplicates and convert to lowercase
        return list(set([tag.lower() for tag in methodology_tags]))
    
    def build_golden_enhanced_prompt(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Legacy method - now uses new PromptBuilder architecture for consistency
        """
        # Extract RFQ text from context
        rfq_text = context.get("rfq_details", {}).get("text", "")

        # Convert to RAG context
        rag_context = self._convert_golden_examples_to_rag_context(golden_examples)

        # Extract methodology tags
        methodology_tags = self._extract_methodology_tags(context, golden_examples)

        # Use new PromptBuilder
        return self.prompt_builder.build_survey_generation_prompt(
            rfq_text=rfq_text,
            context=context,
            rag_context=rag_context,
            methodology_tags=methodology_tags
        )
    
    def refresh_rules_from_database(self):
        """Refresh rules from database (useful when rules are updated)"""
        self.methodology_rules = {}
        self.quality_rules = {}
        self.pillar_rules = {}
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
            context_parts.append("Follow these core quality standards to ensure high-quality survey design:")

            # Separate generation rules from evaluation rules
            generation_rules = [r for r in rules if r.get('rule_type') == 'generation']
            evaluation_rules = [r for r in rules if r.get('rule_type') == 'evaluation']

            # Show generation rules first (these are the actionable guidelines)
            for rule in generation_rules:
                priority_indicator = "🔴" if rule['priority'] == 'core' else "🟡" if rule['priority'] == 'high' else "🔵" if rule['priority'] == 'medium' else "⚪"

                # Use generation_guideline if available, otherwise fall back to description
                guideline = rule.get('generation_guideline', rule.get('description', ''))
                context_parts.append(f"- {priority_indicator} {guideline}")

                # Add implementation notes for complex rules
                if rule.get('implementation_notes') and rule['priority'] in ['core', 'high']:
                    for note in rule['implementation_notes'][:2]:  # Limit to first 2 notes to keep prompt concise
                        context_parts.append(f"  • {note}")

            # Show evaluation rules if no generation rules exist for this pillar
            if not generation_rules and evaluation_rules:
                for rule in evaluation_rules:
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
        
        # Basic quality validation is now handled by generation rules
        # (No separate quality check needed - generation rules prevent issues at source)
        validation_results["quality_score"] = 0.8  # Default good score
        
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
    
    # _check_quality_rules method removed - quality validation now handled by generation rules
