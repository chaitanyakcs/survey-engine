"""
State-of-the-Art Prompt Builder System
Modular, efficient, and clean prompt generation for survey creation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import logging
from src.services.annotation_insights_service import AnnotationInsightsService

logger = logging.getLogger(__name__)


@dataclass
class PromptSection:
    """Represents a single section in the prompt"""
    title: str
    content: List[str]
    order: int = 0
    required: bool = True


@dataclass
class RAGContext:
    """Context from RAG/golden example retrieval"""
    example_count: int
    avg_quality_score: float
    methodology_tags: List[str]
    similarity_scores: List[float]


class SectionManager:
    """Manages prompt sections with clean organization"""

    def __init__(self) -> None:
        self.sections: Dict[str, PromptSection] = {}

    def add_section(self, key: str, section: PromptSection) -> None:
        """Add a section to the manager"""
        self.sections[key] = section

    def get_ordered_sections(self) -> List[PromptSection]:
        """Get sections in proper order"""
        return sorted(self.sections.values(), key=lambda s: s.order)

    def build_system_role_section(self) -> PromptSection:
        """Build the system role and expertise section"""
        content = [
            "# Expert Survey Designer and Market Research Specialist",
            "",
            "## Your Expertise:",
            "- Market research methodology design with 15+ years experience",
            "- Question design and survey optimization",
            "- Statistical analysis and data quality assurance",
            "- Industry best practices and compliance standards"
        ]
        return PromptSection("system_role", content, order=1)

    def build_methodology_section(self, methodology_tags: List[str], methodology_rules: Dict[str, Any]) -> PromptSection:
        """Build methodology requirements section"""
        if not methodology_tags:
            return PromptSection("methodology", [], order=2, required=False)

        content = ["## Methodology Requirements:", ""]

        for tag in methodology_tags:
            if tag.lower() in methodology_rules:
                method = methodology_rules[tag.lower()]
                content.extend([
                    f"### {method['description']}:",
                    f"- Required Questions: {method['required_questions']}",
                    f"- Validation Rules: {'; '.join(method['validation_rules'])}",
                    ""
                ])

        return PromptSection("methodology", content, order=2)

    def build_pillar_framework_section(self, pillar_rules_context: str) -> PromptSection:
        """Build the 5-pillar evaluation framework section"""
        content = [
            "## 5-PILLAR EVALUATION FRAMEWORK:",
            "Follow these comprehensive rules to ensure high-quality survey design:",
            ""
        ]

        if pillar_rules_context:
            content.append(pillar_rules_context)

        return PromptSection("pillar_framework", content, order=3)

    def build_rag_context_section(self, rag_context: Optional[RAGContext]) -> PromptSection:
        """Build RAG context section (replaces golden examples)"""
        if not rag_context or rag_context.example_count == 0:
            return PromptSection("rag_context", [], order=4, required=False)

        content = [
            "## CONTEXTUAL KNOWLEDGE:",
            f"Based on {rag_context.example_count} high-quality similar surveys retrieved via semantic matching:",
            f"- Average quality score: {rag_context.avg_quality_score:.2f}",
            f"- Primary methodologies: {', '.join(rag_context.methodology_tags)}",
            f"- Similarity range: {min(rag_context.similarity_scores):.3f} - {max(rag_context.similarity_scores):.3f}",
            "- Common patterns and best practices have been incorporated into the framework above",
            ""
        ]

        return PromptSection("rag_context", content, order=4)

    def build_current_task_section(self, rfq_details: Dict[str, Any]) -> PromptSection:
        """Build current RFQ task section"""
        content = [
            "## CURRENT RFQ:",
            f"**Title:** {rfq_details.get('title', 'N/A')}",
            f"**Description:** {rfq_details.get('text', '')}",
            f"**Category:** {rfq_details.get('category', 'N/A')}",
            f"**Target Segment:** {rfq_details.get('segment', 'N/A')}",
            f"**Research Goal:** {rfq_details.get('goal', 'N/A')}",
            ""
        ]

        return PromptSection("current_task", content, order=5)


class OutputFormatter:
    """Handles strict JSON formatting requirements"""

    @staticmethod
    def get_json_requirements_section() -> PromptSection:
        """Get the consolidated JSON formatting requirements"""
        content = [
            "## CRITICAL REQUIREMENT - SECTIONS FORMAT:",
            "🚨 MANDATORY: Generate survey using SECTIONS format with exactly 7 sections",
            "🚨 MANDATORY: Return ONLY valid JSON - NO markdown, explanations, or additional text",
            "🚨 MANDATORY: Start response with { and end with } - this is the ONLY format accepted",
            "🚨 MANDATORY: Include ALL required text blocks (introText, textBlocks, closingText) as specified in text requirements",
            "",
            "## SECTION ORGANIZATION:",
            "1. **Sample Plan** (id: 1): Participant qualification criteria, recruitment requirements, and quotas",
            "   - REQUIRED: Study_Intro in introText",
            "   - OPTIONAL: Confidentiality_Agreement in textBlocks (for sensitive methodologies)",
            "2. **Screener** (id: 2): Initial qualification questions and basic demographics",
            "   REQUIRED QUESTIONS:",
            "   - Recent participation check (market research in last 6 months)",
            "   - Conflict of interest screening (industry employment, competitors)",
            "   - Basic demographics (age, gender)",
            "   - Category usage qualification",
            "   SEQUENCING: General → Specific, terminate early if disqualified",
            "3. **Brand/Product Awareness & Usage** (id: 3): Brand recall, awareness funnel, and usage patterns",
            "   REQUIRED QUESTIONS (if brand study):",
            "   - Unaided brand recall (top-of-mind brands)",
            "   - Brand awareness funnel: Aware → Considered → Purchased → Continue → Preferred",
            "   - Product satisfaction ratings",
            "   - Usage frequency and patterns",
            "   - REQUIRED: Product_Usage in textBlocks (for product-related studies)",
            "4. **Concept Exposure** (id: 4): Product/concept introduction and reaction assessment",
            "   REQUIRED QUESTIONS (if concept testing):",
            "   - Concept introduction text",
            "   - Overall impression rating",
            "   - Purchase likelihood assessment",
            "   - REQUIRED: Concept_Intro in introText (for concept testing)",
            "5. **Methodology** (id: 5): Research-specific questions (Conjoint, Pricing, Feature Importance)",
            "   Van Westendorp REQUIRED (if pricing study):",
            "   - Too cheap price point",
            "   - Bargain/good value price point",
            "   - Getting expensive price point",
            "   - Too expensive price point",
            "   Gabor Granger REQUIRED (if pricing study):",
            "   - Sequential price acceptance questions",
            "6. **Additional Questions** (id: 6): Supplementary research questions and follow-ups",
            "7. **Programmer Instructions** (id: 7): Technical implementation notes and data specifications",
            "",
            "## JSON FORMATTING RULES:",
            "✅ All strings in double quotes, proper syntax, no trailing commas",
            "✅ Section IDs are numbers (1,2,3,4,5,6,7), Question IDs are strings (q1,q2,q3)",
            "✅ All question text on single lines - NO newlines within strings",
            "✅ No markdown formatting, bullet points, or special characters in text",
            "✅ Include text blocks (introText, textBlocks, closingText) with proper structure and labels",
            "✅ Text blocks MUST have: id, type, label, content, mandatory fields",
            "✅ Use correct labels: Study_Intro, Product_Usage, Concept_Intro, Confidentiality_Agreement",
            "",
            "## QUESTION TYPE GUIDELINES:",
            "📊 **matrix_likert**: For rating multiple attributes on a scale",
            "   - Format: Question text ending with '?', ':', or '.' followed by comma-separated attributes",
            "   - Examples: 'How important are the following when choosing a product? Comfort, Price, Quality, Brand reputation.'",
            "   - Examples: 'Rate the following features: Comfort, Price, Quality, Brand reputation.'",
            "   - Examples: 'Please evaluate these aspects. Comfort, Price, Quality, Brand reputation.'",
            "   - Structure: Attributes become table rows, options become columns with radio buttons",
            "   - Required: 'options' array with scale labels (e.g., ['Not important', 'Somewhat important', 'Very important'])",
            "",
            "🎯 **constant_sum**: For allocating points across multiple items",
            "   - Format: Question text with 'allocate X points across' followed by comma-separated items",
            "   - Example: 'Please allocate 100 points across the following features: Comfort, Price, Quality, Brand reputation.'",
            "   - Structure: Items become individual input fields with point allocation",
            "   - Required: No 'options' array needed - points are extracted from question text",
            "",
            "📋 **numeric_grid**: For collecting numeric values in a grid format",
            "   - Format: Question text with comma-separated items and 'options' for column headers",
            "   - Example: 'How much would you pay for each? Item1, Item2, Item3.' with options ['$0-10', '$10-20', '$20+']",
            "   - Structure: Items become rows, options become columns with number inputs",
            "   - Required: 'options' array for column headers",
            "",
            "💰 **numeric_open**: For open-ended numeric input (prices, quantities, etc.)",
            "   - Format: Question text asking for a specific numeric value",
            "   - Example: 'At what price per box would you consider this product too expensive? Please enter a price in your local currency.'",
            "   - Structure: Single numeric input with currency selection",
            "   - Required: No 'options' array needed - currency is auto-detected from question text",
            "   - Special: Van Westendorp questions use this type for price sensitivity",
            "",
            "## REQUIRED JSON STRUCTURE:"
        ]

        # Add the JSON schema example
        schema_example = {
            "title": "Survey Title",
            "description": "Survey Description",
            "sections": [
                {
                    "id": 1,
                    "title": "Sample Plan",
                    "description": "Participant qualification criteria, recruitment requirements, and quotas",
                    "introText": {
                        "id": "intro_1",
                        "type": "study_intro",
                        "content": "Thank you for agreeing to participate in this study...",
                        "mandatory": True,
                        "label": "Study_Intro"
                    },
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Question text on single line",
                            "type": "multiple_choice",
                            "options": ["Option 1", "Option 2"],
                            "required": True,
                            "methodology": "screening",
                            "order": 1
                        },
                        {
                            "id": "q2",
                            "text": "How important are the following when choosing a product? Comfort, Price, Quality, Brand reputation.",
                            "type": "matrix_likert",
                            "options": ["Not at all important", "Slightly important", "Moderately important", "Very important", "Extremely important"],
                            "required": True,
                            "methodology": "importance_rating",
                            "order": 2
                        },
                        {
                            "id": "q3",
                            "text": "Please allocate 100 points across the following features: Comfort, Price, Quality, Brand reputation.",
                            "type": "constant_sum",
                            "required": True,
                            "methodology": "feature_importance",
                            "order": 3
                        },
                        {
                            "id": "q4",
                            "text": "How much would you pay for each benefit? HydraGlyde Moisture Matrix, SmartShield Technology, Month-long comfort guarantee.",
                            "type": "numeric_grid",
                            "options": ["$0-5", "$5-10", "$10-15", "$15-20", "$20+"],
                            "required": True,
                            "methodology": "willingness_to_pay",
                            "order": 4
                        },
                        {
                            "id": "q5",
                            "text": "At what price per box of 6 monthly lenses would you consider this product too expensive? Please enter a price in your local currency.",
                            "type": "numeric_open",
                            "required": True,
                            "methodology": "van_westendorp_expensive",
                            "order": 5
                        }
                    ]
                },
                {
                    "id": 2,
                    "title": "Screener",
                    "description": "Initial qualification questions and basic demographics",
                    "questions": []
                },
                {
                    "id": 3,
                    "title": "Brand/Product Awareness & Usage",
                    "description": "Brand recall, awareness funnel, and usage patterns",
                    "textBlocks": [
                        {
                            "id": "text_3",
                            "type": "product_usage",
                            "content": "Before we begin, please tell us about your experience...",
                            "mandatory": True,
                            "label": "Product_Usage"
                        }
                    ],
                    "questions": []
                },
                {
                    "id": 4,
                    "title": "Concept Exposure",
                    "description": "Product/concept introduction and reaction assessment",
                    "introText": {
                        "id": "intro_4",
                        "type": "concept_intro",
                        "content": "Please review the following concept carefully...",
                        "mandatory": True,
                        "label": "Concept_Intro"
                    },
                    "questions": []
                },
                {
                    "id": 5,
                    "title": "Methodology",
                    "description": "Research-specific questions (Conjoint, Pricing, Feature Importance)",
                    "questions": []
                },
                {
                    "id": 6,
                    "title": "Additional Questions",
                    "description": "Supplementary research questions and follow-ups",
                    "questions": []
                },
                {
                    "id": 7,
                    "title": "Programmer Instructions",
                    "description": "Technical implementation notes and data specifications",
                    "questions": []
                }
            ],
            "metadata": {
                "estimated_time": 10,
                "methodology_tags": ["methodology"],
                "target_responses": 100,
                "sections_count": 7
            }
        }

        content.append(json.dumps(schema_example, indent=2))
        content.extend([
            "",
            "🚨 CRITICAL: Response must be valid JSON parseable by json.loads()",
            "🚨 Generate the survey JSON now:"
        ])

        return PromptSection("json_requirements", content, order=6)


class PromptBuilder:
    """Main prompt builder that orchestrates all components"""

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.section_manager = SectionManager()
        self.methodology_rules = {}
        self.pillar_rules = {}
        self._load_rules_from_database()

    def _load_rules_from_database(self) -> None:
        """Load rules from database"""
        if not self.db_session:
            return

        try:
            from src.database.models import SurveyRule

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

            # Load pillar rules
            pillar_rules = self.db_session.query(SurveyRule).filter(
                SurveyRule.rule_type.in_(['pillar', 'generation']),
                SurveyRule.is_active == True
            ).all()

            for rule in pillar_rules:
                if rule.category not in self.pillar_rules:
                    self.pillar_rules[rule.category] = []

                rule_content = rule.rule_content or {}
                if isinstance(rule_content, str):
                    import json
                    try:
                        rule_content = json.loads(rule_content)
                    except:
                        rule_content = {}

                self.pillar_rules[rule.category].append({
                    'id': str(rule.id),
                    'name': rule.rule_name,
                    'description': rule.rule_description,
                    'priority': rule_content.get('priority', 'medium'),
                    'generation_guideline': rule_content.get('generation_guideline', ''),
                    'implementation_notes': rule_content.get('implementation_notes', []),
                    'rule_type': rule.rule_type
                })

            logger.info(f"✅ [PromptBuilder] Loaded {len(self.methodology_rules)} methodology rules and {sum(len(rules) for rules in self.pillar_rules.values())} pillar rules")

        except Exception as e:
            logger.error(f"❌ [PromptBuilder] Failed to load rules from database: {e}")

    def get_pillar_rules_context(self) -> str:
        """Get formatted pillar rules context"""
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
            context_parts.append("Follow these core quality standards:")

            for rule in rules:
                if rule.get('rule_type') == 'generation':
                    priority_indicator = "🔴" if rule['priority'] == 'core' else "🟡" if rule['priority'] == 'high' else "🔵"
                    guideline = rule.get('generation_guideline', rule.get('description', ''))
                    context_parts.append(f"- {priority_indicator} {guideline}")

                    # Add implementation notes for core rules
                    if rule['priority'] == 'core' and rule.get('implementation_notes'):
                        for note in rule['implementation_notes'][:2]:
                            context_parts.append(f"  • {note}")

        return "\n".join(context_parts)

    async def build_survey_generation_prompt(
        self,
        rfq_text: str,
        context: Dict[str, Any],
        rag_context: Optional[RAGContext] = None,
        methodology_tags: Optional[List[str]] = None
    ) -> str:
        """Build the complete survey generation prompt"""

        # Extract RFQ details
        rfq_details = context.get("rfq_details", {})
        if "text" not in rfq_details:
            rfq_details["text"] = rfq_text

        # Get methodology tags
        if not methodology_tags:
            methodology_tags = []
            if rfq_details.get("methodology_tags"):
                methodology_tags.extend(rfq_details["methodology_tags"])

        # Build all sections
        self.section_manager.add_section("system_role",
            self.section_manager.build_system_role_section())

        if methodology_tags:
            self.section_manager.add_section("methodology",
                self.section_manager.build_methodology_section(methodology_tags, self.methodology_rules))

        pillar_context = self.get_pillar_rules_context()
        self.section_manager.add_section("pillar_framework",
            self.section_manager.build_pillar_framework_section(pillar_context))

        if rag_context:
            self.section_manager.add_section("rag_context",
                self.section_manager.build_rag_context_section(rag_context))

        # Add annotation insights section if available
        annotation_insights_section = await self._build_annotation_insights_section()
        if annotation_insights_section:
            self.section_manager.add_section("annotation_insights", annotation_insights_section)

        self.section_manager.add_section("current_task",
            self.section_manager.build_current_task_section(rfq_details))

        # Add text requirements section if enhanced RFQ data is available
        text_requirements_section = self._build_text_requirements_section(context)
        if text_requirements_section:
            self.section_manager.add_section("text_requirements", text_requirements_section)

        # Add survey structure requirements section if enhanced RFQ data is available
        survey_structure_section = self._build_survey_structure_section(context)
        if survey_structure_section:
            self.section_manager.add_section("survey_structure", survey_structure_section)

        # Add advanced classification section if enhanced RFQ data is available
        advanced_classification_section = self._build_advanced_classification_section(context)
        if advanced_classification_section:
            self.section_manager.add_section("advanced_classification", advanced_classification_section)

        self.section_manager.add_section("json_requirements",
            OutputFormatter.get_json_requirements_section())

        # Assemble final prompt
        prompt_parts = []
        for section in self.section_manager.get_ordered_sections():
            if section.required or section.content:
                prompt_parts.extend(section.content)
                prompt_parts.append("")

        final_prompt = "\n".join(prompt_parts).strip()

        logger.info(f"🤖 [PromptBuilder] Generated prompt: {len(final_prompt)} chars")

        return final_prompt

    def _build_text_requirements_section(self, context: Dict[str, Any]) -> Optional[PromptSection]:
        """Build text requirements section from enhanced RFQ data"""
        try:
            # Check if enhanced RFQ data is available in context
            enhanced_rfq_data = context.get("enhanced_rfq_data")
            
            # Import the enhanced RFQ converter utility
            from src.utils.enhanced_rfq_converter import generate_text_requirements

            # Generate text requirements from enhanced RFQ data
            if enhanced_rfq_data:
                text_requirements = generate_text_requirements(enhanced_rfq_data)
            else:
                # Fallback: Generate default text requirements based on methodology tags
                methodology_tags = context.get("rfq_details", {}).get("methodology_tags", [])
                if not methodology_tags:
                    methodology_tags = ["survey"]  # Default fallback
                
                # Create default text requirements
                text_requirements = self._generate_default_text_requirements(methodology_tags)

            if not text_requirements.strip():
                return None

            # Create the prompt section
            content = [
                "# 🚨 CRITICAL: MANDATORY TEXT BLOCK REQUIREMENTS 🚨",
                "",
                "⚠️ **ABSOLUTELY CRITICAL**: The following text requirements are MANDATORY and MUST be included in EVERY survey:",
                "",
                text_requirements,
                "",
                "🚨 **IMPLEMENTATION REQUIREMENTS - MUST FOLLOW EXACTLY:**",
                "1. **EVERY** mandatory text block MUST be included in the appropriate QNR section",
                "2. Use 'introText' for section introductions, 'textBlocks' for mid-section content, 'closingText' for endings",
                "3. Use the specified labels (e.g., 'Study_Intro', 'Concept_Intro', 'Survey_Closing') in the text block 'label' field",
                "4. Text blocks should have appropriate types: 'study_intro', 'concept_intro', 'product_usage', 'survey_closing', etc.",
                "5. Follow the 7-section QNR structure with proper text placement",
                "6. **MOST IMPORTANT**: Include 'closingText' in the final section for professional survey completion",
                "",
                "📋 **COMPLETE TEXT BLOCK EXAMPLES - COPY THESE EXACTLY:**",
                "",
                "=== SECTION 1 (Sample Plan) - Study Introduction ===",
                '```json',
                '"introText": {',
                '  "id": "intro_1",',
                '  "type": "study_intro",',
                '  "label": "Study_Intro",',
                '  "content": "Thank you for participating in this research study about contact lenses. The survey will take about 15 to 20 minutes. Your responses are confidential, reported in aggregate, and used for research purposes only. Participation is voluntary and you may stop at any time without penalty.",',
                '  "mandatory": true',
                '}',
                '```',
                "",
                "=== SECTION 3 (Brand/Product Awareness) - Product Usage ===",
                '```json',
                '"textBlocks": [',
                '  {',
                '    "id": "text_3",',
                '    "type": "product_usage",',
                '    "label": "Product_Usage",',
                '    "content": "Before we begin, please tell us about your experience with contact lenses and your current usage patterns.",',
                '    "mandatory": true',
                '  }',
                ']',
                '```',
                "",
                "=== SECTION 4 (Concept Exposure) - Concept Introduction ===",
                '```json',
                '"introText": {',
                '  "id": "intro_4",',
                '  "type": "concept_intro",',
                '  "label": "Concept_Intro",',
                '  "content": "Please review the following product concept carefully. We will ask you questions about your reactions and preferences.",',
                '  "mandatory": true',
                '}',
                '```',
                "",
                "=== SECTION 7 (Programmer Instructions) - Survey Closing ===",
                '```json',
                '"closingText": {',
                '  "id": "closing_1",',
                '  "type": "survey_closing",',
                '  "label": "Survey_Closing",',
                '  "content": "Thank you for completing this survey! Your responses are valuable and will help us better understand market preferences. If you have any questions about this research, please contact us at research@company.com. You may now close this window.",',
                '  "mandatory": true',
                '}',
                '```',
                "",
                "=== OPTIONAL: Confidentiality Agreement (if needed) ===",
                '```json',
                '"textBlocks": [',
                '  {',
                '    "id": "conf_1",',
                '    "type": "confidentiality_agreement",',
                '    "label": "Confidentiality_Agreement",',
                '    "content": "This research contains confidential information. Please do not share any details with others outside this study.",',
                '    "mandatory": true',
                '  }',
                ']',
                '```',
                "",
                "🚨 **MANDATORY VALIDATION CHECKLIST - VERIFY ALL BEFORE SUBMITTING:**",
                "- [ ] Study_Intro text block included in Section 1 (Sample Plan)",
                "- [ ] Product_Usage text block included in Section 3 (Brand/Product Awareness) if applicable",
                "- [ ] Concept_Intro text block included in Section 4 (Concept Exposure) if applicable",
                "- [ ] **Survey_Closing text block included in Section 7 (Programmer Instructions) - THIS IS MANDATORY**",
                "- [ ] All text blocks have correct 'label' field matching requirements",
                "- [ ] All text blocks have 'mandatory': true",
                "- [ ] All text blocks have proper 'type' field",
                "",
                "**QNR SECTION TEXT PLACEMENT MAPPING:**",
                "- **Sample Plan (Section 1)**: Study_Intro in introText, Confidentiality_Agreement in textBlocks (if needed)",
                "- **Brand/Product Awareness (Section 3)**: Product_Usage in textBlocks (if applicable)",
                "- **Concept Exposure (Section 4)**: Concept_Intro in introText (if applicable)",
                "- **Methodology (Section 5)**: Methodology-specific instructions in textBlocks (if needed)",
                "- **Programmer Instructions (Section 7)**: Survey_Closing in closingText (MANDATORY)",
                "",
                "🚨 **CRITICAL FAILURE WARNING:**",
                "🚨 **FAILURE TO INCLUDE THE SURVEY_CLOSING TEXT BLOCK WILL RESULT IN INVALID SURVEY** 🚨",
                "🚨 **FAILURE TO INCLUDE ANY REQUIRED TEXT BLOCKS WILL RESULT IN INVALID SURVEY** 🚨",
                ""
            ]

            return PromptSection(
                title="Text Requirements",
                content=content,
                order=5,  # Place after current task but before JSON requirements
                required=True
            )

        except Exception as e:
            logger.warning(f"⚠️ [PromptBuilder] Failed to build text requirements section: {str(e)}")
            return None

    def _build_survey_structure_section(self, context: Dict[str, Any]) -> Optional[PromptSection]:
        """Build survey structure requirements section from enhanced RFQ data"""
        try:
            # Check if enhanced RFQ data is available in context
            enhanced_rfq_data = context.get("enhanced_rfq_data")
            if not enhanced_rfq_data:
                return None

            survey_structure = enhanced_rfq_data.get("survey_structure", {})
            survey_logic = enhanced_rfq_data.get("survey_logic", {})
            brand_usage = enhanced_rfq_data.get("brand_usage_requirements", {})

            content = []

            # QNR Section Requirements
            qnr_sections = survey_structure.get("qnr_sections", [])
            if qnr_sections:
                content.extend([
                    "## 🏗️ CUSTOM QNR SECTION REQUIREMENTS:",
                    "",
                    "Based on user selections, the following sections MUST be included:",
                    ""
                ])

                section_names = {
                    "sample_plan": "Sample Plan (Section 1)",
                    "screener": "Screener (Section 2)", 
                    "brand_awareness": "Brand/Product Awareness (Section 3)",
                    "concept_exposure": "Concept Exposure (Section 4)",
                    "methodology_section": "Methodology (Section 5)",
                    "additional_questions": "Additional Questions (Section 6)",
                    "programmer_instructions": "Programmer Instructions (Section 7)"
                }

                for section_id in qnr_sections:
                    section_name = section_names.get(section_id, section_id)
                    content.append(f"✅ **{section_name}**: REQUIRED")

                content.extend(["", "⚠️ **IMPORTANT**: Only include the sections listed above. Do NOT include unselected sections."])

            # Survey Logic Requirements
            logic_requirements = []
            if survey_logic.get("requires_piping_logic"):
                logic_requirements.append("• **Piping Logic**: Carry forward responses between questions")
            if survey_logic.get("requires_sampling_logic"):
                logic_requirements.append("• **Sampling Logic**: Randomization and quota controls")
            if survey_logic.get("requires_screener_logic"):
                logic_requirements.append("• **Screener Logic**: Advanced qualification routing")
            if survey_logic.get("custom_logic_requirements"):
                logic_requirements.append(f"• **Custom Logic**: {survey_logic['custom_logic_requirements']}")

            if logic_requirements:
                content.extend([
                    "",
                    "## ⚙️ SURVEY LOGIC REQUIREMENTS:",
                    "",
                    "The following logic features MUST be implemented:"
                ])
                content.extend(logic_requirements)

            # Brand & Usage Requirements
            brand_requirements = []
            if brand_usage.get("brand_recall_required"):
                brand_requirements.append("• **Brand Recall Questions**: Unaided and aided brand awareness")
            if brand_usage.get("brand_awareness_funnel"):
                brand_requirements.append("• **Brand Awareness Funnel**: Awareness → Consideration → Trial → Purchase")
            if brand_usage.get("brand_product_satisfaction"):
                brand_requirements.append("• **Brand/Product Satisfaction**: Satisfaction and loyalty metrics")
            if brand_usage.get("usage_frequency_tracking"):
                brand_requirements.append("• **Usage Frequency Tracking**: Frequency, occasion, and context tracking")

            if brand_requirements:
                content.extend([
                    "",
                    "## 🏷️ BRAND & USAGE REQUIREMENTS:",
                    "",
                    "The following brand research elements MUST be included:"
                ])
                content.extend(brand_requirements)

            if not content:
                return None

            content.extend([
                "",
                "🚨 **IMPLEMENTATION**: These requirements must be reflected in the survey structure and question flow."
            ])

            return PromptSection(
                title="Survey Structure Requirements",
                content=content,
                order=4.5,  # Place after text requirements but before JSON requirements
                required=True
            )

        except Exception as e:
            logger.warning(f"⚠️ [PromptBuilder] Failed to build survey structure section: {str(e)}")
            return None

    def _build_advanced_classification_section(self, context: Dict[str, Any]) -> Optional[PromptSection]:
        """Build advanced classification requirements section from enhanced RFQ data"""
        try:
            # Check if enhanced RFQ data is available in context
            enhanced_rfq_data = context.get("enhanced_rfq_data")
            if not enhanced_rfq_data:
                return None

            advanced_classification = enhanced_rfq_data.get("advanced_classification", {})
            if not advanced_classification:
                return None

            content = []

            # Industry Classification
            industry_classification = advanced_classification.get("industry_classification")
            if industry_classification:
                content.extend([
                    "## 🏭 INDUSTRY CLASSIFICATION REQUIREMENTS:",
                    "",
                    f"**Target Industry**: {industry_classification}",
                    "",
                    "🚨 **CRITICAL**: Survey questions, terminology, and examples MUST be appropriate for this industry:",
                    f"- Use industry-specific language and terminology relevant to {industry_classification}",
                    "- Include industry-appropriate examples and scenarios",
                    "- Ensure question context matches industry standards and practices",
                    "- Consider industry-specific regulations and compliance requirements",
                    ""
                ])

            # Respondent Classification
            respondent_classification = advanced_classification.get("respondent_classification")
            if respondent_classification:
                content.extend([
                    "## 👥 RESPONDENT CLASSIFICATION REQUIREMENTS:",
                    "",
                    f"**Target Respondents**: {respondent_classification}",
                    "",
                    "🚨 **CRITICAL**: Survey design MUST be tailored for this respondent type:",
                    f"- Adjust question complexity and language for {respondent_classification}",
                    "- Use appropriate terminology and examples for this audience",
                    "- Consider respondent expertise level and familiarity with industry concepts",
                    "- Ensure question flow and logic matches respondent expectations",
                    ""
                ])

            # Methodology Tags
            methodology_tags = advanced_classification.get("methodology_tags", [])
            if methodology_tags:
                content.extend([
                    "## 📊 METHODOLOGY CLASSIFICATION REQUIREMENTS:",
                    "",
                    f"**Required Methodologies**: {', '.join(methodology_tags)}",
                    "",
                    "🚨 **CRITICAL**: Survey MUST implement these specific methodologies:"
                ])

                methodology_requirements = {
                    "quantitative": "• Include statistical analysis-ready questions with rating scales, multiple choice, and numerical inputs",
                    "qualitative": "• Include open-ended questions and detailed feedback collection mechanisms",
                    "attitudinal": "• Focus on opinions, preferences, and subjective assessments with Likert scales",
                    "behavioral": "• Include questions about past actions, usage patterns, and behavioral data",
                    "brand_tracking": "• Include brand awareness, recognition, and perception questions with unaided/aided recall",
                    "customer_satisfaction": "• Include satisfaction ratings, NPS questions, and service quality assessments",
                    "pricing_research": "• Include price sensitivity, willingness to pay, and value perception questions",
                    "market_sizing": "• Include market size estimation, penetration, and growth questions",
                    "mixed_methods": "• Combine quantitative and qualitative approaches with both structured and open-ended questions",
                    "concept_testing": "• Include concept introduction, evaluation, and purchase intent questions",
                    "segmentation": "• Include demographic, psychographic, and behavioral segmentation questions",
                    "competitive_analysis": "• Include competitive awareness, preference, and comparison questions"
                }

                for tag in methodology_tags:
                    tag_lower = tag.lower().replace(' ', '_')
                    if tag_lower in methodology_requirements:
                        content.append(methodology_requirements[tag_lower])

                content.append("")

            # Compliance Requirements
            compliance_requirements = advanced_classification.get("compliance_requirements", [])
            if compliance_requirements:
                content.extend([
                    "## ⚖️ COMPLIANCE REQUIREMENTS:",
                    "",
                    f"**Required Compliance**: {', '.join(compliance_requirements)}",
                    "",
                    "🚨 **CRITICAL**: Survey MUST meet these compliance standards:"
                ])

                compliance_requirements_map = {
                    "standard_data_protection": "• Include data protection notices and consent mechanisms",
                    "gdpr_compliance": "• Include GDPR-compliant consent forms, data processing notices, and right to deletion information",
                    "hipaa_compliance": "• Include HIPAA-compliant health information protection and consent mechanisms",
                    "iso_27001": "• Include ISO 27001-compliant security and data handling notices",
                    "soc_2_compliance": "• Include SOC 2-compliant security and availability notices",
                    "custom_compliance": "• Include custom compliance requirements as specified by the client"
                }

                for compliance in compliance_requirements:
                    compliance_lower = compliance.lower().replace(' ', '_')
                    if compliance_lower in compliance_requirements_map:
                        content.append(compliance_requirements_map[compliance_lower])

                content.extend([
                    "",
                    "⚠️ **IMPLEMENTATION**: Include appropriate legal notices, consent forms, and data protection information in text blocks."
                ])

            if not content:
                return None

            content.extend([
                "",
                "🚨 **IMPLEMENTATION**: These classification requirements must be reflected in survey design, question wording, and compliance measures."
            ])

            return PromptSection(
                title="Advanced Classification Requirements",
                content=content,
                order=4.7,  # Place after survey structure but before JSON requirements
                required=True
            )

        except Exception as e:
            logger.warning(f"⚠️ [PromptBuilder] Failed to build advanced classification section: {str(e)}")
            return None

    def _generate_default_text_requirements(self, methodology_tags: List[str]) -> str:
        """Generate default text requirements based on methodology tags"""
        # Default text requirements mapping
        default_requirements = {
            "van_westendorp": ["Study_Intro", "Product_Usage"],
            "gabor_granger": ["Study_Intro", "Product_Usage"],
            "conjoint": ["Study_Intro", "Confidentiality_Agreement"],
            "concept_test": ["Study_Intro", "Concept_Intro"],
            "brand_tracker": ["Study_Intro", "Product_Usage"],
            "pricing": ["Study_Intro", "Product_Usage"],
            "survey": ["Study_Intro"]  # Default fallback
        }
        
        # Find matching requirements
        required_texts = set()
        for tag in methodology_tags:
            tag_lower = tag.lower()
            if tag_lower in default_requirements:
                required_texts.update(default_requirements[tag_lower])
        
        # Always include Study_Intro and Survey_Closing as mandatory defaults
        required_texts.add("Study_Intro")
        required_texts.add("Survey_Closing")
        if not required_texts:
            required_texts.add("Study_Intro")
        
        # Generate text requirements
        sections = []
        sections.append("### Study Introduction (REQUIRED at beginning):")
        sections.append("- Thank participants for participation")
        sections.append("- Explain study purpose and estimated completion time")
        sections.append("- Provide confidentiality assurances")
        sections.append("- Mention voluntary participation and withdrawal rights")
        sections.append("")
        
        if "Product_Usage" in required_texts:
            sections.append("### Product Usage Introduction (REQUIRED before usage questions):")
            sections.append("- Introduce product category")
            sections.append("- Request experience information")
            sections.append("- Explain qualification purpose")
            sections.append("")
        
        if "Concept_Intro" in required_texts:
            sections.append("### Concept Introduction (REQUIRED before concept evaluation):")
            sections.append("- Present concept details clearly")
            sections.append("- Include any stimuli or materials")
            sections.append("- Instruct participants to review carefully")
            sections.append("")
        
        if "Confidentiality_Agreement" in required_texts:
            sections.append("### Confidentiality Agreement (REQUIRED):")
            sections.append("- Assure response confidentiality")
            sections.append("- Explain research-only usage")
            sections.append("- Confirm no third-party sharing")
            sections.append("")
        
        if "Survey_Closing" in required_texts:
            sections.append("### Survey Closing (MANDATORY at end):")
            sections.append("- Thank participants for completion")
            sections.append("- Acknowledge value of their responses")
            sections.append("- Provide contact information for questions")
            sections.append("- Give clear completion instructions")
            sections.append("")
        
        sections.append("**IMPORTANT**: These text introductions must appear as standalone content blocks before their related question sections, not as question text.")
        
        return "\n".join(sections)
    
    async def _build_annotation_insights_section(self) -> Optional[PromptSection]:
        """Build annotation insights section with quality guidelines from expert feedback"""
        try:
            if not self.db_session:
                return None
            
            # Get annotation insights
            insights_service = AnnotationInsightsService(self.db_session)
            guidelines = await insights_service.get_quality_guidelines()
            
            if not guidelines.get("high_quality_examples") and not guidelines.get("avoid_patterns"):
                return None
            
            content = [
                "# 📊 Quality Standards (Based on Expert Review)",
                "",
                "The following guidelines are derived from expert annotations of survey quality. Use these patterns to create high-quality surveys:",
                ""
            ]
            
            # Add high-quality examples
            if guidelines.get("high_quality_examples"):
                content.extend([
                    "## ✅ HIGH-QUALITY PATTERNS (Score 4-5):",
                    ""
                ])
                
                for example in guidelines["high_quality_examples"][:3]:  # Top 3 examples
                    content.extend([
                        f"**{example['type'].replace('_', ' ').title()} Questions:**",
                        f"- Example: \"{example['example']}\"",
                        f"- Expert Score: {example['score']:.1f}/5",
                        f"- Context: {example.get('context', 'No additional context')}",
                        ""
                    ])
            
            # Add patterns to avoid
            if guidelines.get("avoid_patterns"):
                content.extend([
                    "## ❌ AVOID THESE PATTERNS (Score 1-2):",
                    ""
                ])
                
                for pattern in guidelines["avoid_patterns"][:3]:  # Top 3 patterns
                    content.extend([
                        f"**{pattern['pattern'].replace('_', ' ').title()}:**",
                        f"- Examples: {', '.join(pattern['examples'][:2])}",
                        ""
                    ])
            
            # Add common issues
            if guidelines.get("common_issues"):
                content.extend([
                    "## 🚨 COMMON ISSUES FROM EXPERT FEEDBACK:",
                    ""
                ])
                
                for issue in guidelines["common_issues"][:5]:  # Top 5 issues
                    content.extend([
                        f"**{issue['issue'].replace('_', ' ').title()}** (mentioned {issue['frequency']} times):",
                        f"- Example: \"{issue['examples'][0] if issue['examples'] else 'No examples available'}\"",
                        ""
                    ])
            
            content.extend([
                "## 🎯 IMPLEMENTATION GUIDELINES:",
                "",
                "1. **Follow High-Quality Patterns**: Use the examples above as templates for similar questions",
                "2. **Avoid Problematic Patterns**: Steer clear of the patterns that consistently score low",
                "3. **Address Common Issues**: Be mindful of the issues experts frequently flag",
                "4. **Quality Over Speed**: Take time to craft clear, unbiased questions",
                "5. **Test for Clarity**: Ensure questions are easy to understand and answer",
                ""
            ])
            
            return PromptSection(
                title="Quality Standards from Expert Review",
                content=content,
                order=3,  # After methodology, before current task
                required=True
            )
            
        except Exception as e:
            logger.warning(f"⚠️ [PromptBuilder] Failed to build annotation insights section: {e}")
            return None