"""
Enhanced RFQ Converter - Python backend implementation
Converts Enhanced RFQ structured data into enriched text for LLM processing
Maintains the open-closed principle by converting rich data to text without requiring workflow changes.
"""

from typing import Dict, Any, List

# QNR labeling requirements for methodologies (aligned with 7-section structure)
METHODOLOGY_TEXT_REQUIREMENTS = {
    "concept_test": ["Study_Intro", "Concept_Intro"],
    "product_test": ["Study_Intro", "Product_Usage"],
    "ad_test": ["Study_Intro", "Concept_Intro"],
    "package_test": ["Study_Intro", "Product_Usage"],
    "brand_tracker": ["Study_Intro", "Product_Usage"],
    "u_and_a": ["Study_Intro", "Product_Usage"],
    "segmentation": ["Study_Intro", "Confidentiality_Agreement"],
    "pricing": ["Study_Intro", "Product_Usage"],
    "van_westendorp": ["Study_Intro", "Product_Usage"],
    "gabor_granger": ["Study_Intro", "Product_Usage"],
    "conjoint": ["Study_Intro", "Confidentiality_Agreement"],
    "max_diff": ["Study_Intro"],
    "monadic": ["Study_Intro", "Concept_Intro"],
    "sequential": ["Study_Intro", "Concept_Intro"],
    "competitive": ["Study_Intro", "Product_Usage"],
    "basic_survey": ["Study_Intro"],
}


def build_enhanced_rfq_text(rfq: Dict[str, Any]) -> str:
    """
    Convert Enhanced RFQ structured data into enriched text for LLM processing
    """
    sections: List[str] = []

    # Research Objectives Section
    research_objectives = rfq.get('research_objectives')
    if research_objectives and research_objectives.get('key_research_questions'):
        sections.append("## Research Objectives:")
        for i, objective in enumerate(research_objectives['key_research_questions'], 1):
            sections.append(f"{i}. {objective}")

        # Enhanced research objective fields
        if research_objectives.get('success_metrics'):
            sections.append(f"\n**Success Metrics**: {research_objectives['success_metrics']}")

        if research_objectives.get('validation_requirements'):
            sections.append(f"**Validation Requirements**: {research_objectives['validation_requirements']}")

        if research_objectives.get('measurement_approach'):
            approach_label = research_objectives['measurement_approach'].replace('_', ' ').title()
            sections.append(f"**Measurement Approach**: {approach_label}")

        sections.append('')

    # Target Audience Details
    if research_objectives and research_objectives.get('research_audience'):
        sections.append("## Target Audience:")
        sections.append(f"- **Research Audience**: {research_objectives['research_audience']}")
        sections.append('')

    # Methodology Preferences
    methodology = rfq.get('methodology')
    if methodology:
        selected_methodologies = methodology.get('selected_methodologies', [])
        primary_method = methodology.get('primary_method')  # Legacy support
        
        # Use selected_methodologies if available, otherwise fallback to primary_method
        has_methodologies = (selected_methodologies and len(selected_methodologies) > 0) or primary_method
        
        if has_methodologies:
            sections.append("## Methodology Preferences:")
            
            if selected_methodologies and len(selected_methodologies) > 0:
                methods_list = ', '.join([m.replace('_', ' ').title() for m in selected_methodologies])
                sections.append(f"- **Selected Methodologies**: {methods_list}")
            elif primary_method:
                # Legacy: use primary_method if selected_methodologies not available
                sections.append(f"- **Primary Method**: {primary_method}")

            if methodology.get('stimuli_details'):
                sections.append(f"- **Stimuli Details**: {methodology['stimuli_details']}")

            if methodology.get('methodology_requirements'):
                sections.append(f"- **Requirements**: {methodology['methodology_requirements']}")

            # Enhanced methodology fields
            if methodology.get('complexity_level'):
                complexity_label = methodology['complexity_level'].replace('_', ' ').title()
                sections.append(f"- **Complexity Level**: {complexity_label}")

            if methodology.get('required_methodologies'):
                methodologies = [m.replace('_', ' ').title() for m in methodology['required_methodologies']]
                sections.append(f"- **Required Methodologies**: {', '.join(methodologies)}")

            if methodology.get('sample_size_target'):
                sections.append(f"- **Sample Size Target**: {methodology['sample_size_target']}")

            sections.append('')

    # Business Context Section
    business_context = rfq.get('business_context')
    if business_context:
        sections.append("## Business Context:")

        if business_context.get('company_product_background'):
            sections.append(f"- **Background**: {business_context['company_product_background']}")

        if business_context.get('business_problem'):
            sections.append(f"- **Business Problem**: {business_context['business_problem']}")

        if business_context.get('business_objective'):
            sections.append(f"- **Business Objective**: {business_context['business_objective']}")

        # Enhanced business context fields
        if business_context.get('stakeholder_requirements'):
            sections.append(f"- **Stakeholder Requirements**: {business_context['stakeholder_requirements']}")

        if business_context.get('decision_criteria'):
            sections.append(f"- **Decision Criteria**: {business_context['decision_criteria']}")

        if business_context.get('budget_range'):
            budget_label = business_context['budget_range'].replace('_', ' ').title()
            sections.append(f"- **Budget Range**: {budget_label}")

        if business_context.get('timeline_constraints'):
            timeline_label = business_context['timeline_constraints'].replace('_', ' ').title()
            sections.append(f"- **Timeline Constraints**: {timeline_label}")

        sections.append('')

    # Survey Requirements Section
    survey_requirements = rfq.get('survey_requirements')
    if survey_requirements:
        sections.append("## Survey Requirements:")

        if survey_requirements.get('sample_plan'):
            sections.append(f"- **Sample Plan**: {survey_requirements['sample_plan']}")

        if survey_requirements.get('required_sections'):
            sections.append(f"- **Required Sections**: {', '.join(survey_requirements['required_sections'])}")

        if survey_requirements.get('must_have_questions'):
            sections.append(f"- **Must-Have Questions**: {'; '.join(survey_requirements['must_have_questions'])}")

        if survey_requirements.get('screener_requirements'):
            sections.append(f"- **Screener Requirements**: {survey_requirements['screener_requirements']}")

        # Enhanced survey requirements
        if survey_requirements.get('completion_time_target'):
            time_label = survey_requirements['completion_time_target'].replace('_', '-').replace('min', ' minutes')
            sections.append(f"- **Target Completion Time**: {time_label}")

        if survey_requirements.get('device_compatibility'):
            device_label = survey_requirements['device_compatibility'].replace('_', ' ').title()
            sections.append(f"- **Device Compatibility**: {device_label}")

        if survey_requirements.get('accessibility_requirements'):
            accessibility_label = survey_requirements['accessibility_requirements'].replace('_', ' ').title()
            sections.append(f"- **Accessibility Requirements**: {accessibility_label}")

        if survey_requirements.get('data_quality_requirements'):
            quality_label = survey_requirements['data_quality_requirements'].replace('_', ' ').title()
            sections.append(f"- **Data Quality Requirements**: {quality_label}")

        sections.append('')

    # Advanced Classification Section
    advanced_classification = rfq.get('advanced_classification')
    if advanced_classification:
        sections.append("## Classification & Compliance:")

        if advanced_classification.get('industry_classification'):
            industry_label = advanced_classification['industry_classification'].replace('_', ' ').title()
            sections.append(f"- **Industry**: {industry_label}")

        if advanced_classification.get('respondent_classification'):
            sections.append(f"- **Respondent Type**: {advanced_classification['respondent_classification']}")

        if advanced_classification.get('methodology_tags'):
            tags = [tag.replace('_', ' ').title() for tag in advanced_classification['methodology_tags']]
            sections.append(f"- **Methodology Tags**: {', '.join(tags)}")

        if advanced_classification.get('compliance_requirements'):
            sections.append(f"- **Compliance Requirements**: {', '.join(advanced_classification['compliance_requirements'])}")

        sections.append('')

    # Survey Logic Section
    survey_logic = rfq.get('survey_logic')
    if survey_logic:
        sections.append("## Survey Logic Requirements:")

        if survey_logic.get('requires_piping_logic'):
            sections.append("- **Piping Logic**: Required")

        if survey_logic.get('requires_sampling_logic'):
            sections.append("- **Sampling Logic**: Required")

        if survey_logic.get('requires_screener_logic'):
            sections.append("- **Screener Logic**: Required")

        if survey_logic.get('custom_logic_requirements'):
            sections.append(f"- **Custom Logic**: {survey_logic['custom_logic_requirements']}")

        sections.append('')

    # Brand Usage Requirements Section
    brand_usage = rfq.get('brand_usage_requirements')
    if brand_usage:
        sections.append("## Brand & Usage Requirements:")

        if brand_usage.get('brand_recall_required'):
            sections.append("- **Brand Recall Questions**: Required")

        if brand_usage.get('brand_awareness_funnel'):
            sections.append("- **Brand Awareness Funnel**: Required")

        if brand_usage.get('brand_product_satisfaction'):
            sections.append("- **Brand/Product Satisfaction**: Required")

        if brand_usage.get('usage_frequency_tracking'):
            sections.append("- **Usage Frequency Tracking**: Required")

        sections.append('')

    # Additional Requirements Section
    additional_requirements = rfq.get('additional_requirements')
    if additional_requirements:
        sections.append("## Additional Requirements:")

        if additional_requirements.get('qnr_country'):
            sections.append(f"- **QNR Country**: {additional_requirements['qnr_country']}")

        if additional_requirements.get('recent_participation_screening'):
            sections.append("- **Recent Participation Screening**: Required")

        if additional_requirements.get('coi_check_required'):
            sections.append("- **Conflict of Interest Check**: Required")

        if additional_requirements.get('demog_basic_required'):
            sections.append("- **Basic Demographics**: Required")

        if additional_requirements.get('medical_conditions_general'):
            sections.append("- **General Medical Conditions Screening**: Required")

        if additional_requirements.get('medical_conditions_study'):
            sections.append("- **Study-Specific Medical Conditions**: Required")

        if additional_requirements.get('custom_screening_requirements'):
            sections.append(f"- **Custom Screening**: {additional_requirements['custom_screening_requirements']}")

        sections.append('')

    # Rules and Definitions
    if rfq.get('rules_and_definitions'):
        sections.append("## Rules & Definitions:")
        sections.append(rfq['rules_and_definitions'])
        sections.append('')

    return '\n'.join(sections)


def create_enhanced_description(rfq: Dict[str, Any]) -> str:
    """
    Combine enhanced text with original description
    """
    enhanced_text = build_enhanced_rfq_text(rfq)
    original_description = str(rfq.get('description', ''))

    if not enhanced_text.strip():
        return original_description

    if not original_description.strip():
        return enhanced_text

    return f"{original_description}\n\n---\n\n{enhanced_text}"


def generate_text_requirements(rfq: Dict[str, Any]) -> str:
    """
    Generate text introduction requirements based on methodology or custom text blocks
    """
    sections: List[str] = []

    # Check if custom text blocks are defined in survey_structure
    survey_structure = rfq.get('survey_structure', {})
    text_blocks = survey_structure.get('text_blocks', [])
    
    if text_blocks:
        # Use custom text blocks from RFQ
        sections.append("## MANDATORY TEXT BLOCK REQUIREMENTS:")
        sections.append("The following text blocks MUST be included in the survey with their specified content:")
        sections.append("")
        
        for block in text_blocks:
            block_id = block.get('id', '')
            block_name = block.get('name', block_id)
            block_type = block.get('type', 'custom')
            content = block.get('content', '')
            label = block.get('label', block_id)
            mandatory = block.get('mandatory', False)
            section_mapping = block.get('section_mapping')
            
            # Map section number to section name
            section_names = {
                1: 'Sample Plan (Section 1)',
                2: 'Screener (Section 2)',
                3: 'Brand/Product Awareness (Section 3)',
                4: 'Concept Exposure (Section 4)',
                5: 'Methodology (Section 5)',
                6: 'Additional Questions (Section 6)',
                7: 'Programmer Instructions (Section 7)'
            }
            section_name = section_names.get(section_mapping, f'Section {section_mapping}') if section_mapping else 'Not specified'
            
            mandatory_text = " (MANDATORY)" if mandatory else ""
            sections.append(f"### {block_name}{mandatory_text}:")
            sections.append(f"- **Label**: {label}")
            sections.append(f"- **Type**: {block_type}")
            sections.append(f"- **Section**: {section_name}")
            sections.append(f"- **Content**: {content}")
            sections.append("")
        
        sections.append("**IMPORTANT**: These text blocks must appear as standalone content blocks with the exact structure:")
        sections.append("- Use 'introText' for section introductions")
        sections.append("- Use 'textBlocks' array for mid-section content")
        sections.append("- Use 'closingText' for section endings")
        sections.append("- Include the specified 'label' field matching the requirements above")
        sections.append("- Include the specified 'content' field with the exact text provided")
        
        return '\n'.join(sections)
    
    # Fallback to methodology-based generation (legacy behavior)
    methodology = rfq.get('methodology', {})
    methodologies = methodology.get('required_methodologies', [])

    # Use selected_methodologies (new approach)
    selected_methodologies = methodology.get('selected_methodologies', [])
    if selected_methodologies:
        methodologies.extend(selected_methodologies)
    # Legacy: fallback to primary_method
    elif methodology.get('primary_method'):
        methodologies.append(methodology['primary_method'])

    if not methodologies:
        return ''

    # Get required text introductions
    required_texts = set()
    for method in methodologies:
        requirements = METHODOLOGY_TEXT_REQUIREMENTS.get(method, [])
        required_texts.update(requirements)

    # Always require study intro
    required_texts.add('Study_Intro')

    if required_texts:
        sections.append("## MANDATORY TEXT INTRODUCTIONS:")
        sections.append("The following text introductions MUST be included before relevant question sections:")
        sections.append("")

        for text_type in sorted(required_texts):
            if text_type == 'Study_Intro':
                sections.append("### Study Introduction (REQUIRED at beginning):")
                sections.append("- Thank participants for participation")
                sections.append("- Explain study purpose and estimated completion time")
                sections.append("- Provide confidentiality assurances")
                sections.append("- Mention voluntary participation and withdrawal rights")
            elif text_type == 'Concept_Intro':
                sections.append("### Concept Introduction (REQUIRED before concept evaluation):")
                sections.append("- Present concept details clearly")
                sections.append("- Include any stimuli or materials")
                sections.append("- Instruct participants to review carefully")
            elif text_type == 'Confidentiality_Agreement':
                sections.append("### Confidentiality Agreement (REQUIRED):")
                sections.append("- Assure response confidentiality")
                sections.append("- Explain research-only usage")
                sections.append("- Confirm no third-party sharing")
            elif text_type == 'Product_Usage':
                sections.append("### Product Usage Introduction (REQUIRED before usage questions):")
                sections.append("- Introduce product category")
                sections.append("- Request experience information")
                sections.append("- Explain qualification purpose")

            sections.append("")

        sections.append("**IMPORTANT**: These text introductions must appear as standalone content blocks before their related question sections, not as question text.")

        sections.append("")
        sections.append("**QNR SECTION MAPPING:**")
        sections.append("- **Sample Plan (Section 1)**: Study_Intro, Confidentiality_Agreement")
        sections.append("- **Brand/Product Awareness (Section 3)**: Product_Usage introduction")
        sections.append("- **Concept Exposure (Section 4)**: Concept_Intro for concept presentation")
        sections.append("- **Methodology (Section 5)**: Methodology-specific instructions")

    return '\n'.join(sections)


def createEnhancedDescriptionWithTextRequirements(rfq: Dict[str, Any]) -> str:
    """
    Create enhanced description with text requirements (matches frontend function name)
    """
    enhanced_text = build_enhanced_rfq_text(rfq)
    text_requirements = generate_text_requirements(rfq)
    original_description = rfq.get('description', '')

    parts: List[str] = []

    if original_description.strip():
        parts.append(original_description)

    if enhanced_text.strip():
        parts.append(enhanced_text)

    if text_requirements.strip():
        parts.append(text_requirements)

    return '\n\n---\n\n'.join(parts)