import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { PlusIcon, TrashIcon, CheckIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface MethodologyRule {
  description: string;
  required_questions: number;
  validation_rules: string[];
}

interface QualityRule {
  [category: string]: string[];
}

export const RulesPage: React.FC = () => {
  const [methodologies, setMethodologies] = useState<Record<string, MethodologyRule>>({});
  const [qualityRules, setQualityRules] = useState<QualityRule>({});
  const [customRules, setCustomRules] = useState<Array<{ id: string; type: string; rule: string; rule_id?: string }>>([]);
  const [newRule, setNewRule] = useState({ type: 'question_quality', rule: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/?view=golden-examples';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    }
    // For 'rules', we stay on the current page
  };

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

      setMethodologies(methodologiesData.rules || {});
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

      if (response.ok) {
        const result = await response.json();
        setCustomRules([...customRules, { ...newRule, id: result.rule_id, rule_id: result.rule_id }]);
        setNewRule({ type: 'question_quality', rule: '' });
        // Refresh quality rules to include the new custom rule
        fetchRules();
      }
    } catch (err) {
      console.error('Failed to add custom rule:', err);
    }
  };

  const removeCustomRule = async (ruleId: string) => {
    try {
      const response = await fetch(`/api/v1/rules/custom-rule/${ruleId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setCustomRules(customRules.filter(rule => rule.rule_id !== ruleId));
        // Refresh quality rules to remove the deleted custom rule
        fetchRules();
      }
    } catch (err) {
      console.error('Failed to remove custom rule:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 flex">
      {/* Sidebar */}
      <Sidebar currentView="rules" onViewChange={handleViewChange} />

      {/* Main Content */}
      <div className="flex-1 lg:ml-16 xl:ml-64 transition-all duration-300 ease-in-out">
        {/* Top Bar */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
          <div className="px-6 py-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Rules Management
                </h1>
                <p className="text-gray-600 mt-1">Configure survey generation rules and methodologies</p>
              </div>
            </div>
          </div>
        </header>

        <main className="py-6">
          <div className="px-6">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <div className="flex flex-col items-center space-y-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-200 border-t-purple-600"></div>
                  <p className="text-gray-600 text-lg">Loading rules...</p>
                </div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-red-800">Error loading rules</h3>
                    <p className="text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Methodologies */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div className="bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600 px-6 py-6 text-white">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold">Methodology Rules</h2>
                        <p className="text-blue-100 mt-1">Configure research methodologies and their applications</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid gap-6">
                      {Object.entries(methodologies).map(([key, rule], index) => (
                        <div key={key} className="group border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-blue-300 transition-all duration-300 bg-gradient-to-r from-white to-blue-50/30">
                          <div className="flex items-start space-x-4">
                            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-blue-200 transition-colors">
                              <span className="text-blue-600 font-semibold text-sm">{index + 1}</span>
                            </div>
                            <div className="flex-1">
                              <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-blue-900 transition-colors capitalize">{key.replace('_', ' ')}</h3>
                              <p className="text-gray-600 mb-4 leading-relaxed">{rule.description}</p>
                              <div className="flex items-center space-x-4 mb-4">
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                  </svg>
                                  {rule.required_questions} questions required
                                </span>
                              </div>
                              {rule.validation_rules && rule.validation_rules.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                                    <svg className="w-4 h-4 mr-2 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    Validation Rules
                                  </h4>
                                  <ul className="space-y-2">
                                    {rule.validation_rules.map((validation, idx) => (
                                      <li key={idx} className="text-sm text-gray-600 flex items-start group-hover:text-gray-700 transition-colors">
                                        <span className="w-2 h-2 bg-green-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                                        <span className="leading-relaxed">{validation}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Quality Rules */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div className="bg-gradient-to-r from-green-500 via-green-600 to-emerald-600 px-6 py-6 text-white">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold">Quality Rules</h2>
                        <p className="text-green-100 mt-1">Define quality standards and guidelines for surveys</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="grid gap-6">
                      {Object.entries(qualityRules).map(([key, rules], index) => (
                        <div key={key} className="group border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-green-300 transition-all duration-300 bg-gradient-to-r from-white to-green-50/30">
                          <div className="flex items-start space-x-4">
                            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-green-200 transition-colors">
                              <span className="text-green-600 font-semibold text-sm">{index + 1}</span>
                            </div>
                            <div className="flex-1">
                              <h3 className="text-xl font-semibold text-gray-900 mb-4 group-hover:text-green-900 transition-colors capitalize">{key.replace('_', ' ')}</h3>
                              {Array.isArray(rules) && rules.length > 0 && (
                                <ul className="space-y-2">
                                  {rules.map((rule, idx) => (
                                    <li key={idx} className="text-sm text-gray-600 flex items-start group-hover:text-gray-700 transition-colors">
                                      <span className="w-2 h-2 bg-green-400 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                                      <span className="leading-relaxed">{rule}</span>
                                    </li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Custom Rules */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div className="bg-gradient-to-r from-purple-500 via-purple-600 to-pink-600 px-6 py-6 text-white">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold">Custom Rules</h2>
                        <p className="text-purple-100 mt-1">Add your own custom rules and guidelines</p>
                      </div>
                    </div>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4 mb-8">
                      {customRules.map((rule) => (
                        <div key={rule.id} className="group border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-purple-300 transition-all duration-300 bg-gradient-to-r from-purple-50/50 to-pink-50/50">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-4 flex-1">
                              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-purple-200 transition-colors">
                                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              </div>
                              <div className="flex-1">
                                <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-purple-900 transition-colors capitalize">{rule.type.replace('_', ' ')}</h3>
                                <p className="text-gray-600 text-sm mb-3 leading-relaxed">{rule.rule}</p>
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 group-hover:bg-purple-200 transition-colors">
                                  Custom Rule
                                </span>
                              </div>
                            </div>
                            <button
                              onClick={() => removeCustomRule(rule.rule_id || rule.id)}
                              className="ml-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200 group-hover:bg-red-50"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>
                        </div>
                      ))}
                      {customRules.length === 0 && (
                        <div className="text-center py-12">
                          <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
                            <svg className="w-10 h-10 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                          </div>
                          <p className="text-gray-500 text-lg">No custom rules added yet</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-dashed border-purple-200 rounded-2xl p-6 hover:border-purple-300 transition-colors">
                      <div className="text-center mb-6">
                        <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                          <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Add New Custom Rule</h3>
                        <p className="text-gray-600">Create your own methodology or quality rules</p>
                      </div>
                      
                      <div className="flex space-x-4">
                        <select
                          value={newRule.type}
                          onChange={(e) => setNewRule({ ...newRule, type: e.target.value })}
                          className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                        >
                          <option value="question_quality">Question Quality</option>
                          <option value="survey_structure">Survey Structure</option>
                          <option value="methodology_compliance">Methodology Compliance</option>
                          <option value="respondent_experience">Respondent Experience</option>
                        </select>
                        <input
                          type="text"
                          value={newRule.rule}
                          onChange={(e) => setNewRule({ ...newRule, rule: e.target.value })}
                          placeholder="Enter custom rule..."
                          className="flex-2 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                        />
                        <button
                          onClick={addCustomRule}
                          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 flex items-center font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200"
                        >
                          <PlusIcon className="h-5 w-5 mr-2" />
                          Add Rule
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};