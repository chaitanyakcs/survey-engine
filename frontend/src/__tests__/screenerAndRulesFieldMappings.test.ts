/// <reference types="jest" />

import { useAppStore } from '../store/useAppStore';
import type { RFQFieldMapping } from '../types';

describe('Screener and Rules Field Mappings', () => {
  it('should map screener_requirements field correctly', () => {
    const mappings: RFQFieldMapping[] = [
      { 
        field: 'survey_requirements.screener_requirements', 
        value: 'Screener and respondent tagging rules, piping logic for qualification', 
        confidence: 0.9, 
        source: 'Document section', 
        reasoning: 'Found screener requirements in document', 
        needs_review: false, 
        user_action: 'accepted' 
      }
    ];

    const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);

    expect(rfqUpdates.survey_requirements?.screener_requirements).toBe('Screener and respondent tagging rules, piping logic for qualification');
  });

  it('should map rules_and_definitions field correctly', () => {
    const mappings: RFQFieldMapping[] = [
      { 
        field: 'rules_and_definitions', 
        value: 'need more than 60 questions', 
        confidence: 0.8, 
        source: 'Document requirements', 
        reasoning: 'Found rules and definitions in document', 
        needs_review: false, 
        user_action: 'accepted' 
      }
    ];

    const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);

    expect(rfqUpdates.rules_and_definitions).toBe('need more than 60 questions');
  });

  it('should handle both fields together', () => {
    const mappings: RFQFieldMapping[] = [
      { 
        field: 'survey_requirements.screener_requirements', 
        value: 'Multi-stage qualification with demographic quotas', 
        confidence: 0.9, 
        source: 'Document', 
        reasoning: 'Found screener requirements', 
        needs_review: false, 
        user_action: 'accepted' 
      },
      { 
        field: 'rules_and_definitions', 
        value: 'Standard market research terminology applies', 
        confidence: 0.7, 
        source: 'Document', 
        reasoning: 'Found rules and definitions', 
        needs_review: false, 
        user_action: 'accepted' 
      }
    ];

    const rfqUpdates = useAppStore.getState().buildRFQUpdatesFromMappings(mappings);

    expect(rfqUpdates.survey_requirements?.screener_requirements).toBe('Multi-stage qualification with demographic quotas');
    expect(rfqUpdates.rules_and_definitions).toBe('Standard market research terminology applies');
  });
});
