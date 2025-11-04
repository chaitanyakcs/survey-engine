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


@dataclass
class PromptModule:
    """Base class for prompt modules - represents a major section of the prompt"""
    name: str
    order: int
    sections: List[PromptSection]
    required: bool = True
    
    def format_output(self) -> str:
        """Format this module's sections into prompt text"""
        if not self.sections:
            return ""
        
        parts = [f"\n{'='*80}\n{self.name.upper()}\n{'='*80}\n"]
        for section in sorted(self.sections, key=lambda s: s.order):
            if section.content:
                parts.append("\n".join(section.content))
                parts.append("\n")
        
        return "\n".join(parts)


class RoleModule:
    """MODULE 1: Role and Objective"""
    
    @staticmethod
    def build(context: Dict[str, Any]) -> PromptModule:
        """Build role and objective sections"""
        sections = []
        
        # Role definition
        role_content = [
            "# ROLE: Expert Survey Designer and Market Research Specialist",
            "",
            "You are an expert market research professional with 15+ years of experience in:",
            "- Survey methodology design (taste tests, NPS, brand tracking, pricing research)",
            "- Question crafting and survey optimization",
            "- Statistical analysis and data quality assurance",
            "- Industry best practices and compliance standards",
            "",
            "## YOUR OBJECTIVE:",
            "Transform the provided RFQ into a field-ready, professional QNR (questionnaire) that:",
            "1. Matches the depth, structure, and quality of reference golden examples",
            "2. Follows all mandatory quality requirements precisely",
            "3. Includes appropriate question density for the methodology",
            "4. Contains all required text blocks (introductions, instructions, closing)",
            "5. Generates valid, parseable JSON output",
            "",
            "## SUCCESS CRITERIA:",
            "Your survey will be evaluated against golden reference surveys. It must:",
            "- Match question count and depth (±20% of similar examples)",
            "- Include all mandatory text blocks in proper sections",
            "- Follow methodology-specific patterns (e.g., rating batteries for taste tests)",
            "- Include appropriate follow-up questions for open-ended insights",
            "- Be ready for field deployment without manual editing"
        ]
        
        sections.append(PromptSection("role", role_content, order=1.1))
        
        return PromptModule(
            name="MODULE 1: ROLE AND OBJECTIVE",
            order=1,
            sections=sections,
            required=True
        )


class InputsModule:
    """MODULE 2: Inputs - Background and Context"""
    
    @staticmethod
    def build(context: Dict[str, Any], rfq_text: str) -> PromptModule:
        """Build inputs and context sections"""
        sections = []
        
        # RFQ Input
        rfq_content = [
            "# RFQ INPUT (Request for Quotation)",
            "",
            "## Original RFQ Text:",
            rfq_text,
            ""
        ]
        sections.append(PromptSection("rfq_input", rfq_content, order=2.1))
        
        # QNR Structure
        structure_content = [
            "# QNR STRUCTURE - 7-Section Framework",
            "",
            "Your survey MUST follow this exact 7-section structure:",
            "",
            "## Section 1: Sample Plan",
            "Purpose: Sample quotas, screening criteria, demographic targets",
            "Text blocks: Study_Intro (introText - MANDATORY)",
            "",
            "## Section 2: Screener",
            "Purpose: Qualification questions to identify eligible respondents",
            "Text blocks: Screener intro (introText - MANDATORY)",
            "",
            "## Section 3: Brand/Product Awareness",
            "Purpose: Brand awareness, usage, and familiarity questions",
            "Text blocks: Section intro (introText - MANDATORY)",
            "",
            "## Section 4: Concept Exposure",
            "Purpose: Main research content - product/concept evaluation",
            "Text blocks: Concept/Product instructions (introText - MANDATORY)",
            "",
            "## Section 5: Methodology",
            "Purpose: Methodology-specific questions (pricing, MaxDiff, etc.)",
            "Text blocks: Methodology instructions (introText - MANDATORY)",
            "",
            "## Section 6: Additional Questions",
            "Purpose: Demographics, psychographics, behavioral questions",
            "Text blocks: Section intro (introText - MANDATORY)",
            "",
            "## Section 7: Programmer Instructions",
            "Purpose: Technical routing, quotas, termination rules",
            "Text blocks: Survey_Closing (closingText - MANDATORY)",
            ""
        ]
        sections.append(PromptSection("qnr_structure", structure_content, order=2.2))
        
        # Additional Research Context
        context_parts = [
            "# ADDITIONAL RESEARCH CONTEXT",
            ""
        ]
        
        rfq_details = context.get("rfq_details", {})
        if rfq_details.get("methodology_tags"):
            context_parts.append(f"**Methodology Tags**: {', '.join(rfq_details['methodology_tags'])}")
        if rfq_details.get("research_goal"):
            context_parts.append(f"**Research Goal**: {rfq_details['research_goal']}")
        if rfq_details.get("industry_category"):
            context_parts.append(f"**Industry**: {rfq_details['industry_category']}")
        if rfq_details.get("target_segment"):
            context_parts.append(f"**Target Audience**: {rfq_details['target_segment']}")
        
        context_parts.append("")
        
        sections.append(PromptSection("research_context", context_parts, order=2.3))
        
        return PromptModule(
            name="MODULE 2: INPUTS - Background and Context",
            order=2,
            sections=sections,
            required=True
        )


class InstructionModule:
    """MODULE 3: Instructions - How to Generate (MOST CRITICAL)"""
    
    @staticmethod
    def build(context: Dict[str, Any], methodology_tags: List[str], pillar_rules_context: str) -> PromptModule:
        """Build comprehensive instruction sections"""
        sections = []
        
        # 3.1 Mandatory Quality Instructions
        mandatory_content = [
            "# 3.1 MANDATORY QUALITY REQUIREMENTS",
            "",
            "These requirements are ABSOLUTE and NON-NEGOTIABLE:",
            "",
            "## Survey Structure:",
            "- MUST generate exactly 7 sections (Sample Plan, Screener, Brand/Product Awareness, Concept Exposure, Methodology, Additional Questions, Programmer Instructions)",
            "- Each section MUST have an integer 'id' field (1-7)",
            "",
            "## Text Blocks - CRITICAL:",
            "- Sections 1-6: MUST have 'introText' field with welcome/context",
            "- Section 7: MUST have 'closingText' field thanking respondent",
            "- All text blocks MUST have: id, type, label, content, mandatory: true",
            "- NO empty text blocks, NO placeholder text",
            "",
            "## Question Quality:",
            "- NO placeholder text like [BRAND NAME], [PRODUCT], [CONCEPT]",
            "- Extract actual names from RFQ",
            "- NO programming instructions in question text",
            "- Remove [SHOW], [RANDOMIZE], [IF RESPONSE], etc.",
            "- Clean, respondent-facing language only",
            "",
            "## JSON Format:",
            "- Valid JSON parseable by json.loads()",
            "- No line breaks within string values",
            "- Proper quotes, commas, brackets",
            "- NO markdown, NO explanations outside JSON",
            ""
        ]
        sections.append(PromptSection("mandatory_quality", mandatory_content, order=3.1))
        
        # 3.2 Methodology-Specific Depth Requirements (NEW - KEY FIX)
        methodology_depth = [
            "# 3.2 METHODOLOGY-SPECIFIC DEPTH REQUIREMENTS",
            "",
            "Match the question depth and patterns of the methodology:",
            ""
        ]
        
        # Add methodology-specific guidance
        methodology_lower = [tag.lower() for tag in methodology_tags]
        
        if any(tag in ['taste_test', 'sensory', 'clt', 'blind_taste_test', 'central_location_testing'] for tag in methodology_lower):
            methodology_depth.extend([
                "## TASTE TEST / SENSORY EVALUATION:",
                "**Question Density**: 60-120 questions typical (multiple samples × attributes)",
                "",
                "**Required Question Batteries** (for EACH sample):",
                "1. Visual attributes (appearance, color, clarity) - 2-4 rating questions",
                "2. Aroma/Smell attributes (intensity, character, notes) - 3-6 rating questions",
                "3. Taste attributes (flavor, sweetness, bitterness, etc.) - 5-8 rating questions",
                "4. Mouthfeel attributes (smoothness, texture, body) - 2-4 rating questions",
                "5. Aftertaste attributes (length, character) - 2-3 rating questions",
                "6. Overall liking - 1-2 rating questions",
                "",
                "**Rating Scales**: Typically 11-point (1-11) or 5-point scales",
                "**Follow-ups**: ASK IF CODED 7-11: 'What did you like?' (open-ended)",
                "**Follow-ups**: ASK IF CODED 1-6: 'What could be improved?' (open-ended)",
                "",
                "**Critical**: 30-50 rating questions PER SAMPLE is normal for comprehensive sensory testing",
                ""
            ])
        
        if 'nps' in methodology_lower or 'net_promoter' in methodology_lower:
            methodology_depth.extend([
                "## NPS (NET PROMOTER SCORE):",
                "**Question Density**: 2-5 questions",
                "",
                "**MANDATORY Questions**:",
                "1. NPS Score: 0-10 scale ('How likely to recommend?')",
                "2. NPS Follow-up (MANDATORY): 'Why did you give this score?' (open-ended)",
                "3. Optional: Relationship questions, competitive comparison",
                ""
            ])
        
        if any(tag in ['van_westendorp', 'gabor_granger', 'pricing'] for tag in methodology_lower):
            methodology_depth.extend([
                "## PRICING RESEARCH:",
                "**Van Westendorp**: Exactly 4 price questions (too cheap, cheap, expensive, too expensive)",
                "**Gabor-Granger**: Purchase intent at each price point (4-6 price levels)",
                "**Question Density**: 4-8 pricing questions + context questions",
                ""
            ])
        
        if 'brand_tracking' in methodology_lower:
            methodology_depth.extend([
                "## BRAND TRACKING:",
                "**Question Density**: 15-25 questions",
                "**Required Flow**: Awareness → Usage → Preference → Perception cascade",
                ""
            ])
        
        methodology_depth.extend([
            "**CRITICAL**: Review golden examples for question count and depth expectations",
            "Your survey should match within ±20% of similar reference surveys",
            ""
        ])
        
        sections.append(PromptSection("methodology_depth", methodology_depth, order=3.2))
        
        # 3.3 Question and Option Guidelines (NEW - FOLLOW-UPS FIX)
        question_guidelines = [
            "# 3.3 QUESTION AND OPTION LEVEL GUIDELINES",
            "",
            "## Follow-up Question Patterns:",
            "Many methodologies require follow-up questions. Common patterns:",
            "",
            "### Pattern 1: Rating Scale Follow-ups",
            "After a rating/scale question, often ask WHY:",
            "",
            "**Example**:",
            "```json",
            "{",
            '  "id": "q_liking",',
            '  "text": "How much did you like this sample? (1=Dislike extremely, 11=Like extremely)",',
            '  "type": "scale",',
            '  "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],',
            '  "required": true',
            "},",
            "{",
            '  "id": "q_liking_positive",',
            '  "text": "ASK IF CODED 7 TO 11 IN q_liking: What did you like about this sample?",',
            '  "type": "open_ended",',
            '  "required": false',
            "}",
            "```",
            "",
            "### Pattern 2: Multiple Choice Follow-ups",
            "If respondent selects 'Other', ask for specification:",
            "",
            "**Example**:",
            "```json",
            "{",
            '  "text": "Which brands are you aware of?",',
            '  "type": "multiple_choice",',
            '  "options": ["Brand A", "Brand B", "Brand C", "Other"]',
            "},",
            "{",
            '  "text": "ASK IF CODED \'Other\': Please specify which other brand",',
            '  "type": "open_ended"',
            "}",
            "```",
            "",
            "### Pattern 3: Screener Follow-ups",
            "Based on qualification, route to detailed questions or termination",
            "",
            "**Implementation Tips**:",
            "- Document conditions in question text: 'ASK IF CODED...'",
            "- Use open-ended type for follow-up questions",
            "- Typical ratio: 10-15% of rating questions should have follow-ups",
            "",
            "## Question Type Selection:",
            "- Use 'scale' for rating questions (with numeric options)",
            "- Use 'matrix_likert' for attribute batteries (multiple items, same scale)",
            "- Use 'open_ended' for qualitative follow-ups",
            "- Use 'multiple_choice' for lists with single selection",
            "- Use 'multiple_select' for check-all-that-apply",
            "",
            "## Option Formatting:",
            "- NO programmer codes in options: Use 'Male' not '01 | Male'",
            "- NO special instructions: Remove [RANDOMIZE], [ANCHOR], etc.",
            "- Clean, respondent-facing text only",
            ""
        ]
        sections.append(PromptSection("question_guidelines", question_guidelines, order=3.3))
        
        # 3.4 Evaluation Framework (condensed)
        if pillar_rules_context:
            eval_content = [
                "# 3.4 EVALUATION FRAMEWORK - Quality Standards",
                "",
                "Your survey will be evaluated on these pillars:",
                "",
                pillar_rules_context,
                ""
            ]
            sections.append(PromptSection("evaluation_framework", eval_content, order=3.4))
        
        # 3.5 Static Text Requirements (NEW - TEXT BLOCKS FIX)
        static_text = [
            "# 3.5 STATIC TEXT BLOCK REQUIREMENTS",
            "",
            "Every survey MUST include these text blocks with proper structure:",
            "",
            "## SECTION 1 - Sample Plan:",
            "### MANDATORY: introText (Study_Intro)",
            "```json",
            '"introText": {',
            '  "id": "intro_1",',
            '  "type": "study_intro",',
            '  "label": "Study_Intro",',
            '  "content": "Thank you for agreeing to participate in this research study. We are conducting a survey about [TOPIC from RFQ]. The survey will take approximately [X] minutes. Your participation is voluntary, and you may stop at any time. Your responses will be kept confidential and used for research purposes only.",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "### OPTIONAL: textBlocks (Confidentiality Agreement)",
            "```json",
            '"textBlocks": [{',
            '  "id": "text_1_1",',
            '  "type": "confidentiality",',
            '  "label": "Confidentiality_Agreement",',
            '  "content": "Confidentiality Agreement: Your identity will not be linked to your answers. Results will be used for research purposes only and shared in aggregate. Do not attempt to identify any product or brand during the study.",',
            '  "mandatory": true',
            "}]",
            "```",
            "",
            "## SECTION 2 - Screener:",
            "### MANDATORY: introText",
            "```json",
            '"introText": {',
            '  "id": "intro_2",',
            '  "type": "section_intro",',
            '  "label": "Screener_Intro",',
            '  "content": "We will now ask a few questions to confirm your eligibility for this study.",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "## SECTION 3 - Brand/Product Awareness:",
            "### MANDATORY: introText",
            "```json",
            '"introText": {',
            '  "id": "intro_3",',
            '  "type": "section_intro",',
            '  "label": "Brand_Awareness_Intro",',
            '  "content": "In this section, we will ask about your awareness and experience with various brands/products.",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "### OPTIONAL: textBlocks (if product usage context needed)",
            "```json",
            '"textBlocks": [{',
            '  "id": "text_3_1",',
            '  "type": "product_usage",',
            '  "label": "Product_Usage",',
            '  "content": "Please think about your usage and experiences with these products over the past [timeframe].",',
            '  "mandatory": true',
            "}]",
            "```",
            "",
            "## SECTION 4 - Concept Exposure:",
            "### MANDATORY: introText (for concept/product evaluation)",
            "```json",
            '"introText": {',
            '  "id": "intro_4",',
            '  "type": "concept_intro",',
            '  "label": "Concept_Intro",',
            '  "content": "You will now be presented with [product/concept description]. Please evaluate it carefully based on the following questions. [Add specific instructions like \'Do not attempt to guess the brand\' for blind tests]",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "## SECTION 5 - Methodology:",
            "### MANDATORY: introText",
            "```json",
            '"introText": {',
            '  "id": "intro_5",',
            '  "type": "section_intro",',
            '  "label": "Methodology_Intro",',
            '  "content": "[Methodology-specific instructions - e.g., for pricing: \'We will now ask about your price perceptions\', for MaxDiff: \'You will see sets of features...\']",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "## SECTION 6 - Additional Questions:",
            "### MANDATORY: introText",
            "```json",
            '"introText": {',
            '  "id": "intro_6",',
            '  "type": "section_intro",',
            '  "label": "Demographics_Intro",',
            '  "content": "Finally, we have a few questions about you for classification purposes only.",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "## SECTION 7 - Programmer Instructions:",
            "### MANDATORY: closingText (Survey_Closing)",
            "```json",
            '"closingText": {',
            '  "id": "closing_7",',
            '  "type": "survey_closing",',
            '  "label": "Survey_Closing",',
            '  "content": "Thank you for completing this survey. Your feedback is valuable and will help us [purpose from RFQ]. Your responses have been recorded. You may now close this window.",',
            '  "mandatory": true',
            "}",
            "```",
            "",
            "## IMPLEMENTATION CHECKLIST:",
            "Before submitting, verify:",
            "- [ ] Section 1 has introText (Study_Intro)",
            "- [ ] Section 2 has introText (Screener context)",
            "- [ ] Section 3 has introText (Brand awareness context)",
            "- [ ] Section 4 has introText (Concept/Product instructions)",
            "- [ ] Section 5 has introText (Methodology instructions)",
            "- [ ] Section 6 has introText (Demographics context)",
            "- [ ] Section 7 has closingText (Survey_Closing)",
            "- [ ] All text blocks have: id, type, label, content, mandatory: true",
            "- [ ] Content is customized to RFQ (not generic placeholders)",
            "",
            "🚨 MISSING ANY TEXT BLOCK = INVALID SURVEY 🚨",
            ""
        ]
        sections.append(PromptSection("static_text_requirements", static_text, order=3.5))
        
        return PromptModule(
            name="MODULE 3: INSTRUCTIONS - How to Generate",
            order=3,
            sections=sections,
            required=True
        )


class ExampleModule:
    """MODULE 4: Examples - Reference Surveys and Patterns"""
    
    @staticmethod
    def build(golden_examples: List[Dict[str, Any]], rag_context: Optional[RAGContext],
              golden_questions: List[Dict[str, Any]]) -> PromptModule:
        """Build example sections showing golden patterns"""
        sections = []
        
        # 4.1 Golden Examples as Reference
        if rag_context and rag_context.example_count > 0:
            golden_content = [
                "# 4.1 REFERENCE GOLDEN SURVEYS",
                "",
                f"You have {rag_context.example_count} high-quality reference survey(s) to guide your generation.",
                f"Average quality score: {rag_context.avg_quality_score:.2f}/1.0",
                ""
            ]
            
            if rag_context.methodology_tags:
                golden_content.append(f"**Methodologies**: {', '.join(rag_context.methodology_tags)}")
                golden_content.append("")
            
            golden_content.extend([
                "## CRITICAL GUIDANCE FROM GOLDEN EXAMPLES:",
                "",
                "These reference surveys demonstrate:",
                "- Appropriate question depth for the methodology",
                "- Proper text block structure (introText, textBlocks, closingText)",
                "- Follow-up question patterns after ratings",
                "- Professional question phrasing",
                "- Clean JSON structure",
                "",
                "**YOUR TASK**: Generate a survey that matches this quality and structure.",
                "",
                "**Look for these patterns in the references**:",
                "1. **Question Density**: How many questions for this methodology?",
                "2. **Rating Batteries**: How are sensory/attribute questions organized?",
                "3. **Follow-ups**: When do they ask 'why' or 'what' after ratings?",
                "4. **Text Blocks**: What intro/closing text do they include?",
                "5. **Section Distribution**: How are questions distributed across 7 sections?",
                "",
                "⚠️ **Match the depth within ±20%** - Don't under-generate questions",
                ""
            ])
            
            # Add similarity info if available
            if rag_context.similarity_scores:
                avg_similarity = sum(rag_context.similarity_scores) / len(rag_context.similarity_scores)
                golden_content.append(f"**Relevance Score**: {avg_similarity:.2f} (semantic match to your RFQ)")
                golden_content.append("")
            
            sections.append(PromptSection("golden_examples", golden_content, order=4.1))
        
        # 4.2 Golden Questions (specific examples)
        if golden_questions:
            question_content = [
                "# 4.2 EXPERT QUESTION EXAMPLES",
                "",
                "High-quality questions from verified surveys - use as templates:",
                ""
            ]
            
            # Show up to 8 questions
            for i, question in enumerate(golden_questions[:8], 1):
                question_text = question.get('question_text', '')
                question_type = question.get('question_type', 'unknown')
                quality_score = question.get('quality_score', 0.0)
                human_verified = question.get('human_verified', False)
                annotation_comment = question.get('annotation_comment', '')
                
                question_content.extend([
                    f"**Example {i}:** \"{question_text}\"",
                    f"**Type:** {question_type} | **Quality:** {quality_score:.2f}/1.0 | {'✅ Verified' if human_verified else '🤖 AI'}",
                ])
                
                if annotation_comment:
                    # Truncate long comments
                    max_length = 200
                    truncated = (annotation_comment[:max_length] + "...") if len(annotation_comment) > max_length else annotation_comment
                    question_content.extend([
                        f"**Expert Guidance:** {truncated}",
                        ""
                    ])
                else:
                    question_content.append("")
            
            sections.append(PromptSection("golden_questions", question_content, order=4.2))
        
        # 4.3 Few-Shot Examples for Question Types
        fewshot_content = [
            "# 4.3 FEW-SHOT EXAMPLES - Question Type Patterns",
            "",
            "## Example 1: Scale Question with Follow-up",
            "```json",
            "{",
            '  "id": "q_1",',
            '  "text": "How much did you like this vodka sample? (1=Dislike extremely, 11=Like extremely)",',
            '  "type": "scale",',
            '  "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],',
            '  "required": true',
            "},",
            "{",
            '  "id": "q_1_followup",',
            '  "text": "ASK IF CODED 7 TO 11 IN q_1: What did you like about this sample?",',
            '  "type": "open_ended",',
            '  "required": false',
            "}",
            "```",
            "",
            "## Example 2: Matrix Likert (Attribute Battery)",
            "```json",
            "{",
            '  "id": "q_attributes",',
            '  "text": "Please rate the following attributes of this sample:",',
            '  "type": "matrix_likert",',
            '  "rows": [',
            '    "Appearance - Clarity",',
            '    "Aroma - Intensity",',
            '    "Taste - Smoothness",',
            '    "Aftertaste - Length"',
            '  ],',
            '  "options": ["1", "2", "3", "4", "5"],',
            '  "scale_labels": {"1": "Very Poor", "5": "Excellent"},',
            '  "required": true',
            "}",
            "```",
            "",
            "## Example 3: Multiple Choice with 'Other' Follow-up",
            "```json",
            "{",
            '  "id": "q_brands",',
            '  "text": "Which vodka brands are you aware of?",',
            '  "type": "multiple_choice",',
            '  "options": ["Absolut", "Grey Goose", "Smirnoff", "Belvedere", "Other"],',
            '  "required": true',
            "},",
            "{",
            '  "id": "q_brands_other",',
            '  "text": "ASK IF CODED \'Other\' IN q_brands: Please specify which other brand",',
            '  "type": "open_ended",',
            '  "required": false',
            "}",
            "```",
            "",
            "## Example 4: NPS with Mandatory Follow-up",
            "```json",
            "{",
            '  "id": "q_nps",',
            '  "text": "How likely are you to recommend this product to a friend or colleague? (0=Not at all likely, 10=Extremely likely)",',
            '  "type": "scale",',
            '  "options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],',
            '  "required": true',
            "},",
            "{",
            '  "id": "q_nps_why",',
            '  "text": "Why did you give this score?",',
            '  "type": "open_ended",',
            '  "required": true',
            "}",
            "```",
            "",
            "**Key Patterns to Follow**:",
            "- Rating questions (scale): Use numeric string options",
            "- Follow-ups: Document condition in question text ('ASK IF...')",
            "- Matrix questions: Use rows + options, not nested structures",
            "- Clean options: No codes like '01 |', no [RANDOMIZE]",
            ""
        ]
        sections.append(PromptSection("fewshot_examples", fewshot_content, order=4.3))
        
        return PromptModule(
            name="MODULE 4: EXAMPLES - Reference Surveys and Patterns",
            order=4,
            sections=sections,
            required=True
        )


class OutputModule:
    """MODULE 5: Output - Format and Validation"""
    
    @staticmethod
    def build(json_examples_mode: str = 'consolidated') -> PromptModule:
        """Build output format and validation sections"""
        sections = []
        
        # 5.1 Output Structure & Schema
        structure_content = [
            "# 5.1 OUTPUT STRUCTURE",
            "",
            "## Required JSON Schema:",
            "```json",
            "{",
            '  "title": "Survey Title from RFQ",',
            '  "description": "Clear description of survey purpose",',
            '  "sections": [',
            "    {",
            '      "id": 1,',
            '      "title": "Sample Plan",',
            '      "description": "Sample quotas and screening",',
            '      "introText": {',
            '        "id": "intro_1",',
            '        "type": "study_intro",',
            '        "label": "Study_Intro",',
            '        "content": "Thank you for participating...",',
            '        "mandatory": true',
            "      },",
            '      "textBlocks": [...]  // Optional',
            '      "questions": [...]  // Array of question objects',
            "    },",
            "    // ... sections 2-6 with similar structure",
            "    {",
            '      "id": 7,',
            '      "title": "Programmer Instructions",',
            '      "description": "Technical routing and quotas",',
            '      "questions": [...]  // Programmer instruction questions (type: "instruction")',
            '      "closingText": {',
            '        "id": "closing_7",',
            '        "type": "survey_closing",',
            '        "label": "Survey_Closing",',
            '        "content": "Thank you for completing...",',
            '        "mandatory": true',
            "      }",
            "    }",
            "  ],",
            '  "metadata": {',
            '    "estimated_time": 20,',
            '    "methodology_tags": ["taste_test", "blind"],',
            '    "target_responses": 400,',
            '    "sections_count": 7',
            "  }",
            "}",
            "```",
            ""
        ]
        sections.append(PromptSection("output_structure", structure_content, order=5.1))
        
        # 5.2 Formatting Requirements
        format_content = [
            "# 5.2 FORMATTING REQUIREMENTS",
            "",
            "## JSON Format Rules:",
            "- MUST be valid JSON parseable by json.loads()",
            "- NO markdown formatting (no ```json tags)",
            "- NO explanations or text before/after JSON",
            "- Response must START with '{' and END with '}'",
            "- NO line breaks within string values",
            "- Proper escape sequences for quotes within strings",
            "",
            "## Clean Question Text:",
            "❌ BAD: 'Q1. How would you rate [PRODUCT NAME]? [SHOW SCALE] 01 | Very Poor'",
            "✅ GOOD: 'How would you rate this vodka?' (options: ['Very Poor', 'Poor', ...])",
            "",
            "❌ BAD: Options with codes: ['01 | Male', '02 | Female']",
            "✅ GOOD: Clean options: ['Male', 'Female']",
            "",
            "❌ BAD: Placeholders: '[BRAND NAME]', '[INSERT CONCEPT]'",
            "✅ GOOD: Actual names: 'Absolut Vodka', 'Product X'",
            "",
            "## Remove Programming Instructions:",
            "Remove from question text: [RANDOMIZE], [ANCHOR], [SHOW CONCEPT], [IF RESPONSE], [TERMINATE], QUOTAS:, CLASSIFY AS",
            "These belong in programmer instruction questions (Section 7) if needed, not in respondent-facing questions",
            ""
        ]
        sections.append(PromptSection("formatting_requirements", format_content, order=5.2))
        
        # 5.3 Pre-Submission Validation Checklist
        validation_content = [
            "# 5.3 PRE-SUBMISSION VALIDATION CHECKLIST",
            "",
            "Before returning your JSON, verify EVERY item below:",
            "",
            "## Structure Validation:",
            "- [ ] Exactly 7 sections (ids 1-7)",
            "- [ ] Each section has: id, title, description, questions array",
            "- [ ] Valid JSON format (no syntax errors)",
            "",
            "## Text Block Validation (CRITICAL):",
            "- [ ] Section 1: Has introText (Study_Intro)",
            "- [ ] Section 2: Has introText (Screener context)",
            "- [ ] Section 3: Has introText (Brand awareness context)",
            "- [ ] Section 4: Has introText (Concept/Product instructions)",
            "- [ ] Section 5: Has introText (Methodology instructions)",
            "- [ ] Section 6: Has introText (Demographics context)",
            "- [ ] Section 7: Has closingText (Survey_Closing)",
            "- [ ] All text blocks have: id, type, label, content, mandatory: true",
            "- [ ] Content is customized to RFQ (not generic templates)",
            "",
            "## Question Quality Validation:",
            "- [ ] Question count matches methodology depth (refer to golden examples ±20%)",
            "- [ ] For taste test: 25-50 rating questions per sample",
            "- [ ] For NPS: Score question + why follow-up",
            "- [ ] Rating questions have follow-ups where appropriate (10-15%)",
            "- [ ] Open-ended questions present (10-15% of total)",
            "- [ ] NO placeholder text ([BRAND], [PRODUCT], etc.)",
            "- [ ] NO programming codes in question text or options",
            "- [ ] Clean, respondent-facing language",
            "",
            "## Methodology Compliance:",
            "- [ ] Taste test: Rating batteries for each sensory attribute",
            "- [ ] NPS: 0-10 scale + mandatory follow-up",
            "- [ ] Van Westendorp: 4 price questions",
            "- [ ] Brand tracking: Awareness → Usage → Preference flow",
            "- [ ] Follow-up questions documented: 'ASK IF CODED...'",
            "",
            "## Format Validation:",
            "- [ ] Valid JSON (test with json.loads)",
            "- [ ] No markdown formatting",
            "- [ ] No text outside JSON",
            "- [ ] No line breaks in strings",
            "- [ ] Proper quote escaping",
            "",
            "═══════════════════════════════════════════════════════════════",
            "🚨 IF ANY ITEM FAILS: DO NOT SUBMIT - FIX THE ISSUE FIRST 🚨",
            "═══════════════════════════════════════════════════════════════",
            "",
            "## FINAL INSTRUCTION:",
            "Return ONLY the valid JSON survey object. No explanations, no markdown, no additional text.",
            "Start with '{' and end with '}'",
            ""
        ]
        sections.append(PromptSection("validation_checklist", validation_content, order=5.3))
        
        return PromptModule(
            name="MODULE 5: OUTPUT - Format and Validation",
            order=5,
            sections=sections,
            required=True
        )


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
                    f"- Required Questions: {method.get('required_questions', 'varies')}",
                    f"- Validation Rules: {'; '.join(method['validation_rules'])}",
                    ""
                ])
                
                # Add specific formatting note for MaxDiff
                if tag.lower() == 'maxdiff':
                    content.append("- CRITICAL: Use 'features' array (not 'options') with actual feature names")
                    content.append("- Generate ONE question per concept showing ALL features in a single table")
                    content.append("- Extract feature names from product/concept descriptions")
                    content.append("")

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

    def build_unmapped_context_section(self, unmapped_context: str) -> PromptSection:
        """Build unmapped context section for additional RFQ information"""
        if not unmapped_context or not unmapped_context.strip():
            return PromptSection("unmapped_context", [], order=4.5, required=False)
        
        content = [
            "## ADDITIONAL CONTEXT FROM RFQ:",
            "The following information was extracted from the RFQ but doesn't fit into structured fields:",
            "",
            unmapped_context.strip(),
            ""
        ]
        
        return PromptSection("unmapped_context", content, order=4.5)

    def build_golden_questions_section(
        self, 
        golden_questions: List[Dict[str, Any]], 
        feedback_digest: Optional[Dict[str, Any]] = None
    ) -> PromptSection:
        """Build simplified golden questions section focused on examples and expert guidance"""
        if not golden_questions and not feedback_digest:
            return PromptSection("golden_questions", [], order=4.2, required=False)
        
        content = [
            "## 📝 EXPERT QUESTION EXAMPLES:",
            "",
            "High-quality questions from verified surveys. Use these as templates.",
            ""
        ]
        
        # Display up to 8 questions (increased from 5 since we removed label filtering)
        for i, question in enumerate(golden_questions[:8], 1):
            question_text = question.get('question_text', '')
            question_type = question.get('question_type', 'unknown')
            quality_score = question.get('quality_score', 0.0)
            human_verified = question.get('human_verified', False)
            annotation_comment = question.get('annotation_comment', '')
            
            content.extend([
                f"**Example {i}:** \"{question_text}\"",
                f"**Type:** {question_type} | **Quality:** {quality_score:.2f}/1.0 | {'✅ Human Verified' if human_verified else '🤖 AI Generated'}",
            ])
            
            if annotation_comment:
                # Truncate long comments to prevent prompt bloat (keep key guidance)
                max_comment_length = 200  # Keep reasonable detail without bloat
                truncated_comment = (
                    annotation_comment[:max_comment_length] + "..."
                    if len(annotation_comment) > max_comment_length
                    else annotation_comment
                )
                content.extend([
                    f"**Expert Guidance:** {truncated_comment}",
                    ""
                ])
            else:
                content.append("")
        
        # Add feedback digest if available
        if feedback_digest and feedback_digest.get('feedback_digest'):
            content.extend([
                "",
                "---",
                "",
                feedback_digest['feedback_digest'],
                ""
            ])
        
        content.extend([
            "**USAGE INSTRUCTIONS:**",
            "- Use these as templates, adapting the wording to match your specific RFQ context",
            "- Pay special attention to expert guidance comments for best practices",
            "- Review the feedback digest above for common patterns, recommendations, and issues to avoid",
            "- Refer to the QNR Taxonomy Reference for complete list of required question types",
            ""
        ])
        
        return PromptSection("golden_questions", content, order=4.2)

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
    def get_json_requirements_section(json_examples_mode: str = 'consolidated') -> PromptSection:
        """Get the consolidated JSON formatting requirements
        
        Args:
            json_examples_mode: 'rag_reference' (OFF - use RAG) or 'consolidated' (ON - use consolidated example)
        """
        content = [
            "## CRITICAL REQUIREMENT - SECTIONS FORMAT:",
            "🚨 MANDATORY: Generate survey using SECTIONS format with exactly 7 sections",
            "🚨 MANDATORY: Return ONLY valid JSON - NO markdown, explanations, or additional text",
            "🚨 MANDATORY: Start response with { and end with } - this is the ONLY format accepted",
            "🚨 MANDATORY: Include ALL required text blocks (introText, textBlocks, closingText) as specified in text requirements",
            "",
            "## SECTION ORGANIZATION:",
            "1. **Sample Plan** (id: 1): Participant qualification criteria, recruitment requirements, and quotas",
            "2. **Screener** (id: 2): Initial qualification questions and basic demographics",
            "3. **Brand/Product Awareness & Usage** (id: 3): Brand recall, awareness funnel, and usage patterns",
            "4. **Concept Exposure** (id: 4): Product/concept introduction and reaction assessment",
            "5. **Methodology** (id: 5): Research-specific questions (Conjoint, Pricing, Feature Importance)",
            "6. **Additional Questions** (id: 6): Supplementary research questions and follow-ups",
            "7. **Programmer Instructions** (id: 7): Technical implementation notes and data specifications",
            "   - CRITICAL: Generate programmer instruction questions (type: 'instruction') based on RFQ requirements",
            "   - Include routing logic, quota checks, termination rules, skip logic, SEC calculations, and validation rules",
            "   - Extract ANY routing, quota, termination, or logic requirements mentioned in the RFQ",
            "   - Use golden examples as templates to see what programmer instructions look like",
            "   - Examples: 'IF ELIGIBLE RESPONDENT THEN CONTINUE, ELSE THANK AND TERMINATE'",
            "   - Examples: 'SEC CALCULATION GRID: HOUSEHOLD INCOME (R5) x SCORE FOR HOUSEHOLD PROPERTIES (R7)'",
            "   - Examples: 'IF CODED SEC B & C, CHECK QUOTA. IF CODED A, D, E TERMINATE'",
            "   - Examples: 'BEVERAGE TERMINATION RULES: Awareness must include VODKA (14)'",
            "   - Examples: 'PRESENCE OF SMELL SKIPS: If 'No, this vodka is odorless' in neat aroma, SKIP to mixed visual'",
            "",
            "**Note**: Refer to the QNR Taxonomy Reference for required question types per section.",
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
            "✅ **yes_no**: For simple yes/no confirmation questions",
            "   - Format: Question text asking for confirmation or binary choice",
            "   - Examples: 'Please confirm you are 18 years or older.', 'Have you purchased this product in the past 3 months?', 'Do you agree to participate?',",
            "   - Structure: Single question with two radio button options: Yes and No",
            "   - Required: 'options' array must be exactly ['Yes', 'No']",
            "   - CRITICAL: Question text must be a complete, readable sentence - do NOT use internal labels as text",
            "",
            "📊 **matrix_likert**: For rating multiple attributes on a scale",
            "   - Format: Question text ending with '?', ':', or '.' followed by comma-separated attributes",
            "   - Examples: 'How important are the following when choosing a product? Comfort, Price, Quality, Brand reputation.'",
            "   - Examples: 'Rate the following features: Comfort, Price, Quality, Brand reputation.'",
            "   - Examples: 'Please evaluate these aspects. Comfort, Price, Quality, Brand reputation.'",
            "   - Structure: Attributes become table rows, options become columns with radio buttons",
            "   - Required: 'options' array with scale labels (e.g., ['Not important', 'Somewhat important', 'Very important'])",
            "   - CRITICAL: DO NOT put scale labels (like '1 = Dislike Extremely') in the question text - put them in 'options' array",
            "   - CRITICAL: DO include comma-separated attributes in question text after '?', ':', or '.'",
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
            "💰 **numeric_open**: For open-ended numeric input (any numeric value)",
            "   - Format: Question text asking for a specific numeric value",
            "   - Examples: 'How many times per week do you exercise?' or 'At what price would you consider this too expensive?'",
            "   - Van Westendorp Example: 'At what price per bottle would you consider this product too cheap that you would question its quality? Please enter amount in your local currency.'",
            "   - Structure: Single numeric input field",
            "   - Required: No 'options' array needed - input type is context-dependent",
            "   - Context: Can represent any numeric value (age, price, quantity, rating, etc.)",
            "   - CRITICAL: Question text must be a complete, descriptive question - do NOT use generic placeholders like 'Currency Question' or 'Please enter the amount:'",
            "",
            "🎯 **maxdiff**: text='Select MOST/LEAST important features', type='maxdiff', features=['Feature1','Feature2',...] (NOT options)",
            "   Extract actual names from concept, NO placeholders | ONE question with ALL features | NO [SHOW CONCEPT] instructions",
            "",
        ]

        # Add JSON structure section based on mode
        if json_examples_mode == 'rag_reference':
            # Mode: RAG Reference (OFF) - Explicit guidance to use RAG context
            content.extend([
                "## REQUIRED JSON STRUCTURE:",
                "",
                "📚 **REFERENCE GOLDEN EXAMPLES FROM RAG CONTEXT**:",
                "",
                "When JSON schema example is not provided, refer to the 'CONTEXTUAL KNOWLEDGE' section above.",
                "The golden examples retrieved via RAG contain complete JSON structures that you can use as templates.",
                "",
                "**Look for these structure elements in the contextual knowledge section:**",
                "",
                "- **introText structure**: {id, type, label, content, mandatory}",
                "  Example: Study introductions, concept introductions",
                "",
                "- **textBlocks array**: [{id, type, label, content, mandatory}]",
                "  Example: Product usage instructions, mid-section content",
                "",
                "- **closingText structure**: {id, type, label, content, mandatory}",
                "  Example: Survey closing messages",
                "",
                "- **Question objects**: {id, text, type, options, required, methodology, order}",
                "  Note: Question types match the guidelines above (yes_no, matrix_likert, constant_sum, etc.)",
                "",
                "- **Section structure**: {id, title, description, introText, textBlocks, questions, closingText}",
                "  All 7 sections follow this pattern",
                "",
                "- **Metadata structure**: {estimated_time, methodology_tags, target_responses, sections_count}",
                "",
                "**Instructions:**",
                "1. Use similar surveys from RAG context as templates for JSON structure",
                "2. Follow the format rules and question type guidelines above",
                "3. Match the structure patterns you see in the contextual knowledge examples",
                "4. Ensure all required fields are present (id, type, label for text blocks; id, text, type for questions)",
                ""
            ])
        else:
            # Mode: Consolidated Examples (ON) - Unified example covering all question types
            content.extend([
                "## REQUIRED JSON STRUCTURE:"
            ])
            
            # Add the JSON schema example (consolidated version - more efficient than current)
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
                                "text": "Please confirm you are 18 years or older.",
                                "type": "yes_no",
                                "options": ["Yes", "No"],
                                "required": True,
                                "methodology": "screening",
                                "order": 1
                            },
                            {
                                "id": "q2",
                                "text": "Which city do you currently live in?",
                                "type": "multiple_choice",
                                "options": ["Option 1", "Option 2"],
                                "required": True,
                                "methodology": "screening",
                                "order": 2
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
                                "text": "Which of the following brands do you regularly purchase?",
                                "type": "multiple_select",
                                "options": ["Brand A", "Brand B", "Brand C", "None of these"],
                                "required": True,
                                "methodology": "brand_usage",
                                "order": 3
                            },
                            {
                                "id": "q4",
                                "text": "Please allocate 100 points across the following factors: Taste, Price, Brand reputation, Packaging.",
                                "type": "constant_sum",
                                "required": True,
                                "methodology": "feature_importance",
                                "order": 4
                            },
                            {
                                "id": "q5",
                                "text": "Please rate the sensory attributes of this sample. Appearance, Aroma, Taste, Mouthfeel, Finish.",
                                "type": "matrix_likert",
                                "options": ["Very poor", "Poor", "Fair", "Good", "Very good"],
                                "required": True,
                                "methodology": "sensory_evaluation",
                                "order": 5
                            },
                            {
                                "id": "q6",
                                "text": "Highlight the MOST IMPORTANT and the LEAST IMPORTANT features in the Product_A description.",
                                "type": "maxdiff",
                                "features": ["AI Personal Coaching", "Custom Workout Plans", "Nutrition Tracking", "Social Community", "Live Classes", "Progress Analytics"],
                                "required": True,
                                "methodology": "maxdiff",
                                "order": 6
                            },
                            {
                                "id": "q7",
                                "text": "How much would you pay for each? Product A, Product B, Product C.",
                                "type": "numeric_grid",
                                "options": ["$0-10", "$10-20", "$20-30", "$30+"],
                                "required": True,
                                "methodology": "willingness_to_pay",
                                "order": 7
                            },
                            {
                                "id": "q8",
                                "text": "How many times per week do you purchase this product?",
                                "type": "numeric_open",
                                "required": True,
                                "methodology": "purchase_frequency",
                                "order": 8
                            },
                            {
                                "id": "q9",
                                "text": "At what price per bottle would you consider this product too cheap that you would question its quality? Please enter amount in your local currency.",
                                "type": "numeric_open",
                                "required": True,
                                "methodology": "VW_pricing",
                                "order": 9
                            },
                            {
                                "id": "q10",
                                "text": "At what price per bottle would you consider this product getting expensive, but still worth considering? Please enter amount in your local currency.",
                                "type": "numeric_open",
                                "required": True,
                                "methodology": "VW_pricing",
                                "order": 10
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
                        "questions": [
                            {
                                "id": "prog_1",
                                "type": "instruction",
                                "text": "IF ELIGIBLE RESPONDENT THEN CONTINUE, ELSE THANK AND TERMINATE. TO BE FOLLOWED ONLY IF THE CRITERIA IS RELAXED FOR RECRUITMENT.",
                                "mandatory": False
                            },
                            {
                                "id": "prog_2",
                                "type": "instruction",
                                "text": "SEC CALCULATION GRID: HOUSEHOLD INCOME (R5) x SCORE FOR HOUSEHOLD PROPERTIES (R7) -> SEC A/B/C/D/E. IF CODED SEC B & C, CHECK QUOTA. IF CODED A, D, E TERMINATE.",
                                "mandatory": False
                            }
                        ],
                        "closingText": {
                            "id": "closing_7",
                            "type": "survey_closing",
                            "label": "Survey_Closing",
                            "content": "Thank you for completing this survey! Your responses are valuable and will help us better understand market preferences. If you have any questions about this research, please contact us at research@company.com. You may now close this window.",
                            "mandatory": True
                        }
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
                "## CLEAN OUTPUT EXAMPLES:",
                "",
                "❌ BAD Gabor-Granger (messy):",
                "   'CQ01b. On a scale of 1 to 5: where 1 is \"Definitely will not purchase\"...",
                "   [SHOW HYPERLINK] [RANDOMIZE] Product_B at $249 | $299 | $349'",
                "   options: ['1 = Definitely will not purchase', '2 = Probably will not purchase', ...]",
                "",
                "✅ GOOD Gabor-Granger (clean):",
                "   text: 'How likely would you be to purchase Product_B?'",
                "   type: 'gabor_granger'",
                "   options: ['$249', '$299', '$349', '$399']",
                "   scale_labels: {'1': 'Definitely will not purchase', '5': 'Definitely will purchase'}",
                "",
                "🚨 REMOVE from ALL questions: [SHOW HYPERLINK], [RANDOMIZE], [IF RESPONSE], [CAPTURE], [TERMINATE], QUOTAS:, CLASSIFY AS",
                "",
                "🚨 CRITICAL: Response must be valid JSON parseable by json.loads()",
                "",
                "## FINAL INSTRUCTION - JSON OUTPUT ONLY:",
                "🚨 YOU MUST RETURN **ONLY** VALID JSON - NO PROSE, NO EXPLANATIONS, NO TEXT OUTSIDE JSON",
                "🚨 Your response must START with '{' and END with '}'",
                "🚨 Do NOT include markdown formatting, descriptions, or any text before/after the JSON",
                "🚨 The response will be parsed with json.loads() - it must be valid JSON",
                "",
                "Generate the survey JSON now:"
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

    def get_pillar_rules_context(self, detail_level: str = 'digest') -> str:
        """Get formatted pillar rules context
        
        Args:
            detail_level: 'full' (all rules with details), 'digest' (core rules only), 'none' (no rules)
        """
        if detail_level == 'none' or not self.pillar_rules:
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

            if detail_level == 'digest':
                # Digest mode: Only core rules, no implementation notes
                core_rules = [r for r in rules if r.get('rule_type') == 'generation' and r.get('priority') == 'core']
                if not core_rules:
                    continue
                
                context_parts.append(f"\n## {pillar_display} ({weight:.0%} Weight)")
                context_parts.append("Follow these core quality standards:")
                
                for rule in core_rules:
                    guideline = rule.get('generation_guideline', rule.get('description', ''))
                    context_parts.append(f"- 🔴 {guideline}")
            else:
                # Full mode: All rules with priority indicators and implementation notes
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
        """
        Build the complete survey generation prompt using the new 5-module architecture:
        1. Role Module - Who you are and what to accomplish
        2. Inputs Module - RFQ, context, and background
        3. Instruction Module - How to generate (mandatory requirements)
        4. Example Module - Golden examples and patterns
        5. Output Module - Format and validation requirements
        """

        # Extract RFQ details
        rfq_details = context.get("rfq_details", {})
        if "text" not in rfq_details:
            rfq_details["text"] = rfq_text
            context["rfq_details"] = rfq_details

        # Get methodology tags
        if not methodology_tags:
            methodology_tags = []
            if rfq_details.get("methodology_tags"):
                methodology_tags.extend(rfq_details["methodology_tags"])

        # Get pillar rules context for evaluation framework
        generation_config = context.get("generation_config", {})
        pillar_rules_detail = generation_config.get("pillar_rules_detail", "digest")
        pillar_context = self.get_pillar_rules_context(detail_level=pillar_rules_detail)

        # Get golden questions if available
        golden_questions = context.get("golden_questions", [])
        golden_examples = context.get("golden_examples", [])

        # Build all 5 modules
        logger.info("🏗️ [PromptBuilder] Building modular prompt...")
        
        # MODULE 1: Role and Objective
        role_module = RoleModule.build(context)
        
        # MODULE 2: Inputs - Background and Context
        inputs_module = InputsModule.build(context, rfq_text)
        
        # MODULE 3: Instructions - How to Generate (MOST CRITICAL)
        instruction_module = InstructionModule.build(context, methodology_tags, pillar_context)
        
        # MODULE 4: Examples - Reference Surveys and Patterns
        example_module = ExampleModule.build(golden_examples, rag_context, golden_questions)
        
        # MODULE 5: Output - Format and Validation
        output_module = OutputModule.build(json_examples_mode='consolidated')

        # Assemble modules in order
        modules = [
            role_module,
            inputs_module,
            instruction_module,
            example_module,
            output_module
        ]

        # Format each module and combine
        prompt_parts = []
        for module in sorted(modules, key=lambda m: m.order):
            if module.sections:
                module_output = module.format_output()
                if module_output.strip():
                    prompt_parts.append(module_output)

        final_prompt = "\n".join(prompt_parts).strip()

        logger.info(f"✅ [PromptBuilder] Generated modular prompt: {len(final_prompt)} chars")
        logger.info(f"📊 [PromptBuilder] Modules: Role, Inputs, Instructions, Examples, Output")

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

            # Create the prompt section - Hybrid approach: Brief checklist + golden reference
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
                "📚 **REFERENCE GOLDEN EXAMPLES FROM RAG CONTEXT FOR TEXT BLOCK STRUCTURE:**",
                "The golden examples retrieved via RAG contain complete text block structures you can use as templates.",
                "Look for these structure patterns in the 'CONTEXTUAL KNOWLEDGE' section:",
                "",
                "- **introText structure**: {id, type, label, content, mandatory} - Example: Study_Intro in Section 1",
                "- **textBlocks array**: [{id, type, label, content, mandatory}] - Example: Product_Usage in Section 3",
                "- **closingText structure**: {id, type, label, content, mandatory} - Example: Survey_Closing in Section 7",
                "",
                "**QNR SECTION TEXT PLACEMENT MAPPING:**",
                "- **Sample Plan (Section 1)**: Study_Intro in introText, Confidentiality_Agreement in textBlocks (if needed)",
                "- **Brand/Product Awareness (Section 3)**: Product_Usage in textBlocks (if applicable)",
                "- **Concept Exposure (Section 4)**: Concept_Intro in introText (if applicable)",
                "- **Methodology (Section 5)**: Methodology-specific instructions in textBlocks (if needed)",
                "- **Programmer Instructions (Section 7)**: Programmer instruction questions (type: 'instruction') in questions array (based on RFQ requirements), Survey_Closing in closingText (MANDATORY)",
                "",
                "🚨 **CRITICAL: Programmer Instructions Content**",
                "Section 7 (Programmer Instructions) should include BOTH:",
                "1. **Programmer instruction questions** (type: 'instruction') - Generate these based on RFQ requirements:",
                "   - Routing logic requirements (IF/THEN/ELSE conditions)",
                "   - Quota checks and controls",
                "   - Termination rules and eligibility criteria",
                "   - Skip logic requirements",
                "   - SEC calculations and classifications",
                "   - Validation rules and data specifications",
                "   - Any technical implementation notes mentioned in the RFQ",
                "2. **Survey_Closing text block** (in closingText field) - MANDATORY",
                "",
                "Look for patterns in the RFQ like:",
                "- 'Terminate if...', 'Skip to...', 'IF...THEN...ELSE...'",
                "- 'Quota', 'Sample size', 'Target responses'",
                "- 'SEC', 'Socio-economic classification', 'Demographics classification'",
                "- 'Validation', 'Data quality', 'Checks'",
                "- 'Routing', 'Logic', 'Conditions'",
                "",
                "🚨 **MANDATORY VALIDATION CHECKLIST - VERIFY ALL BEFORE SUBMITTING:**",
                "- [ ] Study_Intro text block included in Section 1 (Sample Plan)",
                "- [ ] Product_Usage text block included in Section 3 (Brand/Product Awareness) if applicable",
                "- [ ] Concept_Intro text block included in Section 4 (Concept Exposure) if applicable",
                "- [ ] **Programmer instruction questions generated in Section 7 (Programmer Instructions) based on RFQ routing/quota/termination requirements**",
                "- [ ] **Survey_Closing text block included in Section 7 (Programmer Instructions) - THIS IS MANDATORY**",
                "- [ ] All text blocks have correct 'label' field matching requirements",
                "- [ ] All text blocks have 'mandatory': true",
                "- [ ] All text blocks have proper 'type' field",
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

    def _build_qnr_taxonomy_section(self, context: Dict[str, Any]) -> Optional[PromptSection]:
        """Build comprehensive QNR taxonomy reference for LLM to use in survey generation"""
        try:
            if not self.db_session:
                logger.info("No database session available for QNR taxonomy section")
                return None
            
            from src.services.qnr_label_service import QNRLabelService
            qnr_service = QNRLabelService(self.db_session)
            
            # Get all labels (no filtering - let LLM decide)
            all_labels = qnr_service.get_all_labels_for_prompt()
            
            if not all_labels:
                logger.warning("No QNR labels found in database")
                return None
            
            # Group labels by section
            labels_by_section = {}
            for label in all_labels:
                section_id = label.get('section_id')
                if section_id not in labels_by_section:
                    labels_by_section[section_id] = []
                labels_by_section[section_id].append(label)
            
            content = [
                "## 📚 QNR TAXONOMY REFERENCE (Standard Question Types)",
                "",
                "This taxonomy provides a comprehensive list of standard question types used in market research surveys.",
                "Review the RFQ's industry and methodology to determine which question types are relevant.",
                "",
                "**Instructions for LLM:**",
                "1. Scan this taxonomy to understand available question types",
                "2. Select question types that match the RFQ's industry, methodology, and research goals",
                "3. Skip question types that don't apply (e.g., medical questions for food surveys, taste test for healthcare)",
                "4. Use golden examples as templates where available",
                "5. Generate additional relevant questions beyond this taxonomy if needed for comprehensive coverage",
                ""
            ]
            
            # Section name mapping
            section_names = {
                1: "Sample Plan",
                2: "Screener",
                3: "Brand/Product Awareness & Usage",
                4: "Concept Exposure",
                5: "Methodology",
                6: "Additional Questions",
                7: "Programmer Instructions"
            }
            
            # Build section-by-section taxonomy
            for section_id in sorted(labels_by_section.keys()):
                section_name = section_names.get(section_id, f"Section {section_id}")
                section_labels = labels_by_section[section_id]
                
                content.extend([
                    f"### SECTION {section_id}: {section_name}",
                    ""
                ])
                
                # Separate mandatory and optional
                mandatory_labels = [l for l in section_labels if l.get('mandatory')]
                optional_labels = [l for l in section_labels if not l.get('mandatory')]
                
                if mandatory_labels:
                    content.append("**Mandatory Question Types:**")
                    for label in mandatory_labels:
                        name = label['name']
                        desc = label.get('description', '')[:100]  # Truncate for prompt size
                        
                        # Add context hints
                        hints = []
                        applicable_labels = label.get('applicable_labels', [])
                        if applicable_labels:
                            # Extract relevant hints
                            if any(al.lower() in ['healthcare', 'medtech', 'consumer health'] for al in applicable_labels):
                                hints.append('healthcare')
                            if any(al.lower() in ['food_beverage', 'taste test'] for al in applicable_labels):
                                hints.append('food/beverage')
                            if 'Van Westendorp' in applicable_labels:
                                hints.append('pricing')
                            if 'Gabor Granger' in applicable_labels:
                                hints.append('pricing')
                            if 'Conjoint' in applicable_labels:
                                hints.append('conjoint')
                        
                        hint_str = f" [{', '.join(hints)}]" if hints else ""
                        content.append(f"  • **{name}**: {desc}{hint_str}")
                    content.append("")
                
                if optional_labels and len(optional_labels) <= 10:  # Only show if manageable
                    content.append("**Optional Question Types:**")
                    for label in optional_labels[:10]:  # Limit to avoid bloat
                        name = label['name']
                        desc = label.get('description', '')[:80]
                        
                        # Add context hints (same as mandatory labels)
                        hints = []
                        applicable_labels = label.get('applicable_labels', [])
                        if applicable_labels:
                            if any(al.lower() in ['healthcare', 'medtech', 'consumer health'] for al in applicable_labels):
                                hints.append('healthcare')
                            if any(al.lower() in ['food_beverage', 'taste test'] for al in applicable_labels):
                                hints.append('food/beverage')
                            if 'Van Westendorp' in applicable_labels:
                                hints.append('pricing')
                            if 'Gabor Granger' in applicable_labels:
                                hints.append('pricing')
                            if 'Conjoint' in applicable_labels:
                                hints.append('conjoint')
                        
                        hint_str = f" [{', '.join(hints)}]" if hints else ""
                        content.append(f"  • {name}: {desc}{hint_str}")
                    content.append("")
            
            content.extend([
                "---",
                "**Remember:** This is a reference guide. Select question types based on semantic relevance to the RFQ.",
                "Don't force-fit question types that don't make sense for the specific research context.",
                ""
            ])
            
            return PromptSection(
                title="QNR Taxonomy Reference",
                content=content,
                order=4.3,  # After text requirements, before survey structure
                required=False  # Non-blocking
            )
        
        except Exception as e:
            logger.warning(f"⚠️ [PromptBuilder] Failed to build QNR taxonomy section: {str(e)}")
            return None

    def _build_methodology_context_section(
        self, 
        context: Dict[str, Any],
        methodology_tags: Optional[List[str]] = None
    ) -> Optional[PromptSection]:
        """Provide semantic hints connecting RFQ methodologies to taxonomy labels"""
        logger.info(f"🔍 [PromptBuilder] Building methodology context section. Methodology tags: {methodology_tags}")
        if not methodology_tags:
            logger.info("⚠️ [PromptBuilder] No methodology tags provided, skipping methodology context section")
            return None
        
        # Keyword-based semantic mapping (no complex normalization needed)
        methodology_hints = {
            'taste': ['Blind_Taste_Test', 'Concept_visual_impression', 'Concept_taste_impression', 
                      'Concept_Aroma_*', 'Concept_quality_impression', 'Survey_Invite'],
            'sensory': ['Blind_Taste_Test', 'Concept_Aroma_*', 'Concept_taste_*'],
            'blind': ['Blind_Taste_Test'],
            'van_westendorp': ['VW_pricing', 'VW_Likelihood'],
            'pricing': ['VW_pricing', 'VW_Likelihood', 'GG_Likelihood'],
            'gabor': ['GG_Likelihood'],
            'conjoint': ['Concept_choice'],
            'maxdiff': ['Concept_Feature_Highlight']
        }
        
        # Find matching hints
        relevant_labels = set()
        for method in methodology_tags:
            method_lower = method.lower().replace('_', ' ')
            for keyword, labels in methodology_hints.items():
                if keyword in method_lower:
                    relevant_labels.update(labels)
        
        if not relevant_labels:
            logger.info("⚠️ [PromptBuilder] No relevant labels found for methodology tags")
            return None
        
        logger.info(f"✅ [PromptBuilder] Found {len(relevant_labels)} relevant labels for methodology tags")
        
        content = [
            "## METHODOLOGY GUIDANCE",
            "",
            f"Your RFQ includes: {', '.join(methodology_tags)}",
            "",
            "Consider using these relevant taxonomy labels:",
            ""
        ]
        
        for label in sorted(relevant_labels):
            content.append(f"  - {label}")
        
        content.extend([
            "",
            "These labels match your methodology semantically. Use them where appropriate.",
            ""
        ])
        
        logger.info(f"✅ [PromptBuilder] Created methodology context section with {len(content)} lines")
        return PromptSection(
            title="Methodology Context",
            content=content,
            order=4.35,
            required=False
        )

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
            
            # Add actionable comments from high-quality annotations
            if guidelines.get("actionable_comments"):
                content.extend([
                    "## 📝 EXPERT ANNOTATION GUIDANCE:",
                    "",
                    "From high-quality annotated questions, apply these specific principles:",
                    ""
                ])
                
                for comment_data in guidelines["actionable_comments"][:5]:  # Top 5 actionable comments
                    verified_badge = "✓ Human Verified" if comment_data.get("human_verified") else ""
                    score_badge = f"(Score: {comment_data.get('quality_score', 0):.1f}/5)"
                    content.extend([
                        f"- \"{comment_data['comment']}\" {verified_badge} {score_badge}",
                        ""
                    ])
            
            content.extend([
                "## 🎯 IMPLEMENTATION GUIDELINES:",
                "",
                "1. **Follow High-Quality Patterns**: Use the examples above as templates for similar questions",
                "2. **Apply Expert Guidance**: Incorporate the specific principles from annotated questions",
                "3. **Avoid Problematic Patterns**: Steer clear of the patterns that consistently score low",
                "4. **Address Common Issues**: Be mindful of the issues experts frequently flag",
                "5. **Quality Over Speed**: Take time to craft clear, unbiased questions",
                "6. **Test for Clarity**: Ensure questions are easy to understand and answer",
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