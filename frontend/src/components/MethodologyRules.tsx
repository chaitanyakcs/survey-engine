import React, { useState } from 'react';
import { PlusIcon, TrashIcon, PencilIcon, XMarkIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '../store/useAppStore';

interface MethodologyRule {
  description: string;
  required_questions: number;
  validation_rules: string[];
  question_flow?: string[];
  best_practices?: string[];
}

interface MethodologyRulesProps {
  methodologies: Record<string, MethodologyRule>;
  onUpdateMethodologies: (methodologies: Record<string, MethodologyRule>) => void;
  onFetchRules: () => Promise<void>;
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

export const MethodologyRules: React.FC<MethodologyRulesProps> = ({
  methodologies,
  onUpdateMethodologies,
  onFetchRules,
  saving,
  setSaving,
  onShowDeleteConfirm
}) => {
  const { addToast } = useAppStore();
  const [editingMethodology, setEditingMethodology] = useState<string | null>(null);
  const [editingMethodologyData, setEditingMethodologyData] = useState<MethodologyRule | null>(null);
  const [addingMethodology, setAddingMethodology] = useState(false);
  const [newMethodologyData, setNewMethodologyData] = useState<MethodologyRule>({
    description: '',
    required_questions: 0,
    validation_rules: [],
    question_flow: [],
    best_practices: []
  });

  const startEditMethodology = (methodologyName: string) => {
    const methodology = methodologies[methodologyName];
    if (methodology) {
      setEditingMethodology(methodologyName);
      setEditingMethodologyData({ ...methodology });
    }
  };

  const cancelEditMethodology = () => {
    setEditingMethodology(null);
    setEditingMethodologyData(null);
  };

  const saveEditMethodology = async () => {
    if (!editingMethodology || !editingMethodologyData) return;

    const saveKey = `edit-methodology-${editingMethodology}`;
    setSaving(saveKey);

    try {
      const response = await fetch('/api/v1/rules/methodology-rules', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          methodology_name: editingMethodology,
          description: editingMethodologyData.description,
          required_questions: editingMethodologyData.required_questions,
          validation_rules: editingMethodologyData.validation_rules,
          question_flow: editingMethodologyData.question_flow,
          best_practices: editingMethodologyData.best_practices
        })
      });

      if (response.ok) {
        const updatedMethodologies = { ...methodologies };
        updatedMethodologies[editingMethodology] = editingMethodologyData;
        onUpdateMethodologies(updatedMethodologies);
        setEditingMethodology(null);
        setEditingMethodologyData(null);
        addToast({
          type: 'success',
          title: 'Methodology Updated',
          message: `Methodology '${editingMethodology}' has been updated successfully.`,
          duration: 3000
        });
      } else {
        const errorData = await response.json();
        addToast({
          type: 'error',
          title: 'Update Failed',
          message: errorData.detail || 'Failed to update methodology rule',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to update methodology:', error);
      addToast({
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to update methodology rule',
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  const deleteMethodology = async (methodologyName: string) => {
    onShowDeleteConfirm({
      show: true,
      type: 'methodology',
      title: 'Delete Methodology',
      message: `Are you sure you want to delete the '${methodologyName}' methodology? This action cannot be undone.`,
      onConfirm: async () => {
        await performMethodologyDeletion(methodologyName);
      }
    });
  };

  const performMethodologyDeletion = async (methodologyName: string) => {
    const saveKey = `delete-methodology-${methodologyName}`;
    setSaving(saveKey);

    try {
      const response = await fetch(`/api/v1/rules/methodology-rules/${methodologyName}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        const updatedMethodologies = { ...methodologies };
        delete updatedMethodologies[methodologyName];
        onUpdateMethodologies(updatedMethodologies);
        addToast({
          type: 'success',
          title: 'Methodology Deleted',
          message: `Methodology '${methodologyName}' has been deleted successfully.`,
          duration: 3000
        });
        // Close the delete confirmation popup
        onShowDeleteConfirm({
          show: false,
          type: 'methodology',
          title: '',
          message: '',
          onConfirm: () => {}
        });
      } else {
        const errorData = await response.json();
        addToast({
          type: 'error',
          title: 'Delete Failed',
          message: errorData.detail || 'Failed to delete methodology rule',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to delete methodology:', error);
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: 'Failed to delete methodology rule',
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  const startAddMethodology = () => {
    setAddingMethodology(true);
    setNewMethodologyData({
      description: '',
      required_questions: 0,
      validation_rules: [],
      question_flow: [],
      best_practices: []
    });
  };

  const cancelAddMethodology = () => {
    setAddingMethodology(false);
    setNewMethodologyData({
      description: '',
      required_questions: 0,
      validation_rules: [],
      question_flow: [],
      best_practices: []
    });
  };

  const saveAddMethodology = async () => {
    if (!newMethodologyData.description.trim()) {
      addToast({
        type: 'error',
        title: 'Validation Error',
        message: 'Methodology name and description are required',
        duration: 5000
      });
      return;
    }

    const saveKey = 'add-methodology';
    setSaving(saveKey);

    try {
      const response = await fetch('/api/v1/rules/methodology-rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          methodology_name: newMethodologyData.description.toLowerCase().replace(/\s+/g, '_'),
          description: newMethodologyData.description,
          required_questions: newMethodologyData.required_questions,
          validation_rules: newMethodologyData.validation_rules,
          question_flow: newMethodologyData.question_flow,
          best_practices: newMethodologyData.best_practices
        })
      });

      if (response.ok) {
        const result = await response.json();
        const updatedMethodologies = { ...methodologies };
        updatedMethodologies[result.methodology_name] = newMethodologyData;
        onUpdateMethodologies(updatedMethodologies);
        setAddingMethodology(false);
        setNewMethodologyData({
          description: '',
          required_questions: 0,
          validation_rules: [],
          question_flow: [],
          best_practices: []
        });
        addToast({
          type: 'success',
          title: 'Methodology Added',
          message: `Methodology '${result.methodology_name}' has been added successfully.`,
          duration: 3000
        });
      } else {
        const errorData = await response.json();
        addToast({
          type: 'error',
          title: 'Add Failed',
          message: errorData.detail || 'Failed to add methodology rule',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to add methodology:', error);
      addToast({
        type: 'error',
        title: 'Add Failed',
        message: 'Failed to add methodology rule',
        duration: 5000
      });
    } finally {
      setSaving(null);
    }
  };

  const addValidationRule = (type: 'editing' | 'adding') => {
    if (type === 'editing' && editingMethodologyData) {
      setEditingMethodologyData({
        ...editingMethodologyData,
        validation_rules: [...editingMethodologyData.validation_rules, '']
      });
    } else if (type === 'adding') {
      setNewMethodologyData({
        ...newMethodologyData,
        validation_rules: [...newMethodologyData.validation_rules, '']
      });
    }
  };

  const removeValidationRule = (index: number, type: 'editing' | 'adding') => {
    if (type === 'editing' && editingMethodologyData) {
      const newRules = editingMethodologyData.validation_rules.filter((_, i) => i !== index);
      setEditingMethodologyData({
        ...editingMethodologyData,
        validation_rules: newRules
      });
    } else if (type === 'adding') {
      const newRules = newMethodologyData.validation_rules.filter((_, i) => i !== index);
      setNewMethodologyData({
        ...newMethodologyData,
        validation_rules: newRules
      });
    }
  };

  const updateValidationRule = (index: number, value: string, type: 'editing' | 'adding') => {
    if (type === 'editing' && editingMethodologyData) {
      const newRules = [...editingMethodologyData.validation_rules];
      newRules[index] = value;
      setEditingMethodologyData({
        ...editingMethodologyData,
        validation_rules: newRules
      });
    } else if (type === 'adding') {
      const newRules = [...newMethodologyData.validation_rules];
      newRules[index] = value;
      setNewMethodologyData({
        ...newMethodologyData,
        validation_rules: newRules
      });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {Object.entries(methodologies).map(([name, rule]) => (
        <div key={name} className="border border-gray-200 rounded-xl p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
          {editingMethodology === name ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800">Edit {name.replace('_', ' ').toUpperCase()}</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={saveEditMethodology}
                    disabled={saving === `edit-methodology-${name}`}
                    className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
                  >
                    {saving === `edit-methodology-${name}` ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      'Save'
                    )}
                  </button>
                  <button
                    onClick={cancelEditMethodology}
                    className="px-3 py-1 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="lg:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={editingMethodologyData?.description || ''}
                    onChange={(e) => setEditingMethodologyData(prev => prev ? {...prev, description: e.target.value} : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    rows={2}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Required Questions</label>
                  <input
                    type="number"
                    value={editingMethodologyData?.required_questions || 0}
                    onChange={(e) => setEditingMethodologyData(prev => prev ? {...prev, required_questions: parseInt(e.target.value) || 0} : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    min="0"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Validation Rules</label>
                  <div className="space-y-2">
                    {(editingMethodologyData?.validation_rules || []).map((rule, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={rule}
                          onChange={(e) => updateValidationRule(index, e.target.value, 'editing')}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                          placeholder="Enter validation rule..."
                        />
                        <button
                          onClick={() => removeValidationRule(index, 'editing')}
                          className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() => addValidationRule('editing')}
                      className="flex items-center space-x-2 px-3 py-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors text-sm"
                    >
                      <PlusIcon className="w-4 h-4" />
                      <span>Add Rule</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-800">{name.replace('_', ' ').toUpperCase()}</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => startEditMethodology(name)}
                    className="p-2 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteMethodology(name)}
                    disabled={saving === `delete-methodology-${name}`}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {saving === `delete-methodology-${name}` ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
                    ) : (
                      <TrashIcon className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
              <p className="text-gray-600 mb-3">{rule.description}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Required Questions:</span>
                  <span className="ml-2 text-gray-600">{rule.required_questions}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Validation Rules:</span>
                  <span className="ml-2 text-gray-600">{rule.validation_rules.length} rules</span>
                </div>
              </div>
              {rule.validation_rules.length > 0 && (
                <div className="mt-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Validation Rules:</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                    {rule.validation_rules.map((validationRule, index) => (
                      <li key={index}>{validationRule}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      
      {addingMethodology && (
        <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Add New Methodology</h3>
            <div className="flex space-x-2">
              <button
                onClick={saveAddMethodology}
                disabled={saving === 'add-methodology'}
                className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
              >
                {saving === 'add-methodology' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  'Save'
                )}
              </button>
              <button
                onClick={cancelAddMethodology}
                className="px-3 py-1 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={newMethodologyData.description}
                onChange={(e) => setNewMethodologyData(prev => ({...prev, description: e.target.value}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                rows={2}
                placeholder="Enter methodology description..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Required Questions</label>
              <input
                type="number"
                value={newMethodologyData.required_questions}
                onChange={(e) => setNewMethodologyData(prev => ({...prev, required_questions: parseInt(e.target.value) || 0}))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                min="0"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Validation Rules</label>
              <div className="space-y-2">
                {newMethodologyData.validation_rules.map((rule, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={rule}
                      onChange={(e) => updateValidationRule(index, e.target.value, 'adding')}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      placeholder="Enter validation rule..."
                    />
                    <button
                      onClick={() => removeValidationRule(index, 'adding')}
                      className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </div>
                ))}
                <button
                  onClick={() => addValidationRule('adding')}
                  className="flex items-center space-x-2 px-3 py-2 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors text-sm"
                >
                  <PlusIcon className="w-4 h-4" />
                  <span>Add Rule</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
