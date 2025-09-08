import React, { useState, useEffect } from 'react';
import { PlusIcon, TrashIcon, CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface MethodologyRule {
  description: string;
  required_questions: number;
  validation_rules: string[];
}

interface QualityRule {
  [category: string]: string[];
}

interface RulesManagerProps {
  onClose: () => void;
}

export const RulesManager: React.FC<RulesManagerProps> = ({ onClose }) => {
  const [methodologies, setMethodologies] = useState<Record<string, MethodologyRule>>({});
  const [qualityRules, setQualityRules] = useState<QualityRule>({});
  const [customRules, setCustomRules] = useState<Array<{ id: string; type: string; rule: string; rule_id?: string }>>([]);
  const [newRule, setNewRule] = useState({ type: 'question_quality', rule: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const [methodologiesRes, qualityRes] = await Promise.all([
        fetch('/api/v1/rules/methodologies'),
        fetch('/api/v1/rules/quality-rules')
      ]);

      if (!methodologiesRes.ok || !qualityRes.ok) {
        throw new Error('Failed to fetch rules');
      }

      const methodologiesData = await methodologiesRes.json();
      const qualityData = await qualityRes.json();

      setMethodologies(methodologiesData.rules);
      setQualityRules(qualityData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch rules');
    } finally {
      setLoading(false);
    }
  };

  const addCustomRule = async () => {
    if (!newRule.rule.trim()) return;

    try {
      const response = await fetch('/api/v1/rules/custom-rule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRule)
      });

      if (!response.ok) {
        throw new Error('Failed to add custom rule');
      }

      const result = await response.json();
      setCustomRules(prev => [...prev, { 
        id: Date.now().toString(), 
        rule_id: result.rule_id,
        type: newRule.type, 
        rule: newRule.rule 
      }]);
      setNewRule({ type: 'question_quality', rule: '' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add rule');
    }
  };

  const removeCustomRule = async (id: string, rule_id?: string) => {
    try {
      if (rule_id) {
        // Delete from database
        const response = await fetch(`/api/v1/rules/custom-rule/${rule_id}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error('Failed to delete custom rule');
        }
      }
      
      // Remove from local state
      setCustomRules(prev => prev.filter(rule => rule.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Survey Generation Rules</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Methodology Rules */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Methodology Rules</h3>
            <div className="space-y-3">
              {Object.entries(methodologies).map(([name, rule]) => (
                <div key={name} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 capitalize">{name.replace('_', ' ')}</h4>
                  <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                  <div className="mt-2">
                    <span className="text-xs font-medium text-gray-500">Required Questions:</span>
                    <span className="ml-2 text-sm text-gray-700">{rule.required_questions}</span>
                  </div>
                  <div className="mt-2">
                    <span className="text-xs font-medium text-gray-500">Validation Rules:</span>
                    <ul className="mt-1 text-xs text-gray-600">
                      {rule.validation_rules.map((validation, idx) => (
                        <li key={idx} className="flex items-start">
                          <CheckIcon className="h-3 w-3 text-green-500 mt-0.5 mr-1 flex-shrink-0" />
                          {validation}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quality Rules */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Quality Rules</h3>
            <div className="space-y-3">
              {Object.entries(qualityRules).map(([category, rules]) => (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 capitalize">
                    {category.replace('_', ' ')}
                  </h4>
                  <ul className="mt-2 space-y-1">
                    {rules.map((rule, idx) => (
                      <li key={idx} className="flex items-start text-sm text-gray-600">
                        <CheckIcon className="h-3 w-3 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                        {rule}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Custom Rules */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Custom Rules</h3>
          
          {/* Add New Rule */}
          <div className="flex gap-2 mb-4">
            <select
              value={newRule.type}
              onChange={(e) => setNewRule(prev => ({ ...prev, type: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="question_quality">Question Quality</option>
              <option value="survey_structure">Survey Structure</option>
              <option value="methodology_compliance">Methodology Compliance</option>
              <option value="respondent_experience">Respondent Experience</option>
            </select>
            <input
              type="text"
              value={newRule.rule}
              onChange={(e) => setNewRule(prev => ({ ...prev, rule: e.target.value }))}
              placeholder="Enter custom rule..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
            <button
              onClick={addCustomRule}
              disabled={!newRule.rule.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              Add
            </button>
          </div>

          {/* Custom Rules List */}
          <div className="space-y-2">
            {customRules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="text-xs font-medium text-gray-500 uppercase">
                    {rule.type.replace('_', ' ')}
                  </span>
                  <p className="text-sm text-gray-700 mt-1">{rule.rule}</p>
                </div>
                <button
                  onClick={() => removeCustomRule(rule.id, rule.rule_id)}
                  className="text-red-400 hover:text-red-600"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            Close
          </button>
          <button
            onClick={fetchRules}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Refresh Rules
          </button>
        </div>
      </div>
    </div>
  );
};
