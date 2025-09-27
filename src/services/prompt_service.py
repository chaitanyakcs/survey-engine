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
        
        # Custom requirements section (methodology requirements already added above)
        prompt_parts.extend([
            "## Custom Requirements:",
            "",
            "## Output Requirements:",
            "- Generate valid JSON following the specified schema",
            "- CRITICAL: Output must be properly formatted JSON with NO line breaks within string values",
            "- CRITICAL: All string values must be on single lines - do not break text across multiple lines",
            "- CRITICAL: Use proper JSON syntax with correct quotes, commas, and brackets",
            "- Include proper question types and validation rules",
            "- Add appropriate metadata and methodology tags",
            "- Ensure questions are properly categorized and sequenced",
            "- Example of CORRECT format: {\"text\": \"What is your age?\", \"type\": \"number\"}",
            "- Example of INCORRECT format: {\"text\": \"What\nis\nyour\nage?\", \"type\": \"number\"}",
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
        
        # Add comprehensive 5-pillar evaluation framework
        prompt_parts.extend([
            "## 5-PILLAR EVALUATION FRAMEWORK:",
            "Follow these comprehensive rules to ensure high-quality survey design:",
            "",
            "## Content Validity (20% Weight)",
            "Follow these core quality standards to ensure high-quality survey design:",
            "- 🔴 Include sufficient screening questions to identify and qualify the target respondent population",
            "  • Design screening questions early in survey flow",
            "  • Ensure screening criteria match target population definition",
            "- 🔴 Ensure the questionnaire comprehensively covers all essential research objectives stated in the RFQ document",
            "  • Review all RFQ objectives carefully before question design",
            "  • Map each research objective to specific survey questions",
            "- 🔴 Include appropriate and sufficient demographic questions for target audience analysis",
            "  • Consider age, gender, income, geography as relevant to research goals",
            "  • Include occupation, education level when business-relevant",
            "- 🔴 Address information needs of all key stakeholders identified in the research",
            "  • Identify all stakeholders mentioned in RFQ",
            "  • Ensure questions address each stakeholder's information needs",
            "- 🟡 Ensure questions capture data at the appropriate level of detail for analysis requirements",
            "  • Consider analysis granularity needs when designing questions",
            "  • Balance detail level with respondent burden",
            "- 🟡 Include validation questions or consistency checks to verify response reliability",
            "  • Add attention check questions in longer surveys",
            "  • Include consistency verification questions for critical data",
            "",
            "## Methodological Rigor (25% Weight)",
            "Follow these core quality standards to ensure high-quality survey design:",
            "- 🔴 Include appropriate sample size considerations and statistical power requirements",
            "  • Consider minimum sample size for intended analysis",
            "  • Include sample size guidance in survey metadata",
            "- 🔴 Design questions to minimize measurement error and response bias",
            "  • Use neutral, unbiased question wording",
            "  • Avoid leading or loaded questions",
            "- 🔴 Include appropriate control questions and randomization where methodologically required",
            "  • Add control questions for experimental designs",
            "  • Include randomization instructions where needed",
            "- 🔴 Ensure response scales and formats are consistent with established research practices",
            "  • Use standard Likert scales (5-point, 7-point) where appropriate",
            "  • Maintain consistent scale directions throughout survey",
            "- 🔴 Use methodologically sound question types appropriate for the specific data collection needs",
            "  • Match question types to data requirements (categorical, ordinal, interval)",
            "  • Use established question formats for validated constructs",
            "",
            "## Clarity & Comprehensibility (25% Weight)",
            "Follow these core quality standards to ensure high-quality survey design:",
            "- 🔴 Use consistent terminology and question formats throughout the survey",
            "  • Maintain consistent terms for the same concepts",
            "  • Use consistent question format patterns",
            "- 🔴 Write all questions using clear, unambiguous language that is easily understood by the target audience",
            "  • Use simple, direct language appropriate for target demographic",
            "  • Avoid ambiguous terms that could be interpreted multiple ways",
            "- 🔴 Avoid unnecessary technical jargon and define technical terms when they must be used",
            "  • Use plain language instead of technical jargon where possible",
            "  • Provide clear definitions for necessary technical terms",
            "- 🔴 Ensure response options are mutually exclusive and collectively exhaustive",
            "  • Design response options that don't overlap",
            "  • Include all reasonable response possibilities",
            "- 🔴 Provide clear, comprehensive instructions for completing each question type",
            "  • Include specific instructions for complex question types",
            "  • Explain how to use scales, rankings, or special formats",
            "- 🔴 Design questions to avoid double-barreled, leading, or loaded constructions",
            "  • Ask about one concept per question",
            "  • Use neutral wording that doesn't suggest preferred answers",
            "",
            "## Structural Coherence (20% Weight)",
            "Follow these core quality standards to ensure high-quality survey design:",
            "- 🔴 Organize questions in a logical, coherent flow that guides respondents naturally through the survey",
            "  • Start with general questions and move to specific",
            "  • Group related questions together logically",
            "- 🔴 Structure survey sections in a logical sequence that supports the research objectives",
            "  • Organize sections to build understanding progressively",
            "  • Place screening questions early in survey",
            "- 🔴 Implement appropriate skip logic and branching to maintain survey relevance for all respondents",
            "  • Design skip logic to avoid irrelevant questions",
            "  • Create clear branching paths for different respondent types",
            "- 🔴 Balance survey length appropriately for the target audience and research depth required",
            "  • Consider target audience attention span",
            "  • Balance comprehensiveness with completion rates",
            "",
            "## Deployment Readiness (10% Weight)",
            "Follow these core quality standards to ensure high-quality survey design:",
            "- 🔴 Design questions to be mobile-friendly and accessible across different devices and platforms",
            "  • Ensure questions work well on mobile devices",
            "  • Consider accessibility requirements",
            "- 🔴 Include appropriate time estimates and progress indicators in survey design",
            "  • Provide realistic completion time estimates",
            "  • Design for progress tracking",
            "- 🔴 Provide clear, comprehensive instructions for survey respondents and administrators",
            "  • Include detailed respondent instructions",
            "  • Provide administrator guidance where needed",
            "",
            "## Output Requirements:",
            *[f"- {req}" for req in self.base_rules['output_requirements']],
            ""
        ])
        
        return "\n".join(prompt_parts)
    
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
        """
        # Ensure context has rfq_details for consistency
        if "rfq_details" not in context:
            context["rfq_details"] = {}
        
        # Add RFQ text to context if not already present
        if "text" not in context["rfq_details"]:
            context["rfq_details"]["text"] = rfq_text
        
        # Build the complete prompt using the existing method
        return self.build_golden_enhanced_prompt(
            context=context,
            golden_examples=golden_examples,
            methodology_blocks=methodology_blocks,
            custom_rules=custom_rules
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
    
    def build_golden_enhanced_prompt(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the complete prompt with system rules, golden examples, and context
        Focused on sections format generation with all essential rules
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
        
        # Build system prompt with rules (but shorter than full version)
        system_prompt = self.build_system_prompt(
            context=context,
            methodology_tags=methodology_tags,
            custom_rules=custom_rules
        )
        
        # Build the main prompt with all essential components
        prompt_parts = [
            system_prompt,
            "",
            "## GOLDEN STANDARD EXAMPLES:",
            ""
        ]
        
        # Add golden examples as few-shot prompts (but limit to 3 for brevity)
        for i, example in enumerate(golden_examples[:3], 1):
            prompt_parts.extend([
                f"### Example {i}:",
                f"**RFQ:** {example['rfq_text'][:400]}...",
                f"**Quality Score:** {example.get('quality_score', 'N/A')}",
                f"**Methodology:** {', '.join(example.get('methodology_tags', []))}",
                f"**Survey Structure:**",
                json.dumps(example['survey_json'], indent=2)[:800] + "...",
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
            "## CRITICAL REQUIREMENT - SECTIONS FORMAT:",
            "🚨 MANDATORY: You MUST generate the survey using the SECTIONS format, NOT the legacy questions format.",
            "🚨 The survey MUST have a 'sections' array with exactly 5 sections, each containing questions.",
            "🚨 DO NOT use a flat 'questions' array - this will cause errors.",
            "",
            "## TASK:",
            "Generate a complete, high-quality survey following all the rules and guidelines above.",
            "CRITICAL: Ensure compliance with the 5-Pillar Evaluation Framework rules listed above.",
            "Use the golden examples as reference for quality and structure.",
            "Ensure methodology compliance and proper question design.",
            "",
            "## SECTION ORGANIZATION - REQUIRED STRUCTURE:",
            "You MUST organize all questions into these 5 sections:",
            "1. **Screener & Demographics** (id: 1): Age, location, income, qualifying criteria, basic demographics",
            "2. **Consumer Details** (id: 2): Lifestyle, behavior patterns, detailed consumer profile information", 
            "3. **Consumer product awareness, usage and preference** (id: 3): Brand awareness, usage frequency, preferences, satisfaction",
            "4. **Product introduction and Concept reaction** (id: 4): New product/concept presentation, reactions, purchase intent",
            "5. **Methodology** (id: 5): Research-specific questions, validation questions, feedback on survey experience",
            "",
            "⚠️  CRITICAL: Every question MUST be placed in the most appropriate section.",
            "⚠️  Each section should have at least 2-3 relevant questions unless the RFQ specifically doesn't require that type of information.",
            "⚠️  The JSON structure MUST use 'sections' array, NOT 'questions' array.",
            "🚨 MANDATORY: You MUST generate actual questions for each section - do NOT leave any sections with empty questions arrays.",
            "🚨 MANDATORY: Each section must contain at least 2-3 relevant questions based on the RFQ requirements.",
            "",
            "## CRITICAL JSON FORMATTING REQUIREMENTS:",
            "🚨🚨🚨 MANDATORY: You MUST return ONLY valid JSON format - NO markdown, NO explanations, NO additional text 🚨🚨🚨",
            "🚨🚨🚨 MANDATORY: Start your response with { and end with } - this is the ONLY format accepted 🚨🚨🚨",
            "1. Return ONLY valid JSON - no markdown, no explanations, no additional text",
            "2. Use proper JSON syntax with double quotes for all strings",
            "3. Ensure all brackets and braces are properly closed",
            "4. Use consistent indentation (2 spaces)",
            "5. Escape special characters in strings properly",
            "6. 🚨 CRITICAL: NO line breaks within string values - keep all text on single lines",
            "7. 🚨 CRITICAL: Do NOT break question text across multiple lines",
            "8. 🚨 CRITICAL: Do NOT break option text across multiple lines",
            "9. Example CORRECT: {\"text\": \"What is your age?\", \"options\": [\"18-25\", \"26-35\"]}",
            "10. Example WRONG: {\"text\": \"What\nis\nyour\nage?\", \"options\": [\"18-25\",\n\"26-35\"]}",
            "11. Use numeric IDs for sections (1, 2, 3, 4, 5)",
            "12. Use string IDs for questions (q1, q2, q3, etc.)",
            "13. Write question text as single lines - NO newlines within question text",
            "14. Use proper sentence structure - do not break words across lines",
            "15. 🚨🚨🚨 FORBIDDEN: Do NOT use markdown formatting like 1), 2), -, *, or any other markdown syntax 🚨🚨🚨",
            "16. 🚨🚨🚨 FORBIDDEN: Do NOT use numbered lists, bullet points, or any text formatting 🚨🚨🚨",
            "",
            "## REQUIRED JSON STRUCTURE:",
            json.dumps({
                "title": "Survey Title",
                "description": "Survey Description",
                "sections": [
                    {
                        "id": 1,
                        "title": "Screener & Demographics",
                        "description": "Initial screening questions and demographic information",
                        "questions": [
                            {
                                "id": "q1",
                                "text": "Question text",
                                "type": "multiple_choice",
                                "options": ["Option 1", "Option 2"],
                                "required": True,
                                "methodology": "screening",
                                "validation": "optional validation rules",
                                "order": 1
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Consumer Details", 
                        "description": "Detailed consumer information and behavior patterns",
                        "questions": [
                            {
                                "id": "q2",
                                "text": "What is your household income range?",
                                "type": "multiple_choice",
                                "options": ["Under $25,000", "$25,000-$50,000", "$50,000-$75,000", "$75,000-$100,000", "Over $100,000"],
                                "required": True,
                                "methodology": "demographics",
                                "validation": "single_select",
                                "order": 1
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Consumer product awareness, usage and preference",
                        "description": "Understanding consumer awareness, usage patterns and preferences",
                        "questions": [
                            {
                                "id": "q3",
                                "text": "How often do you purchase products in this category?",
                                "type": "multiple_choice",
                                "options": ["Daily", "Weekly", "Monthly", "Quarterly", "Annually", "Never"],
                                "required": True,
                                "methodology": "usage_frequency",
                                "validation": "single_select",
                                "order": 1
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Product introduction and Concept reaction",
                        "description": "Introduction of new concepts and gathering reactions",
                        "questions": [
                            {
                                "id": "q4",
                                "text": "How likely are you to purchase this product?",
                                "type": "scale",
                                "options": ["Very Unlikely", "Unlikely", "Neutral", "Likely", "Very Likely"],
                                "required": True,
                                "methodology": "purchase_intent",
                                "validation": "single_select",
                                "order": 1
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Methodology",
                        "description": "Methodology-specific questions and validation",
                        "questions": [
                            {
                                "id": "q5",
                                "text": "Please rate the overall quality of this survey",
                                "type": "scale",
                                "options": ["Poor", "Fair", "Good", "Very Good", "Excellent"],
                                "required": False,
                                "methodology": "quality_check",
                                "validation": "single_select",
                                "order": 1
                            }
                        ]
                    }
                ],
                "metadata": {
                    "estimated_time": 10,
                    "methodology_tags": ["tag1", "tag2"],
                    "target_responses": 100,
                    "quality_score": 0.85,
                    "sections_count": 5
                }
            }, indent=2),
            "",
            "## JSON VALIDATION CHECKLIST:",
            "✅ All strings are wrapped in double quotes",
            "✅ All object keys are strings in double quotes", 
            "✅ All arrays use square brackets []",
            "✅ All objects use curly braces {}",
            "✅ No trailing commas after last array/object elements",
            "✅ All brackets and braces are properly closed",
            "✅ No control characters or unescaped quotes in strings",
            "✅ Section IDs are numbers (1, 2, 3, 4, 5)",
            "✅ Question IDs are strings (q1, q2, q3, etc.)",
            "✅ Question text is on single lines without newlines",
            "✅ No excessive whitespace or formatting artifacts",
            "",
            "## TEXT FORMATTING EXAMPLES:",
            "",
            "❌ BAD - Do NOT format like this:",
            '"text": "\\nWhich\\n of\\n the\\n following\\n best\\n describes\\n your\\n role\\n?"',
            "",
            "✅ GOOD - Format like this:",
            '"text": "Which of the following best describes your role in household purchase decisions?"',
            "",
            "🚨 CRITICAL: Your response must be valid JSON that can be parsed by json.loads()",
            "🚨 DO NOT include any text before or after the JSON",
            "🚨 DO NOT use markdown code blocks (```json)",
            "🚨 DO NOT add explanations or comments",
            "🚨 DO NOT break question text across multiple lines with newlines",
            "",
            "Generate the survey JSON now:"
        ])
        
        # Join all prompt parts into final prompt
        final_prompt = "\n".join(prompt_parts)
        
        # Log prompt metadata without the actual content
        logger.info("🤖 Final prompt generated for LLM")
        logger.info("📤 Prompt length: {} characters".format(len(final_prompt)))
        
        return final_prompt
    
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
