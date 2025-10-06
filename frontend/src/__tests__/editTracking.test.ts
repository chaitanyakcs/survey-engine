/// <reference types="jest" />

import { useAppStore } from '../store/useAppStore';
import type { EnhancedRFQRequest } from '../types';

describe('Edit Tracking', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAppStore.setState({
      enhancedRfq: {
        title: '',
        description: '',
        business_context: {
          company_product_background: '',
          business_problem: '',
          business_objective: '',
          stakeholder_requirements: '',
          decision_criteria: '',
          budget_range: '10k_50k',
          timeline_constraints: 'standard'
        },
        research_objectives: {
          research_audience: '',
          success_criteria: '',
          key_research_questions: [],
          success_metrics: '',
          validation_requirements: '',
          measurement_approach: 'mixed_methods'
        },
        methodology: {
          primary_method: 'basic_survey',
          stimuli_details: '',
          methodology_requirements: '',
          complexity_level: 'standard',
          required_methodologies: [],
          sample_size_target: '400-600 respondents'
        },
        survey_requirements: {
          sample_plan: '',
          required_sections: [],
          must_have_questions: [],
          screener_requirements: '',
          completion_time_target: '15_25_min',
          device_compatibility: 'both',
          accessibility_requirements: 'standard',
          data_quality_requirements: 'standard'
        },
        advanced_classification: {
          industry_classification: '',
          respondent_classification: '',
          methodology_tags: [],
          compliance_requirements: ['Standard Data Protection']
        },
        survey_structure: {
          qnr_sections: [],
          text_requirements: []
        },
        survey_logic: {
          requires_piping_logic: false,
          requires_sampling_logic: false,
          requires_screener_logic: false,
          custom_logic_requirements: '',
          piping_logic: '',
          sampling_logic: '',
          screener_logic: '',
          user_categorization: ''
        },
        brand_usage_requirements: {
          brand_recall_required: false,
          brand_awareness_funnel: false,
          brand_product_satisfaction: false,
          usage_frequency_tracking: false,
          brand_recall_needed: false,
          brand_satisfaction: false,
          purchase_decision_factors: false,
          category_usage_financial: false,
          future_consideration: false
        },
        rules_and_definitions: 'Standard market research terminology and definitions apply.'
      },
      editedFields: new Set<string>(),
      originalFieldValues: {}
    });
  });

  it('should track field edits correctly', () => {
    const { trackFieldEdit, getEditedFieldsSummary, setEnhancedRfq } = useAppStore.getState();
    
    // First update the state, then track the edit
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'New Project Title' });
    trackFieldEdit('title', 'New Project Title');
    
    // Check that the field is tracked as edited
    const summary = getEditedFieldsSummary();
    expect(summary).toHaveLength(1);
    expect(summary[0].field).toBe('title');
    expect(summary[0].currentValue).toBe('New Project Title');
  });

  it('should track nested field edits correctly', () => {
    const { trackFieldEdit, getEditedFieldsSummary, setEnhancedRfq } = useAppStore.getState();
    
    // First update the state, then track the edit
    setEnhancedRfq({
      ...useAppStore.getState().enhancedRfq,
      business_context: {
        ...useAppStore.getState().enhancedRfq.business_context,
        company_product_background: 'Updated company background'
      }
    });
    trackFieldEdit('business_context.company_product_background', 'Updated company background');
    
    // Check that the field is tracked as edited
    const summary = getEditedFieldsSummary();
    expect(summary).toHaveLength(1);
    expect(summary[0].field).toBe('business_context.company_product_background');
    expect(summary[0].currentValue).toBe('Updated company background');
  });

  it('should not track fields that revert to original value', () => {
    const { trackFieldEdit, getEditedFieldsSummary, setEnhancedRfq } = useAppStore.getState();
    
    // Set initial value
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'Original Title' });
    
    // Edit the field
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'Modified Title' });
    trackFieldEdit('title', 'Modified Title');
    expect(getEditedFieldsSummary()).toHaveLength(1);
    
    // Revert to original value
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'Original Title' });
    trackFieldEdit('title', 'Original Title');
    
    // Should no longer be tracked as edited
    expect(getEditedFieldsSummary()).toHaveLength(0);
  });

  it('should clear edit tracking correctly', () => {
    const { trackFieldEdit, clearEditTracking, getEditedFieldsSummary, setEnhancedRfq } = useAppStore.getState();
    
    // Track some edits
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'Test Title' });
    trackFieldEdit('title', 'Test Title');
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, description: 'Test Description' });
    trackFieldEdit('description', 'Test Description');
    
    expect(getEditedFieldsSummary()).toHaveLength(2);
    
    // Clear tracking
    clearEditTracking();
    
    expect(getEditedFieldsSummary()).toHaveLength(0);
  });

  it('should handle multiple field edits', () => {
    const { trackFieldEdit, getEditedFieldsSummary, setEnhancedRfq } = useAppStore.getState();
    
    // Track multiple edits
    setEnhancedRfq({ ...useAppStore.getState().enhancedRfq, title: 'Project Title' });
    trackFieldEdit('title', 'Project Title');
    
    setEnhancedRfq({
      ...useAppStore.getState().enhancedRfq,
      business_context: {
        ...useAppStore.getState().enhancedRfq.business_context,
        business_problem: 'Business problem'
      }
    });
    trackFieldEdit('business_context.business_problem', 'Business problem');
    
    setEnhancedRfq({
      ...useAppStore.getState().enhancedRfq,
      research_objectives: {
        ...useAppStore.getState().enhancedRfq.research_objectives,
        research_audience: 'Target audience'
      }
    });
    trackFieldEdit('research_objectives.research_audience', 'Target audience');
    
    const summary = getEditedFieldsSummary();
    expect(summary).toHaveLength(3);
    
    const fields = summary.map((s: any) => s.field);
    expect(fields).toContain('title');
    expect(fields).toContain('business_context.business_problem');
    expect(fields).toContain('research_objectives.research_audience');
  });
});
