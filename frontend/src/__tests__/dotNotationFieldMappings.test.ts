/// <reference types="jest" />

import { useAppStore } from '../store/useAppStore';
import type { RFQFieldMapping } from '../types';

describe('Dot Notation Field Mappings', () => {
  it('should handle dot notation field names correctly', () => {
    const mappings: RFQFieldMapping[] = [
      { 
        field: 'business_context.company_product_background', 
        value: 'We are a tech company developing mobile apps', 
        confidence: 0.9, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      },
      { 
        field: 'stakeholder_requirements', 
        value: 'Marketing team needs customer insights', 
        confidence: 0.8, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      },
      { 
        field: 'research_objectives.success_metrics', 
        value: 'Net Promoter Score and feature adoption rate', 
        confidence: 0.7, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      }
    ];

    const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);

    // Check that dot notation fields are mapped correctly
    expect(rfqUpdates.business_context?.company_product_background).toBe('We are a tech company developing mobile apps');
    expect(rfqUpdates.business_context?.stakeholder_requirements).toBe('Marketing team needs customer insights');
    expect(rfqUpdates.research_objectives?.success_metrics).toBe('Net Promoter Score and feature adoption rate');
  });

  it('should handle mixed dot notation and direct field names', () => {
    const mappings: RFQFieldMapping[] = [
      { 
        field: 'title', 
        value: 'Test Research Project', 
        confidence: 0.9, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      },
      { 
        field: 'business_context.budget_range', 
        value: 'under 10k', 
        confidence: 0.8, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      },
      { 
        field: 'methodology.complexity_level', 
        value: 'simple', 
        confidence: 0.7, 
        source: '', 
        reasoning: '', 
        needs_review: false, 
        user_action: 'accepted' 
      }
    ];

    const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);

    // Check that both formats work
    expect(rfqUpdates.title).toBe('Test Research Project');
    expect(rfqUpdates.business_context?.budget_range).toBe('under_10k');
    expect(rfqUpdates.methodology?.complexity_level).toBe('simple');
  });
});
