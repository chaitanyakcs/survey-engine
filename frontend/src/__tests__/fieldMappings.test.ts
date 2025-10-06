/// <reference types="jest" />

import { useAppStore } from '../store/useAppStore';
import type { RFQFieldMapping } from '../types';

/**
 * Comprehensive tests for field mappings auto-fill functionality
 * Tests all field mappings to ensure they correctly map to the EnhancedRFQ form
 */

describe('Field Mappings Auto-Fill', () => {
  
  describe('Basic Info Fields', () => {
    it('should map title field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'title',
          value: 'Test Research Project',
          confidence: 0.95,
          source: 'Document header',
          reasoning: 'Extracted from title',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.title).toBe('Test Research Project');
    });

    it('should map description field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'description',
          value: 'This is a test research description',
          confidence: 0.9,
          source: 'Document body',
          reasoning: 'Extracted from overview',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.description).toBe('This is a test research description');
    });
  });

  describe('Business Context Fields', () => {
    it('should map company_product_background field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'company_product_background',
          value: 'We are a tech company focused on AI products',
          confidence: 0.92,
          source: 'Business context section',
          reasoning: 'Company background information',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.business_context?.company_product_background).toBe('We are a tech company focused on AI products');
    });

    it('should map business_problem field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'business_problem',
          value: 'Need to understand market positioning',
          confidence: 0.88,
          source: 'Problem statement',
          reasoning: 'Business challenge identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.business_context?.business_problem).toBe('Need to understand market positioning');
    });

    it('should map business_objective field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'business_objective',
          value: 'Improve product-market fit',
          confidence: 0.9,
          source: 'Objectives section',
          reasoning: 'Business goal identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.business_context?.business_objective).toBe('Improve product-market fit');
    });

    it('should map stakeholder_requirements field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'stakeholder_requirements',
          value: 'Executive team needs quarterly insights',
          confidence: 0.85,
          source: 'Stakeholder section',
          reasoning: 'Stakeholder needs identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.business_context?.stakeholder_requirements).toBe('Executive team needs quarterly insights');
    });

    it('should map decision_criteria field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'decision_criteria',
          value: 'Actionable insights for product roadmap',
          confidence: 0.87,
          source: 'Success criteria',
          reasoning: 'Decision criteria defined',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.business_context?.decision_criteria).toBe('Actionable insights for product roadmap');
    });

    it('should map budget_range field correctly', () => {
      const testCases = [
        { input: 'under 10k', expected: 'under_10k' },
        { input: 'less than 10k', expected: 'under_10k' },
        { input: '10k to 50k', expected: '10k_50k' },
        { input: '10-50k', expected: '10k_50k' },
        { input: '50k to 100k', expected: '50k_100k' },
        { input: '50-100k', expected: '50k_100k' },
        { input: 'over 100k', expected: '100k_plus' },
        { input: 'more than 100k', expected: '100k_plus' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'budget_range',
            value: input,
            confidence: 0.9,
            source: 'Budget section',
            reasoning: 'Budget range extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.business_context?.budget_range).toBe(expected);
      });
    });

    it('should map timeline_constraints field correctly', () => {
      const testCases = [
        { input: 'urgent deadline', expected: 'rush' },
        { input: 'rush project', expected: 'rush' },
        { input: 'flexible timeline', expected: 'flexible' },
        { input: 'standard delivery', expected: 'standard' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'timeline_constraints',
            value: input,
            confidence: 0.9,
            source: 'Timeline section',
            reasoning: 'Timeline constraints extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.business_context?.timeline_constraints).toBe(expected);
      });
    });
  });

  describe('Research Objectives Fields', () => {
    it('should map research_audience field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'research_audience',
          value: 'B2C consumers aged 25-45',
          confidence: 0.93,
          source: 'Target audience section',
          reasoning: 'Audience demographics identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.research_objectives?.research_audience).toBe('B2C consumers aged 25-45');
    });

    it('should map success_criteria field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'success_criteria',
          value: 'Identify top 3 product features',
          confidence: 0.89,
          source: 'Success criteria section',
          reasoning: 'Success criteria defined',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.research_objectives?.success_criteria).toBe('Identify top 3 product features');
    });

    it('should map key_research_questions as array', () => {
      const testCases = [
        {
          input: ['Question 1', 'Question 2', 'Question 3'],
          expected: ['Question 1', 'Question 2', 'Question 3']
        },
        {
          input: 'Question 1\nQuestion 2\nQuestion 3',
          expected: ['Question 1', 'Question 2', 'Question 3']
        }
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'key_research_questions',
            value: input,
            confidence: 0.9,
            source: 'Research questions',
            reasoning: 'Questions extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.research_objectives?.key_research_questions).toEqual(expected);
      });
    });

    it('should map success_metrics field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'success_metrics',
          value: 'Net Promoter Score and feature adoption rate',
          confidence: 0.87,
          source: 'Metrics section',
          reasoning: 'Success metrics identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.research_objectives?.success_metrics).toBe('Net Promoter Score and feature adoption rate');
    });

    it('should map validation_requirements field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'validation_requirements',
          value: 'Results must be statistically significant at 95% confidence',
          confidence: 0.88,
          source: 'Validation section',
          reasoning: 'Validation requirements identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.research_objectives?.validation_requirements).toBe('Results must be statistically significant at 95% confidence');
    });

    it('should map measurement_approach field correctly', () => {
      const testCases = [
        { input: 'quantitative research', expected: 'quantitative' },
        { input: 'qualitative interviews', expected: 'qualitative' },
        { input: 'mixed methods approach', expected: 'mixed_methods' },
        { input: 'general research', expected: 'mixed_methods' }, // default
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'measurement_approach',
            value: input,
            confidence: 0.9,
            source: 'Methodology',
            reasoning: 'Measurement approach identified',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.research_objectives?.measurement_approach).toBe(expected);
      });
    });
  });

  describe('Methodology Fields', () => {
    it('should map stimuli_details field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'stimuli_details',
          value: 'Product concept with 3 pricing tiers',
          confidence: 0.91,
          source: 'Stimuli section',
          reasoning: 'Stimuli details extracted',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.methodology?.stimuli_details).toBe('Product concept with 3 pricing tiers');
    });

    it('should map methodology_requirements field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'methodology_requirements',
          value: 'Van Westendorp pricing analysis required',
          confidence: 0.92,
          source: 'Methodology section',
          reasoning: 'Methodology requirements identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.methodology?.methodology_requirements).toBe('Van Westendorp pricing analysis required');
    });

    it('should map complexity_level field correctly', () => {
      const testCases = [
        { input: 'simple survey', expected: 'simple' },
        { input: 'basic research', expected: 'simple' },
        { input: 'standard methodology', expected: 'standard' },
        { input: 'complex analysis', expected: 'advanced' },
        { input: 'advanced research', expected: 'advanced' },
        { input: 'sophisticated approach', expected: 'advanced' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'complexity_level',
            value: input,
            confidence: 0.9,
            source: 'Complexity section',
            reasoning: 'Complexity level identified',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.methodology?.complexity_level).toBe(expected);
      });
    });

    it('should map required_methodologies as array', () => {
      const testCases = [
        {
          input: ['Conjoint', 'MaxDiff', 'Pricing'],
          expected: ['Conjoint', 'MaxDiff', 'Pricing']
        },
        {
          input: 'Conjoint, MaxDiff, Pricing',
          expected: ['Conjoint', 'MaxDiff', 'Pricing']
        }
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'required_methodologies',
            value: input,
            confidence: 0.9,
            source: 'Methodologies',
            reasoning: 'Methodologies extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.methodology?.required_methodologies).toEqual(expected);
      });
    });

    it('should map sample_size_target field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'sample_size_target',
          value: '400-600 respondents',
          confidence: 0.93,
          source: 'Sample size section',
          reasoning: 'Sample size target identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.methodology?.sample_size_target).toBe('400-600 respondents');
    });
  });

  describe('Survey Requirements Fields', () => {
    it('should map sample_plan field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'sample_plan',
          value: 'National sample, 500 respondents, 15 min LOI',
          confidence: 0.91,
          source: 'Sample plan section',
          reasoning: 'Sample plan details extracted',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.survey_requirements?.sample_plan).toBe('National sample, 500 respondents, 15 min LOI');
    });

    it('should map must_have_questions as array', () => {
      const testCases = [
        {
          input: ['Q1: Brand awareness', 'Q2: Purchase intent', 'Q3: Demographics'],
          expected: ['Q1: Brand awareness', 'Q2: Purchase intent', 'Q3: Demographics']
        },
        {
          input: 'Q1: Brand awareness\nQ2: Purchase intent\nQ3: Demographics',
          expected: ['Q1: Brand awareness', 'Q2: Purchase intent', 'Q3: Demographics']
        }
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'must_have_questions',
            value: input,
            confidence: 0.9,
            source: 'Must-have questions',
            reasoning: 'Questions extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_requirements?.must_have_questions).toEqual(expected);
      });
    });

    it('should map completion_time_target field correctly', () => {
      const testCases = [
        { input: '5-10 minutes', expected: '5_10_min' },
        { input: '10-15 minutes', expected: '10_15_min' },
        { input: '15-25 minutes', expected: '15_25_min' },
        { input: '25+ minutes', expected: '25_plus_min' },
        { input: '30 minutes', expected: '25_plus_min' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'completion_time_target',
            value: input,
            confidence: 0.9,
            source: 'Time section',
            reasoning: 'Completion time extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_requirements?.completion_time_target).toBe(expected);
      });
    });

    it('should map device_compatibility field correctly', () => {
      const testCases = [
        { input: 'mobile optimized', expected: 'mobile_first' },
        { input: 'desktop only', expected: 'desktop_first' },
        { input: 'responsive design', expected: 'both' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'device_compatibility',
            value: input,
            confidence: 0.9,
            source: 'Device section',
            reasoning: 'Device compatibility extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_requirements?.device_compatibility).toBe(expected);
      });
    });

    it('should map accessibility_requirements field correctly', () => {
      const testCases = [
        { input: 'enhanced accessibility', expected: 'enhanced' },
        { input: 'full ADA compliance', expected: 'full_compliance' },
        { input: 'standard requirements', expected: 'standard' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'accessibility_requirements',
            value: input,
            confidence: 0.9,
            source: 'Accessibility section',
            reasoning: 'Accessibility requirements extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_requirements?.accessibility_requirements).toBe(expected);
      });
    });

    it('should map data_quality_requirements field correctly', () => {
      const testCases = [
        { input: 'premium data quality', expected: 'premium' },
        { input: 'basic quality checks', expected: 'basic' },
        { input: 'standard validation', expected: 'standard' },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'data_quality_requirements',
            value: input,
            confidence: 0.9,
            source: 'Quality section',
            reasoning: 'Data quality requirements extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_requirements?.data_quality_requirements).toBe(expected);
      });
    });
  });

  describe('Survey Structure Fields', () => {
    it('should map qnr_sections_detected as array', () => {
      const testCases = [
        {
          input: ['screener', 'brand_awareness', 'concept_exposure'],
          expected: ['screener', 'brand_awareness', 'concept_exposure']
        },
        {
          input: 'screener, brand_awareness, concept_exposure',
          expected: ['screener', 'brand_awareness', 'concept_exposure']
        }
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'qnr_sections_detected',
            value: input,
            confidence: 0.9,
            source: 'QNR sections',
            reasoning: 'QNR sections extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_structure?.qnr_sections).toEqual(expected);
      });
    });

    it('should map text_requirements_detected as array', () => {
      const testCases = [
        {
          input: ['study_intro', 'concept_intro', 'confidentiality_agreement'],
          expected: ['study_intro', 'concept_intro', 'confidentiality_agreement']
        },
        {
          input: 'study_intro, concept_intro, confidentiality_agreement',
          expected: ['study_intro', 'concept_intro', 'confidentiality_agreement']
        }
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'text_requirements_detected',
            value: input,
            confidence: 0.9,
            source: 'Text requirements',
            reasoning: 'Text requirements extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_structure?.text_requirements).toEqual(expected);
      });
    });
  });

  describe('Survey Logic Fields', () => {
    it('should map requires_piping_logic as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
        { input: 'true', expected: true },
        { input: 'yes', expected: true },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'requires_piping_logic',
            value: input,
            confidence: 0.9,
            source: 'Logic requirements',
            reasoning: 'Piping logic requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_logic?.requires_piping_logic).toBe(expected);
      });
    });

    it('should map requires_sampling_logic as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'requires_sampling_logic',
            value: input,
            confidence: 0.9,
            source: 'Logic requirements',
            reasoning: 'Sampling logic requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_logic?.requires_sampling_logic).toBe(expected);
      });
    });

    it('should map requires_screener_logic as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'requires_screener_logic',
            value: input,
            confidence: 0.9,
            source: 'Logic requirements',
            reasoning: 'Screener logic requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.survey_logic?.requires_screener_logic).toBe(expected);
      });
    });

    it('should map custom_logic_requirements field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'custom_logic_requirements',
          value: 'Skip pattern based on purchase intent',
          confidence: 0.88,
          source: 'Logic section',
          reasoning: 'Custom logic requirements identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.survey_logic?.custom_logic_requirements).toBe('Skip pattern based on purchase intent');
    });
  });

  describe('Brand Usage Requirements Fields', () => {
    it('should map brand_recall_required as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'brand_recall_required',
            value: input,
            confidence: 0.9,
            source: 'Brand requirements',
            reasoning: 'Brand recall requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.brand_usage_requirements?.brand_recall_required).toBe(expected);
      });
    });

    it('should map brand_awareness_funnel as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'brand_awareness_funnel',
            value: input,
            confidence: 0.9,
            source: 'Brand requirements',
            reasoning: 'Brand awareness funnel requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.brand_usage_requirements?.brand_awareness_funnel).toBe(expected);
      });
    });

    it('should map brand_product_satisfaction as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'brand_product_satisfaction',
            value: input,
            confidence: 0.9,
            source: 'Brand requirements',
            reasoning: 'Brand satisfaction requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.brand_usage_requirements?.brand_product_satisfaction).toBe(expected);
      });
    });

    it('should map usage_frequency_tracking as boolean', () => {
      const testCases = [
        { input: true, expected: true },
        { input: false, expected: false },
      ];

      testCases.forEach(({ input, expected }) => {
        const mappings: RFQFieldMapping[] = [
          {
            field: 'usage_frequency_tracking',
            value: input,
            confidence: 0.9,
            source: 'Usage requirements',
            reasoning: 'Usage frequency tracking requirement extracted',
            needs_review: false,
            user_action: 'accepted'
          }
        ];

        const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
        expect(rfqUpdates.brand_usage_requirements?.usage_frequency_tracking).toBe(expected);
      });
    });
  });

  describe('Advanced Classification Fields', () => {
    it('should map industry_classification field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'industry_classification',
          value: 'Technology',
          confidence: 0.94,
          source: 'Industry section',
          reasoning: 'Industry classification identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.advanced_classification?.industry_classification).toBe('Technology');
    });

    it('should map respondent_classification field correctly', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'respondent_classification',
          value: 'B2C Consumers',
          confidence: 0.92,
          source: 'Respondent section',
          reasoning: 'Respondent classification identified',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.advanced_classification?.respondent_classification).toBe('B2C Consumers');
    });
  });

  describe('Multiple Field Mappings', () => {
    it('should correctly map multiple fields at once', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'title',
          value: 'Market Research Study',
          confidence: 0.95,
          source: 'Header',
          reasoning: 'Title extracted',
          needs_review: false,
          user_action: 'accepted'
        },
        {
          field: 'company_product_background',
          value: 'Tech startup in AI space',
          confidence: 0.92,
          source: 'Background',
          reasoning: 'Company context extracted',
          needs_review: false,
          user_action: 'accepted'
        },
        {
          field: 'research_audience',
          value: 'B2B decision makers',
          confidence: 0.90,
          source: 'Audience',
          reasoning: 'Audience identified',
          needs_review: false,
          user_action: 'accepted'
        },
        {
          field: 'budget_range',
          value: '50k to 100k',
          confidence: 0.88,
          source: 'Budget',
          reasoning: 'Budget extracted',
          needs_review: false,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates.title).toBe('Market Research Study');
      expect(rfqUpdates.business_context?.company_product_background).toBe('Tech startup in AI space');
      expect(rfqUpdates.research_objectives?.research_audience).toBe('B2B decision makers');
      expect(rfqUpdates.business_context?.budget_range).toBe('50k_100k');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty mappings array', () => {
      const mappings: RFQFieldMapping[] = [];
      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(Object.keys(rfqUpdates).length).toBeGreaterThanOrEqual(0);
    });

    it('should handle unknown field mapping gracefully', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'unknown_field',
          value: 'some value',
          confidence: 0.5,
          source: 'Unknown',
          reasoning: 'Unknown',
          needs_review: true,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      // Should not throw error, just log warning
      expect(rfqUpdates).toBeDefined();
    });

    it('should handle null/undefined values gracefully', () => {
      const mappings: RFQFieldMapping[] = [
        {
          field: 'title',
          value: null,
          confidence: 0.5,
          source: 'Unknown',
          reasoning: 'Unknown',
          needs_review: true,
          user_action: 'accepted'
        }
      ];

      const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);
      
      expect(rfqUpdates).toBeDefined();
    });
  });
});

