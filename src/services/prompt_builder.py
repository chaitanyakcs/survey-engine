"""
State-of-the-Art Prompt Builder System
Modular, efficient, and clean prompt generation for survey creation
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import logging

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

    def __init__(self):
        self.sections: Dict[str, PromptSection] = {}

    def add_section(self, key: str, section: PromptSection):
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
            "- Industry best practices and compliance standards",
            "",
            "## Core Design Principles:",
            "- Prioritize data quality and respondent experience",
            "- Design surveys that are clear, unbiased, and actionable",
            "- Follow established research methodologies rigorously",
            "- Ensure questions are specific, measurable, and relevant",
            "- Maintain logical flow and appropriate question sequencing"
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
            "🚨 MANDATORY: Generate survey using SECTIONS format with exactly 5 sections",
            "🚨 MANDATORY: Return ONLY valid JSON - NO markdown, explanations, or additional text",
            "🚨 MANDATORY: Start response with { and end with } - this is the ONLY format accepted",
            "",
            "## SECTION ORGANIZATION:",
            "1. **Screener & Demographics** (id: 1): Age, location, income, qualifying criteria",
            "2. **Consumer Details** (id: 2): Lifestyle, behavior patterns, detailed consumer profile",
            "3. **Consumer product awareness, usage and preference** (id: 3): Brand awareness, usage, preferences",
            "4. **Product introduction and Concept reaction** (id: 4): New concepts, reactions, purchase intent",
            "5. **Methodology** (id: 5): Research-specific questions, validation, survey feedback",
            "",
            "## JSON FORMATTING RULES:",
            "✅ All strings in double quotes, proper syntax, no trailing commas",
            "✅ Section IDs are numbers (1,2,3,4,5), Question IDs are strings (q1,q2,q3)",
            "✅ All question text on single lines - NO newlines within strings",
            "✅ No markdown formatting, bullet points, or special characters in text",
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
                    "title": "Screener & Demographics",
                    "description": "Initial screening and demographic information",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "Question text on single line",
                            "type": "multiple_choice",
                            "options": ["Option 1", "Option 2"],
                            "required": True,
                            "methodology": "screening",
                            "order": 1
                        }
                    ]
                }
            ],
            "metadata": {
                "estimated_time": 10,
                "methodology_tags": ["methodology"],
                "target_responses": 100,
                "sections_count": 5
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

    def _load_rules_from_database(self):
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

    def build_survey_generation_prompt(
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

        self.section_manager.add_section("current_task",
            self.section_manager.build_current_task_section(rfq_details))

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