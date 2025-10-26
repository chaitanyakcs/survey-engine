import React from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import PillarRulesManager from './PillarRulesManager';

interface PillarRulesSectionProps {
  expandedSections: {
    methodology: boolean;
    pillars: boolean;
    systemPrompt: boolean;
  };
  onToggleSection: (section: 'methodology' | 'pillars' | 'systemPrompt') => void;
  onShowDeleteConfirm: (config: {
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt' | 'pillar-rule';
    title: string;
    message: string;
    onConfirm: () => void;
  }) => void;
}

export const PillarRulesSection: React.FC<PillarRulesSectionProps> = ({
  expandedSections,
  onToggleSection,
  onShowDeleteConfirm
}) => {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
      <div 
        className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => onToggleSection('pillars')}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-2xl font-bold text-gray-900">5-Pillar Evaluation Rules</h2>
                <span className="px-2 py-1 bg-gray-200 text-gray-700 rounded-full text-xs font-medium">NEW</span>
              </div>
              <p className="text-gray-600 mt-1">Define how surveys are evaluated across 5 dimensions (content validity, methodology, respondent experience, analytical value, business impact). AI uses these criteria to self-assess survey quality.</p>
            </div>
          </div>
          <ChevronDownIcon 
            className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
              expandedSections.pillars ? 'rotate-180' : ''
            }`} 
          />
        </div>
      </div>
      {expandedSections.pillars && (
        <div className="p-6">
          <PillarRulesManager onShowDeleteConfirm={onShowDeleteConfirm} />
        </div>
      )}
    </div>
  );
};
