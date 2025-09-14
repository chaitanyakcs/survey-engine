import React, { useState, useEffect } from 'react';
import { PlusIcon, TrashIcon, CheckIcon, XMarkIcon, PencilIcon } from '@heroicons/react/24/outline';

interface PillarRule {
  id: string;
  rule_name: string;
  rule_description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  rule_content: {
    evaluation_criteria: string[];
    migrated_from?: string;
    priority?: string;
  };
}

interface PillarRules {
  [pillar: string]: PillarRule[];
}

const PILLAR_INFO = {
  content_validity: {
    name: 'Content Validity',
    description: 'Ensures survey questions directly address research objectives',
    weight: '20%',
    color: 'from-blue-500 to-blue-600'
  },
  methodological_rigor: {
    name: 'Methodological Rigor',
    description: 'Validates adherence to research best practices and bias avoidance',
    weight: '25%',
    color: 'from-emerald-500 to-emerald-600'
  },
  clarity_comprehensibility: {
    name: 'Clarity & Comprehensibility',
    description: 'Ensures clear, understandable language for target audience',
    weight: '25%',
    color: 'from-amber-500 to-amber-600'
  },
  structural_coherence: {
    name: 'Structural Coherence',
    description: 'Validates logical flow and organization of survey elements',
    weight: '20%',
    color: 'from-purple-500 to-purple-600'
  },
  deployment_readiness: {
    name: 'Deployment Readiness',
    description: 'Assesses survey feasibility and implementation requirements',
    weight: '10%',
    color: 'from-pink-500 to-pink-600'
  }
};

const PRIORITY_COLORS = {
  critical: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', indicator: '🔴' },
  high: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300', indicator: '🟡' },
  medium: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300', indicator: '🔵' },
  low: { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-300', indicator: '⚪' }
};

const PillarRulesManager: React.FC = () => {
  const [pillarRules, setPillarRules] = useState<PillarRules>({});
  const [loading, setLoading] = useState(true);
  const [selectedPillar, setSelectedPillar] = useState<string>('content_validity');
  const [editingRule, setEditingRule] = useState<string | null>(null);
  const [editingData, setEditingData] = useState<Partial<PillarRule> | null>(null);
  const [addingRule, setAddingRule] = useState<string | null>(null);
  const [newRuleData, setNewRuleData] = useState<Partial<PillarRule>>({
    rule_name: '',
    rule_description: '',
    priority: 'medium',
    rule_content: { evaluation_criteria: [] }
  });

  useEffect(() => {
    fetchPillarRules();
  }, []);

  const fetchPillarRules = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/rules/pillar-rules');
      if (response.ok) {
        const data = await response.json();
        console.log('Pillar rules API response:', data);
        
        // Transform API response to match component expectations
        const transformedRules: PillarRules = {};
        if (data.pillar_rules) {
          Object.keys(data.pillar_rules).forEach(pillar => {
            transformedRules[pillar] = data.pillar_rules[pillar].rules.map((rule: any) => ({
              id: rule.id,
              rule_name: rule.rule_text || 'Untitled Rule',
              rule_description: rule.rule_text || '',
              priority: rule.priority || 'medium',
              rule_content: {
                evaluation_criteria: [],
                migrated_from: rule.created_by,
                priority: rule.priority
              }
            }));
          });
        }
        
        console.log('Transformed pillar rules:', transformedRules);
        setPillarRules(transformedRules);
      } else {
        console.error('Failed to fetch pillar rules:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch pillar rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const startEditRule = (rule: PillarRule) => {
    setEditingRule(rule.id);
    setEditingData({
      ...rule,
      rule_content: {
        ...rule.rule_content,
        evaluation_criteria: [...(rule.rule_content.evaluation_criteria || [])]
      }
    });
  };

  const cancelEdit = () => {
    setEditingRule(null);
    setEditingData(null);
  };

  const saveEditRule = async () => {
    if (!editingRule || !editingData) return;

    try {
      const response = await fetch(`/api/v1/rules/pillar-rules/${editingRule}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingData)
      });

      if (response.ok) {
        await fetchPillarRules();
        setEditingRule(null);
        setEditingData(null);
      }
    } catch (error) {
      console.error('Failed to update pillar rule:', error);
    }
  };

  const deleteRule = async (ruleId: string) => {
    if (!window.confirm('Are you sure you want to delete this rule?')) return;

    try {
      const response = await fetch(`/api/v1/rules/pillar-rules/${ruleId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await fetchPillarRules();
      }
    } catch (error) {
      console.error('Failed to delete pillar rule:', error);
    }
  };

  const startAddRule = (pillar: string) => {
    setAddingRule(pillar);
    setNewRuleData({
      rule_name: '',
      rule_description: '',
      priority: 'medium',
      rule_content: { evaluation_criteria: [] }
    });
  };

  const cancelAddRule = () => {
    setAddingRule(null);
    setNewRuleData({
      rule_name: '',
      rule_description: '',
      priority: 'medium',
      rule_content: { evaluation_criteria: [] }
    });
  };

  const saveAddRule = async () => {
    if (!addingRule || !newRuleData.rule_name?.trim() || !newRuleData.rule_description?.trim()) {
      return;
    }

    try {
      const response = await fetch('/api/v1/rules/pillar-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newRuleData,
          category: addingRule,
          rule_type: 'pillar'
        })
      });

      if (response.ok) {
        await fetchPillarRules();
        cancelAddRule();
      }
    } catch (error) {
      console.error('Failed to add pillar rule:', error);
    }
  };

  const addCriterion = (type: 'editing' | 'adding') => {
    if (type === 'editing' && editingData) {
      setEditingData({
        ...editingData,
        rule_content: {
          ...editingData.rule_content!,
          evaluation_criteria: [...(editingData.rule_content?.evaluation_criteria || []), '']
        }
      });
    } else if (type === 'adding') {
      setNewRuleData({
        ...newRuleData,
        rule_content: {
          ...newRuleData.rule_content!,
          evaluation_criteria: [...(newRuleData.rule_content?.evaluation_criteria || []), '']
        }
      });
    }
  };

  const removeCriterion = (index: number, type: 'editing' | 'adding') => {
    if (type === 'editing' && editingData) {
      const criteria = editingData.rule_content?.evaluation_criteria?.filter((_, i) => i !== index) || [];
      setEditingData({
        ...editingData,
        rule_content: {
          ...editingData.rule_content!,
          evaluation_criteria: criteria
        }
      });
    } else if (type === 'adding') {
      const criteria = newRuleData.rule_content?.evaluation_criteria?.filter((_, i) => i !== index) || [];
      setNewRuleData({
        ...newRuleData,
        rule_content: {
          ...newRuleData.rule_content!,
          evaluation_criteria: criteria
        }
      });
    }
  };

  const updateCriterion = (index: number, value: string, type: 'editing' | 'adding') => {
    if (type === 'editing' && editingData) {
      const criteria = [...(editingData.rule_content?.evaluation_criteria || [])];
      criteria[index] = value;
      setEditingData({
        ...editingData,
        rule_content: {
          ...editingData.rule_content!,
          evaluation_criteria: criteria
        }
      });
    } else if (type === 'adding') {
      const criteria = [...(newRuleData.rule_content?.evaluation_criteria || [])];
      criteria[index] = value;
      setNewRuleData({
        ...newRuleData,
        rule_content: {
          ...newRuleData.rule_content!,
          evaluation_criteria: criteria
        }
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-900 mb-2">5-Pillar Evaluation Rules</h3>
        <p className="text-gray-600">Customize evaluation criteria for each pillar of the survey assessment framework</p>
      </div>

      {/* Pillar Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
        {Object.entries(PILLAR_INFO).map(([pillar, info]) => (
          <button
            key={pillar}
            onClick={() => setSelectedPillar(pillar)}
            className={`p-4 rounded-xl border transition-all duration-200 text-left ${
              selectedPillar === pillar
                ? 'border-purple-300 bg-gradient-to-br from-purple-50 to-purple-100 shadow-md'
                : 'border-gray-200 bg-white hover:border-purple-200 hover:shadow-sm'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${info.color} mb-2`}></div>
            <h4 className="font-medium text-gray-900 text-sm mb-1">{info.name}</h4>
            <p className="text-xs text-gray-600 mb-2">{info.description}</p>
            <span className="text-xs font-medium text-purple-600">{info.weight}</span>
          </button>
        ))}
      </div>

      {/* Selected Pillar Rules */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className={`bg-gradient-to-r ${PILLAR_INFO[selectedPillar as keyof typeof PILLAR_INFO].color} px-6 py-4 text-white`}>
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-lg font-bold">{PILLAR_INFO[selectedPillar as keyof typeof PILLAR_INFO].name}</h4>
              <p className="text-white/90 text-sm">{PILLAR_INFO[selectedPillar as keyof typeof PILLAR_INFO].description}</p>
            </div>
            <button
              onClick={() => startAddRule(selectedPillar)}
              className="flex items-center space-x-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
              <span>Add Rule</span>
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            {pillarRules[selectedPillar]?.map((rule) => (
              <div key={rule.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
                {editingRule === rule.id ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h5 className="font-medium text-gray-900">Edit Rule</h5>
                      <div className="flex space-x-2">
                        <button
                          onClick={saveEditRule}
                          className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors"
                        >
                          <CheckIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name</label>
                        <input
                          type="text"
                          value={editingData?.rule_name || ''}
                          onChange={(e) => setEditingData(prev => prev ? {...prev, rule_name: e.target.value} : null)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                        <select
                          value={editingData?.priority || 'medium'}
                          onChange={(e) => setEditingData(prev => prev ? {...prev, priority: e.target.value as any} : null)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        >
                          <option value="critical">Critical</option>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </div>

                      <div className="lg:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={editingData?.rule_description || ''}
                          onChange={(e) => setEditingData(prev => prev ? {...prev, rule_description: e.target.value} : null)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                          rows={2}
                        />
                      </div>

                      <div className="lg:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation Criteria</label>
                        <div className="space-y-2">
                          {(editingData?.rule_content?.evaluation_criteria || []).map((criterion, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <input
                                type="text"
                                value={criterion}
                                onChange={(e) => updateCriterion(index, e.target.value, 'editing')}
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                placeholder="Enter evaluation criterion..."
                              />
                              <button
                                onClick={() => removeCriterion(index, 'editing')}
                                className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                              >
                                <XMarkIcon className="w-4 h-4" />
                              </button>
                            </div>
                          ))}
                          <button
                            onClick={() => addCriterion('editing')}
                            className="flex items-center space-x-2 px-3 py-2 text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors text-sm"
                          >
                            <PlusIcon className="w-4 h-4" />
                            <span>Add Criterion</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h5 className="font-medium text-gray-900">{rule.rule_name}</h5>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIORITY_COLORS[rule.priority].bg} ${PRIORITY_COLORS[rule.priority].text} ${PRIORITY_COLORS[rule.priority].border} border`}>
                            {PRIORITY_COLORS[rule.priority].indicator} {rule.priority.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm mb-3">{rule.rule_description}</p>
                        {rule.rule_content.evaluation_criteria && rule.rule_content.evaluation_criteria.length > 0 && (
                          <div>
                            <h6 className="text-xs font-medium text-gray-700 mb-1">Evaluation Criteria:</h6>
                            <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                              {rule.rule_content.evaluation_criteria.map((criterion, index) => (
                                <li key={index}>{criterion}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={() => startEditRule(rule)}
                          className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deleteRule(rule.id)}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )) || (
              <div className="text-center py-8 text-gray-500">
                <p className="text-lg font-medium">No rules defined yet</p>
                <p className="text-sm mb-4">Add your first evaluation rule for this pillar</p>
                <button
                  onClick={() => startAddRule(selectedPillar)}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  Add Rule
                </button>
              </div>
            )}

            {addingRule === selectedPillar && (
              <div className="border-2 border-dashed border-purple-300 rounded-lg p-4 bg-purple-50">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h5 className="font-medium text-gray-900">Add New Rule</h5>
                    <div className="flex space-x-2">
                      <button
                        onClick={saveAddRule}
                        disabled={!newRuleData.rule_name?.trim() || !newRuleData.rule_description?.trim()}
                        className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <CheckIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={cancelAddRule}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Rule Name</label>
                      <input
                        type="text"
                        value={newRuleData.rule_name || ''}
                        onChange={(e) => setNewRuleData(prev => ({...prev, rule_name: e.target.value}))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="Enter rule name..."
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                      <select
                        value={newRuleData.priority || 'medium'}
                        onChange={(e) => setNewRuleData(prev => ({...prev, priority: e.target.value as any}))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>

                    <div className="lg:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                      <textarea
                        value={newRuleData.rule_description || ''}
                        onChange={(e) => setNewRuleData(prev => ({...prev, rule_description: e.target.value}))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        rows={2}
                        placeholder="Enter rule description..."
                      />
                    </div>

                    <div className="lg:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation Criteria</label>
                      <div className="space-y-2">
                        {(newRuleData.rule_content?.evaluation_criteria || []).map((criterion, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={criterion}
                              onChange={(e) => updateCriterion(index, e.target.value, 'adding')}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                              placeholder="Enter evaluation criterion..."
                            />
                            <button
                              onClick={() => removeCriterion(index, 'adding')}
                              className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                            >
                              <XMarkIcon className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => addCriterion('adding')}
                          className="flex items-center space-x-2 px-3 py-2 text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors text-sm"
                        >
                          <PlusIcon className="w-4 h-4" />
                          <span>Add Criterion</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PillarRulesManager;