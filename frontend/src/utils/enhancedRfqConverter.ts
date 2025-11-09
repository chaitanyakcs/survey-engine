import { EnhancedRFQRequest, RFQObjective, RFQConstraint, RFQStakeholder, RFQSuccess, METHODOLOGY_TEXT_REQUIREMENTS } from '../types';

/**
 * Convert Enhanced RFQ structured data into enriched text for LLM processing
 * This maintains the open-closed principle by converting rich data to text
 * without requiring workflow changes.
 */
export function buildEnhancedRFQText(rfq: EnhancedRFQRequest): string {
  const sections: string[] = [];

  // Research Objectives Section
  if (rfq.research_objectives?.key_research_questions && rfq.research_objectives.key_research_questions.length > 0) {
    sections.push("## Research Objectives:");
    rfq.research_objectives.key_research_questions.forEach((objective: string, index: number) => {
      sections.push(`${index + 1}. ${objective}`);
    });

    sections.push('');
  }

  // Note: constraints field not in EnhancedRFQRequest interface
  // Project Constraints Section
  // if (rfq.constraints && rfq.constraints.length > 0) {
  //   sections.push("## Project Constraints:");
  //   rfq.constraints.forEach((constraint: RFQConstraint) => {
  //     const constraintEmoji = getConstraintEmoji(constraint.type);
  //     let constraintText = `${constraintEmoji}**${formatConstraintType(constraint.type)}**: ${constraint.description}`;

  //     if (constraint.value) {
  //       constraintText += ` (${constraint.value})`;
  //     }
  //     sections.push(`- ${constraintText}`);
  //   });
  //   sections.push('');
  // }

  // Target Audience Details
  if (rfq.research_objectives?.research_audience) {
    sections.push("## Target Audience:");
    sections.push(`- **Research Audience**: ${rfq.research_objectives.research_audience}`);
    sections.push('');
  }

  // Methodology Preferences
  const selectedMethods = rfq.methodology?.selected_methodologies || [];
  const primaryMethod = rfq.methodology?.primary_method; // Legacy support
  const hasMethodologies = selectedMethods.length > 0 || primaryMethod;
  
  if (hasMethodologies) {
    sections.push("## Methodology Preferences:");

    if (selectedMethods.length > 0) {
      const methodsList = selectedMethods.map(m => m.replace('_', ' ')).join(', ');
      sections.push(`- **Selected Methodologies**: ${methodsList}`);
    } else if (primaryMethod) {
      // Legacy: use primary_method if selected_methodologies not available
      sections.push(`- **Primary Method**: ${primaryMethod}`);
    }

    if (rfq.methodology.stimuli_details) {
      sections.push(`- **Stimuli Details**: ${rfq.methodology.stimuli_details}`);
    }

    sections.push('');
  }

  // Concept Stimuli (NEW)
  if (rfq.concept_stimuli && rfq.concept_stimuli.length > 0) {
    sections.push("## Concept Stimuli:");
    rfq.concept_stimuli.forEach((stimulus, index) => {
      sections.push(`### Concept ${index + 1}: ${stimulus.title}`);
      sections.push(stimulus.description);
      sections.push('');
    });
  }

  // Note: stakeholders field not in EnhancedRFQRequest interface
  // Key Stakeholders Section
  // if (rfq.stakeholders && rfq.stakeholders.length > 0) {
  //   sections.push("## Key Stakeholders:");
  //   rfq.stakeholders.forEach((stakeholder: RFQStakeholder) => {
  //     const influenceEmoji = getInfluenceEmoji(stakeholder.decision_influence);
  //     sections.push(`- **${stakeholder.role}** ${influenceEmoji}(${stakeholder.decision_influence} influence)`);
  //     sections.push(`  ${stakeholder.requirements}`);
  //   });
  //   sections.push('');
  // }

  // Note: success_metrics field not in EnhancedRFQRequest interface
  // Success Metrics Section
  // if (rfq.success_metrics && rfq.success_metrics.length > 0) {
  //   sections.push("## Success Metrics & KPIs:");
  //   rfq.success_metrics.forEach((metric: RFQSuccess, index: number) => {
  //     sections.push(`${index + 1}. **${metric.metric}**`);
  //     sections.push(`   Description: ${metric.description}`);
  //     sections.push(`   Measurement: ${metric.measurement}`);
  //     sections.push('');
  //   });
  // }

  // Business Context Section (SIMPLIFIED)
  if (rfq.business_context) {
    sections.push("## Business Context:");

    if (rfq.business_context.company_product_background) {
      sections.push(`- **Background**: ${rfq.business_context.company_product_background}`);
    }

    if (rfq.business_context.business_problem_and_objective) {
      sections.push(`- **Business Problem & Objective**: ${rfq.business_context.business_problem_and_objective}`);
    }

    if (rfq.business_context.sample_requirements) {
      sections.push(`- **Sample Requirements**: ${rfq.business_context.sample_requirements}`);
    }

    if (rfq.business_context.budget_range) {
      const budgetLabel = rfq.business_context.budget_range.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      sections.push(`- **Budget Range**: ${budgetLabel}`);
    }

    if (rfq.business_context.timeline_constraints) {
      const timelineLabel = rfq.business_context.timeline_constraints.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      sections.push(`- **Timeline Constraints**: ${timelineLabel}`);
    }

    sections.push('');
  }

  // Note: generation_config field not in EnhancedRFQRequest interface
  // Generation Configuration
  // if (rfq.generation_config) {
  //   sections.push("## Survey Generation Preferences:");
  //   sections.push(`- **Creativity Level**: ${rfq.generation_config.creativity_level || 'balanced'}`);
  //   sections.push(`- **Length Preference**: ${rfq.generation_config.length_preference || 'standard'}`);
  //   sections.push(`- **Complexity Level**: ${rfq.generation_config.complexity_level || 'intermediate'}`);

  //   if (rfq.generation_config.include_validation_questions) {
  //     sections.push(`- **Include Validation Questions**: Yes`);
  //   }

  //   if (rfq.generation_config.enable_adaptive_routing) {
  //     sections.push(`- **Enable Adaptive Routing**: Yes`);
  //   }
  //   sections.push('');
  // }

  // Note: estimated_budget and expected_timeline fields not in EnhancedRFQRequest interface
  // Budget and Timeline Information
  // if (rfq.estimated_budget || rfq.expected_timeline) {
  //   sections.push("## Project Details:");

  //   if (rfq.estimated_budget) {
  //     sections.push(`- **Estimated Budget**: ${rfq.estimated_budget}`);
  //   }

  //   if (rfq.expected_timeline) {
  //     sections.push(`- **Expected Timeline**: ${rfq.expected_timeline}`);
  //   }

  //   if (rfq.approval_requirements && rfq.approval_requirements.length > 0) {
  //     sections.push(`- **Approval Requirements**: ${rfq.approval_requirements.join(', ')}`);
  //   }
  //   sections.push('');
  // }

  // Survey Requirements Section (SIMPLIFIED)
  if (rfq.survey_requirements) {
    sections.push("## Survey Requirements:");

    if (rfq.survey_requirements.sample_plan) {
      sections.push(`- **Sample Plan**: ${rfq.survey_requirements.sample_plan}`);
    }

    if (rfq.survey_requirements.required_sections && rfq.survey_requirements.required_sections.length > 0) {
      sections.push(`- **Required Sections**: ${rfq.survey_requirements.required_sections.join(', ')}`);
    }

    if (rfq.survey_requirements.screener_requirements) {
      sections.push(`- **Screener Requirements**: ${rfq.survey_requirements.screener_requirements}`);
    }

    if (rfq.survey_requirements.completion_time_target) {
      const timeLabel = rfq.survey_requirements.completion_time_target.replace('_', '-').replace('min', ' minutes');
      sections.push(`- **Target Completion Time**: ${timeLabel}`);
    }

    if (rfq.survey_requirements.device_compatibility) {
      const deviceLabel = rfq.survey_requirements.device_compatibility.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      sections.push(`- **Device Compatibility**: ${deviceLabel}`);
    }

    sections.push('');
  }

  // Advanced Classification Section (SIMPLIFIED)
  if (rfq.advanced_classification) {
    sections.push("## Classification:");

    if (rfq.advanced_classification.industry_classification) {
      const industryLabel = rfq.advanced_classification.industry_classification.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      sections.push(`- **Industry**: ${industryLabel}`);
    }

    if (rfq.advanced_classification.respondent_classification) {
      sections.push(`- **Respondent Type**: ${rfq.advanced_classification.respondent_classification}`);
    }

    if (rfq.advanced_classification.methodology_tags && rfq.advanced_classification.methodology_tags.length > 0) {
      const tags = rfq.advanced_classification.methodology_tags.map(tag => tag.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())).join(', ');
      sections.push(`- **Methodology Tags**: ${tags}`);
    }

    sections.push('');
  }

  // Additional Info (NEW)
  if (rfq.additional_info) {
    sections.push("## Additional Information:");
    sections.push(rfq.additional_info);
    sections.push('');
  }

  // Rules and Definitions
  if (rfq.rules_and_definitions) {
    sections.push("## Rules & Definitions:");
    sections.push(rfq.rules_and_definitions);
    sections.push('');
  }

  return sections.join('\n');
}

// Helper functions for formatting
function getPriorityEmoji(priority: string): string {
  switch (priority) {
    case 'high': return '🔴 ';
    case 'medium': return '🟡 ';
    case 'low': return '🟢 ';
    default: return '';
  }
}

function getConstraintEmoji(type: string): string {
  switch (type) {
    case 'budget': return '💰 ';
    case 'timeline': return '⏰ ';
    case 'sample_size': return '👥 ';
    case 'methodology': return '📊 ';
    default: return '📋 ';
  }
}

function formatConstraintType(type: string): string {
  return type.split('_').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
}

function getInfluenceEmoji(influence: string): string {
  switch (influence) {
    case 'high': return '🔴 ';
    case 'medium': return '🟡 ';
    case 'low': return '🟢 ';
    default: return '';
  }
}

function formatDemographics(demographics: Record<string, any>): string {
  return Object.entries(demographics)
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ');
}

/**
 * Combine enhanced text with original description
 */
export function createEnhancedDescription(rfq: EnhancedRFQRequest): string {
  const enhancedText = buildEnhancedRFQText(rfq);
  const originalDescription = rfq.description || '';

  if (!enhancedText.trim()) {
    return originalDescription;
  }

  if (!originalDescription.trim()) {
    return enhancedText;
  }

  return `${originalDescription}\n\n---\n\n${enhancedText}`;
}

/**
 * Generate text introduction requirements based on methodology
 */
export function generateTextRequirements(rfq: EnhancedRFQRequest): string {
  const sections: string[] = [];

  // Get methodologies (use selected_methodologies, fallback to primary_method for legacy)
  const methodologies: string[] = [];
  if (rfq.methodology?.selected_methodologies && rfq.methodology.selected_methodologies.length > 0) {
    methodologies.push(...rfq.methodology.selected_methodologies);
  } else if (rfq.methodology?.primary_method) {
    // Legacy: fallback to primary_method
    methodologies.push(rfq.methodology.primary_method);
  }
  if (rfq.advanced_classification?.methodology_tags) {
    methodologies.push(...rfq.advanced_classification.methodology_tags);
  }

  if (methodologies.length === 0) return '';

  // Get required text introductions
  const requiredTexts = new Set<string>();
  methodologies.forEach(method => {
    const requirements = METHODOLOGY_TEXT_REQUIREMENTS[method] || [];
    requirements.forEach(req => requiredTexts.add(req));
  });

  // Always require study intro
  requiredTexts.add('Study_Intro');

  if (requiredTexts.size > 0) {
    sections.push("## MANDATORY TEXT INTRODUCTIONS:");
    sections.push("The following text introductions MUST be included before relevant question sections:");
    sections.push("");

    Array.from(requiredTexts).forEach(textType => {
      switch (textType) {
        case 'Study_Intro':
          sections.push("### Study Introduction (REQUIRED at beginning):");
          sections.push("- Thank participants for participation");
          sections.push("- Explain study purpose and estimated completion time");
          sections.push("- Provide confidentiality assurances");
          sections.push("- Mention voluntary participation and withdrawal rights");
          break;

        case 'Concept_Intro':
          sections.push("### Concept Introduction (REQUIRED before concept evaluation):");
          sections.push("- Present concept details clearly");
          sections.push("- Include any stimuli or materials");
          sections.push("- Instruct participants to review carefully");
          break;

        case 'Confidentiality_Agreement':
          sections.push("### Confidentiality Agreement (REQUIRED):");
          sections.push("- Assure response confidentiality");
          sections.push("- Explain research-only usage");
          sections.push("- Confirm no third-party sharing");
          break;

        case 'Product_Usage':
          sections.push("### Product Usage Introduction (REQUIRED before usage questions):");
          sections.push("- Introduce product category");
          sections.push("- Request experience information");
          sections.push("- Explain qualification purpose");
          break;
      }
      sections.push("");
    });

    sections.push("**IMPORTANT**: These text introductions must appear as standalone content blocks before their related question sections, not as question text.");
  }

  return sections.join('\n');
}

/**
 * Create enhanced description with text requirements
 */
export function createEnhancedDescriptionWithTextRequirements(rfq: EnhancedRFQRequest): string {
  const enhancedText = buildEnhancedRFQText(rfq);
  const textRequirements = generateTextRequirements(rfq);
  const originalDescription = rfq.description || '';

  const parts: string[] = [];

  if (originalDescription.trim()) {
    parts.push(originalDescription);
  }

  if (enhancedText.trim()) {
    parts.push(enhancedText);
  }

  if (textRequirements.trim()) {
    parts.push(textRequirements);
  }

  return parts.join('\n\n---\n\n');
}