import { EnhancedRFQRequest, RFQObjective, RFQConstraint, RFQStakeholder, RFQSuccess } from '../types';

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
  if (rfq.methodology?.primary_method) {
    sections.push("## Methodology Preferences:");

    sections.push(`- **Primary Method**: ${rfq.methodology.primary_method}`);
    
    if (rfq.methodology.stimuli_details) {
      sections.push(`- **Stimuli Details**: ${rfq.methodology.stimuli_details}`);
    }
    
    if (rfq.methodology.methodology_requirements) {
      sections.push(`- **Requirements**: ${rfq.methodology.methodology_requirements}`);
    }
    sections.push('');
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

  // Business Context Section
  if (rfq.business_context) {
    sections.push("## Business Context:");

    if (rfq.business_context.company_product_background) {
      sections.push(`- **Background**: ${rfq.business_context.company_product_background}`);
    }

    if (rfq.business_context.business_problem) {
      sections.push(`- **Business Problem**: ${rfq.business_context.business_problem}`);
    }

    if (rfq.business_context.business_objective) {
      sections.push(`- **Business Objective**: ${rfq.business_context.business_objective}`);
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