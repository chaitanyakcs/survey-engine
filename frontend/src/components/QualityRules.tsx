import React, { useState } from 'react';
import { PlusIcon, TrashIcon, CheckIcon, XMarkIcon, PencilIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '../store/useAppStore';

interface QualityRuleItem {
  id: string;
  text: string;
  created_at?: string;
  updated_at?: string;
}

interface QualityRule {
  [category: string]: QualityRuleItem[];
}

interface QualityRulesProps {
  qualityRules: QualityRule;
  onUpdateQualityRules: (qualityRules: QualityRule) => void;
  onFetchQualityRules: () => Promise<void>;
  saving: string | null;
  setSaving: (key: string | null) => void;
  onShowDeleteConfirm: (config: {
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt';
    title: string;
    message: string;
    onConfirm: () => void;
  }) => void;
}

export const QualityRules: React.FC<QualityRulesProps> = ({
  qualityRules,
  onUpdateQualityRules,
  onFetchQualityRules,
  saving,
  setSaving,
  onShowDeleteConfirm
}) => {
  const { addToast } = useAppStore();
  const [editingRule, setEditingRule] = useState<{category: string, ruleId: string} | null>(null);
  const [editingText, setEditingText] = useState('');
  const [addingRule, setAddingRule] = useState<{category: string} | null>(null);
  const [newRuleText, setNewRuleText] = useState('');

  const startEditRule = (category: string, ruleId: string, currentRule: string) => {
    setEditingRule({ category, ruleId });
    setEditingText(currentRule);
  };

  const cancelEditRule = () => {
    setEditingRule(null);
    setEditingText('');
  };

  const saveEditRule = async () => {
    if (!editingRule || !editingText.trim()) return;

    const saveKey = `${editingRule.category}-${editingRule.ruleId}`;
    setSaving(saveKey);

    try {
      const response = await fetch('/api/v1/rules/quality-rules', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rule_id: editingRule.ruleId,
          rule_text: editingText.trim()
        })
      });

      if (response.ok) {
        await onFetchQualityRules();
        setEditingRule(null);
        setEditingText('');
      } else {
        addToast({
          type: 'error',
          title: 'Update Failed',
          message: 'Failed to update quality rule',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to update quality rule:', error);
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to update quality rule',
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  const startAddRule = (category: string) => {
    setAddingRule({ category });
    setNewRuleText('');
  };

  const cancelAddRule = () => {
    setAddingRule(null);
    setNewRuleText('');
  };

  const saveAddRule = async () => {
    if (!addingRule || !newRuleText.trim()) return;

    const saveKey = `add-${addingRule.category}`;
    setSaving(saveKey);

    try {
      const response = await fetch('/api/v1/rules/quality-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: addingRule.category,
          rule_text: newRuleText.trim()
        })
      });

      if (response.ok) {
        await onFetchQualityRules();
        setAddingRule(null);
        setNewRuleText('');
      } else {
        addToast({
          type: 'error',
          title: 'Add Failed',
          message: 'Failed to add quality rule',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to add quality rule:', error);
      addToast({
        type: 'error',
        title: 'Add Failed',
        message: 'Failed to add quality rule',
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  const deleteRule = async (category: string, ruleId: string) => {
    onShowDeleteConfirm({
      show: true,
      type: 'rule',
      title: 'Delete Rule',
      message: 'Are you sure you want to delete this rule? This action cannot be undone.',
      onConfirm: async () => {
        await performRuleDeletion(category, ruleId);
      }
    });
  };

  const performRuleDeletion = async (category: string, ruleId: string) => {
    const saveKey = `delete-${category}-${ruleId}`;
    setSaving(saveKey);

    try {
      const response = await fetch('/api/v1/rules/quality-rules', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rule_id: ruleId
        })
      });

      if (response.ok) {
        await onFetchQualityRules();
        addToast({
          type: 'success',
          title: 'Rule Deleted',
          message: 'Quality rule has been deleted successfully',
          duration: 3000
        });
        // Close the delete confirmation popup
        onShowDeleteConfirm({
          show: false,
          type: 'rule',
          title: '',
          message: '',
          onConfirm: () => {}
        });
      } else {
        let errorMessage = 'Failed to delete quality rule';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('Failed to parse error response:', parseError);
        }
        
        addToast({
          type: 'error',
          title: 'Delete Failed',
          message: errorMessage,
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Network/Exception error during delete:', error);
      const errorMessage = error instanceof Error ? error.message : 'Network error occurred while deleting the rule';
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: errorMessage,
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="space-y-6">
      {Object.entries(qualityRules).map(([category, rules]) => (
        <div key={category} className="border border-gray-200 rounded-xl p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">
              {category.replace('_', ' ').toUpperCase()}
            </h3>
            <button
              onClick={() => startAddRule(category)}
              className="flex items-center space-x-2 px-3 py-1.5 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm"
            >
              <PlusIcon className="w-4 h-4" />
              <span>Add Rule</span>
            </button>
          </div>
          
          <div className="space-y-3">
            {rules.map((rule, index) => (
              <div key={rule.id || index} className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-amber-300 transition-colors">
                {editingRule?.category === category && editingRule?.ruleId === rule.id ? (
                  <div className="flex-1 flex items-center space-x-2">
                    <input
                      type="text"
                      value={editingText}
                      onChange={(e) => setEditingText(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                      autoFocus
                    />
                    <button
                      onClick={saveEditRule}
                      disabled={saving === `${category}-${rule.id}`}
                      className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {saving === `${category}-${rule.id}` ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                      ) : (
                        <CheckIcon className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={cancelEditRule}
                      className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 text-gray-700">{rule.text}</div>
                    <button
                      onClick={() => startEditRule(category, rule.id, rule.text)}
                      className="p-2 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteRule(category, rule.id)}
                      disabled={saving === `delete-${category}-${rule.id}`}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                    >
                      {saving === `delete-${category}-${rule.id}` ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                      ) : (
                        <TrashIcon className="w-4 h-4" />
                      )}
                    </button>
                  </>
                )}
              </div>
            ))}
            
            {addingRule?.category === category && (
              <div className="flex items-center space-x-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
                <input
                  type="text"
                  value={newRuleText}
                  onChange={(e) => setNewRuleText(e.target.value)}
                  placeholder="Enter new rule..."
                  className="flex-1 px-3 py-2 border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  autoFocus
                />
                <button
                  onClick={saveAddRule}
                  disabled={saving === `add-${category}` || !newRuleText.trim()}
                  className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                >
                  {saving === `add-${category}` ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                  ) : (
                    <CheckIcon className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={cancelAddRule}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
