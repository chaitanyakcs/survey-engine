import {
  Survey,
  SurveyTextContent,
  TextComplianceReport,
  AiRATextLabel,
  EnhancedRFQRequest,
  METHODOLOGY_TEXT_REQUIREMENTS,
  AIRA_LABEL_TO_TYPE_MAP,
  TextContentType
} from '../types';

/**
 * Service for validating and generating survey text content based on AiRA requirements
 */
export class TextValidationService {
  /**
   * Get required text labels for given methodologies
   */
  static getRequiredTextForMethodology(methodologies: string[]): AiRATextLabel[] {
    const requiredLabels = new Set<AiRATextLabel>();

    methodologies.forEach(method => {
      const methodRequirements = METHODOLOGY_TEXT_REQUIREMENTS[method] || [];
      methodRequirements.forEach(label => requiredLabels.add(label as AiRATextLabel));
    });

    // Always require Study_Intro for any methodology
    requiredLabels.add('Study_Intro');

    return Array.from(requiredLabels);
  }

  /**
   * Validate survey compliance with AiRA text requirements
   */
  static validateSurveyTextCompliance(survey: Survey): TextComplianceReport {
    const methodologies = survey.methodologies || [];
    const requiredLabels = this.getRequiredTextForMethodology(methodologies);

    const textComplianceChecks = requiredLabels.map(label => {
      // Check if text is found in any section
      const found = this.findTextInSurvey(survey, label);

      return {
        label,
        type: AIRA_LABEL_TO_TYPE_MAP[label] as TextContentType,
        required: true,
        found: found.isFound,
        content: found.content,
        section: found.sectionTitle
      };
    });

    const missingElements = textComplianceChecks
      .filter(check => !check.found)
      .map(check => check.label);

    const complianceScore = textComplianceChecks.length > 0
      ? Math.round((textComplianceChecks.filter(c => c.found).length / textComplianceChecks.length) * 100)
      : 100;

    const complianceLevel = complianceScore >= 90 ? 'full' :
                           complianceScore >= 60 ? 'partial' : 'poor';

    const recommendations = this.generateRecommendations(missingElements, methodologies);

    return {
      survey_id: survey.survey_id,
      methodology: methodologies,
      required_text_elements: textComplianceChecks,
      missing_elements: missingElements,
      compliance_score: complianceScore,
      compliance_level: complianceLevel,
      recommendations,
      analysis_timestamp: new Date().toISOString()
    };
  }

  /**
   * Find specific text content in survey
   */
  private static findTextInSurvey(survey: Survey, label: AiRATextLabel): {
    isFound: boolean;
    content?: SurveyTextContent;
    sectionTitle?: string;
  } {
    if (!survey.sections) {
      return { isFound: false };
    }

    for (const section of survey.sections) {
      // Check intro text
      if (section.introText?.label === label) {
        return {
          isFound: true,
          content: section.introText,
          sectionTitle: section.title
        };
      }

      // Check text blocks
      if (section.textBlocks) {
        const foundText = section.textBlocks.find(text => text.label === label);
        if (foundText) {
          return {
            isFound: true,
            content: foundText,
            sectionTitle: section.title
          };
        }
      }

      // Check closing text
      if (section.closingText?.label === label) {
        return {
          isFound: true,
          content: section.closingText,
          sectionTitle: section.title
        };
      }
    }

    return { isFound: false };
  }

  /**
   * Generate missing text content based on AiRA requirements and RFQ context
   */
  static generateMissingTextContent(
    missingLabels: AiRATextLabel[],
    methodologies: string[],
    rfq?: EnhancedRFQRequest
  ): SurveyTextContent[] {
    return missingLabels.map((label, index) => {
      const type = AIRA_LABEL_TO_TYPE_MAP[label] as TextContentType;
      const content = this.generateTextContent(label, methodologies, rfq);

      return {
        id: `auto_text_${label.toLowerCase()}_${Date.now()}_${index}`,
        type,
        content,
        mandatory: true,
        label,
        order: index
      };
    });
  }

  /**
   * Generate appropriate text content based on label and context
   */
  private static generateTextContent(
    label: AiRATextLabel,
    methodologies: string[],
    rfq?: EnhancedRFQRequest
  ): string {
    const primaryMethod = methodologies[0] || 'survey';
    const estimatedTime = rfq?.survey_requirements?.completion_time_target?.replace('_', '-').replace('min', ' minutes') || '10-15 minutes';

    switch (label) {
      case 'Study_Intro':
        return this.generateStudyIntro(primaryMethod, estimatedTime, rfq);

      case 'Concept_Intro':
        return this.generateConceptIntro(rfq);

      case 'Confidentiality_Agreement':
        return this.generateConfidentialityText();

      case 'Product_Usage':
        return this.generateProductUsageText(rfq);

      default:
        return `${(label as string).replace('_', ' ')} text will be provided here.`;
    }
  }

  private static generateStudyIntro(method: string, estimatedTime: string, rfq?: EnhancedRFQRequest): string {
    const methodName = method.replace('_', ' ').toLowerCase();
    const businessContext = rfq?.business_context?.business_objective || 'market research';

    return `Thank you for agreeing to participate in this ${methodName} study. Your responses will help us understand ${businessContext}. This survey should take approximately ${estimatedTime} to complete.

Your participation is voluntary and your responses will be kept confidential. You may withdraw from the study at any time without penalty.`;
  }

  private static generateConceptIntro(rfq?: EnhancedRFQRequest): string {
    const stimuliDetails = rfq?.methodology?.stimuli_details;

    if (stimuliDetails) {
      return `Please review the following concept carefully:

${stimuliDetails}

We will ask for your opinions and reactions to this concept. Please take your time to read through all the details before proceeding to the questions.`;
    }

    return `Please review the following concept carefully. We will ask for your opinions and reactions to this concept. Please take your time to read through all the details before proceeding to the questions.`;
  }

  private static generateConfidentialityText(): string {
    return `**Confidentiality Agreement**

All responses in this survey are confidential and will only be used for research purposes. Your individual responses will not be shared with third parties or used for any commercial purposes outside of this research study.

Your participation is anonymous, and no personally identifiable information will be collected or stored in connection with your responses.`;
  }

  private static generateProductUsageText(rfq?: EnhancedRFQRequest): string {
    const productBackground = rfq?.business_context?.company_product_background;

    if (productBackground) {
      return `Before we begin, please tell us about your experience with ${productBackground}. Understanding your background and usage patterns will help us interpret your responses more accurately.`;
    }

    return `Before we begin, please tell us about your experience with products in this category. Understanding your background and usage patterns will help us interpret your responses more accurately.`;
  }

  /**
   * Generate compliance recommendations
   */
  private static generateRecommendations(
    missingElements: AiRATextLabel[],
    methodologies: string[]
  ): string[] {
    const recommendations: string[] = [];

    missingElements.forEach(label => {
      switch (label) {
        case 'Study_Intro':
          recommendations.push('Add a study introduction explaining the purpose, estimated time, and confidentiality assurances');
          break;
        case 'Concept_Intro':
          recommendations.push('Include concept introduction text before concept evaluation questions');
          break;
        case 'Confidentiality_Agreement':
          recommendations.push('Add confidentiality agreement text to ensure respondent privacy protection');
          break;
        case 'Product_Usage':
          recommendations.push('Include product usage screening text to establish respondent qualification');
          break;
        default:
          recommendations.push(`Add mandatory ${(label as string).replace('_', ' ')} text introduction`);
      }
    });

    // Add methodology-specific recommendations
    if (methodologies.includes('van_westendorp') || methodologies.includes('gabor_granger')) {
      recommendations.push('Ensure pricing methodology concepts are clearly explained before price evaluation');
    }

    return recommendations;
  }

  /**
   * Check if survey meets minimum text requirements
   */
  static meetsMinimumTextRequirements(survey: Survey): boolean {
    const report = this.validateSurveyTextCompliance(survey);
    return report.compliance_level !== 'poor' && report.missing_elements.length === 0;
  }

  /**
   * Get text content suggestions for methodology
   */
  static getTextSuggestionsForMethodology(methodology: string[]): {
    label: AiRATextLabel;
    description: string;
    priority: 'high' | 'medium' | 'low';
  }[] {
    const requiredLabels = this.getRequiredTextForMethodology(methodology);

    return requiredLabels.map(label => ({
      label,
      description: this.getTextDescription(label),
      priority: label === 'Study_Intro' ? 'high' : 'medium'
    }));
  }

  private static getTextDescription(label: AiRATextLabel): string {
    switch (label) {
      case 'Study_Intro':
        return 'Introduction explaining study purpose, time commitment, and participant rights';
      case 'Concept_Intro':
        return 'Introduction to concept materials before evaluation questions';
      case 'Confidentiality_Agreement':
        return 'Privacy and confidentiality assurance for respondents';
      case 'Product_Usage':
        return 'Product category experience and usage qualification';
      default:
        return `${(label as string).replace('_', ' ')} description`;
    }
  }
}

export default TextValidationService;