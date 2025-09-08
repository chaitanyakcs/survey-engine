import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { XMarkIcon, TrashIcon } from '@heroicons/react/24/outline';

interface MethodologyRule {
  name: string;
  description: string;
  use_cases: string[];
  best_practices: string[];
}

interface QualityRule {
  [key: string]: {
    description: string;
    guidelines: string[];
  };
}

export const RulesPage: React.FC = () => {
  const [methodologies, setMethodologies] = useState<Record<string, MethodologyRule>>({});
  const [qualityRules, setQualityRules] = useState<QualityRule>({});
  const [customRules, setCustomRules] = useState<Array<{ id: string; type: string; rule: string; rule_id?: string }>>([]);
  const [newRule, setNewRule] = useState({ type: 'question_quality', rule: '' });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setIsLoading(true);
      
      // Fetch methodologies
      const methodologiesResponse = await fetch('/api/v1/rules/methodologies');
      if (methodologiesResponse.ok) {
        const methodologiesData = await methodologiesResponse.json();
        setMethodologies(methodologiesData);
      }

      // Fetch quality rules
      const qualityResponse = await fetch('/api/v1/rules/quality-rules');
      if (qualityResponse.ok) {
        const qualityData = await qualityResponse.json();
        setQualityRules(qualityData);
        
        // Extract custom rules from quality rules
        const custom = Object.entries(qualityData)
          .filter(([key, rule]: [string, any]) => rule.is_custom)
          .map(([key, rule]: [string, any]) => ({
            id: Date.now().toString() + Math.random(),
            type: key,
            rule: rule.description,
            rule_id: rule.id
          }));
        setCustomRules(custom);
      }
    } catch (error) {
      console.error('Failed to fetch rules:', error);
    } finally {
      setIsLoading(false);
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

      if (response.ok) {
        const result = await response.json();
        setCustomRules(prev => [...prev, { 
          id: Date.now().toString(), 
          rule_id: result.rule_id,
          type: newRule.type, 
          rule: newRule.rule 
        }]);
        setNewRule({ type: 'question_quality', rule: '' });
        await fetchRules(); // Refresh all rules
      }
    } catch (error) {
      console.error('Failed to add custom rule:', error);
    }
  };

  const removeCustomRule = async (id: string, rule_id?: string) => {
    try {
      if (rule_id) {
        const response = await fetch(`/api/v1/rules/custom-rule/${rule_id}`, {
          method: 'DELETE'
        });
        if (!response.ok) {
          throw new Error('Failed to delete custom rule');
        }
      }
      setCustomRules(prev => prev.filter(rule => rule.id !== id));
      await fetchRules(); // Refresh all rules
    } catch (error) {
      console.error('Failed to remove custom rule:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Rules Management</h1>
              <p className="mt-2 text-gray-600">Configure survey generation rules and methodologies</p>
            </div>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <XMarkIcon className="h-4 w-4 mr-2" />
              Back
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Methodologies */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Methodology Rules</h2>
            <div className="space-y-4">
              {Object.entries(methodologies).map(([key, rule]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">{rule.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                  <div className="mt-2">
                    <h4 className="text-sm font-medium text-gray-700">Use Cases:</h4>
                    <ul className="text-sm text-gray-600 list-disc list-inside">
                      {rule.use_cases.map((useCase, index) => (
                        <li key={index}>{useCase}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quality Rules */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quality Rules</h2>
            <div className="space-y-4">
              {Object.entries(qualityRules).map(([key, rule]) => (
                <div key={key} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 capitalize">{key.replace('_', ' ')}</h3>
                  <p className="text-sm text-gray-600 mt-1">{rule.description}</p>
                  <div className="mt-2">
                    <h4 className="text-sm font-medium text-gray-700">Guidelines:</h4>
                    <ul className="text-sm text-gray-600 list-disc list-inside">
                      {rule.guidelines.map((guideline, index) => (
                        <li key={index}>{guideline}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Custom Rules */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Custom Rules</h2>
          
          {/* Add New Rule */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Add Custom Rule</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rule Type</label>
                <select
                  value={newRule.type}
                  onChange={(e) => setNewRule(prev => ({ ...prev, type: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                >
                  <option value="question_quality">Question Quality</option>
                  <option value="survey_structure">Survey Structure</option>
                  <option value="response_options">Response Options</option>
                  <option value="industry_specific">Industry Specific</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rule Description</label>
                <textarea
                  value={newRule.rule}
                  onChange={(e) => setNewRule(prev => ({ ...prev, rule: e.target.value }))}
                  placeholder="Enter your custom rule..."
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  rows={3}
                />
              </div>
              <button
                onClick={addCustomRule}
                disabled={!newRule.rule.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Add Rule
              </button>
            </div>
          </div>

          {/* Custom Rules List */}
          <div className="space-y-2">
            {customRules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 capitalize">
                    {rule.type.replace('_', ' ')}
                  </div>
                  <div className="text-sm text-gray-600">{rule.rule}</div>
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
      </div>
    </div>
  );
};
