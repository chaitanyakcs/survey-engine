import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { PlusIcon, TrashIcon, CheckIcon, XMarkIcon, PencilIcon, ExclamationTriangleIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { useAppStore } from '../store/useAppStore';
import PillarRulesManager from '../components/PillarRulesManager';

interface MethodologyRule {
  description: string;
  required_questions: number;
  validation_rules: string[];
  question_flow?: string[];
  best_practices?: string[];
}

interface QualityRuleItem {
  id: string;
  text: string;
  created_at?: string;
  updated_at?: string;
}

interface QualityRule {
  [category: string]: QualityRuleItem[];
}

interface SystemPrompt {
  id: string;
  prompt_text: string;
  created_at?: string;
  updated_at?: string;
}

export const RulesPage: React.FC = () => {
  const { toasts, removeToast, addToast } = useAppStore();
  const [methodologies, setMethodologies] = useState<Record<string, MethodologyRule>>({});
  const [qualityRules, setQualityRules] = useState<QualityRule>({});
  const [systemPrompt, setSystemPrompt] = useState<SystemPrompt>({ id: '', prompt_text: '', created_at: '', updated_at: '' });
  const [isEditingPrompt, setIsEditingPrompt] = useState(false);
  const [tempPromptText, setTempPromptText] = useState('');
  const [loading, setLoading] = useState(true);
  const { mainContentClasses } = useSidebarLayout();
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  // Quality rules editing states
  const [editingRule, setEditingRule] = useState<{category: string, ruleId: string} | null>(null);
  const [editingText, setEditingText] = useState('');
  const [addingRule, setAddingRule] = useState<{category: string} | null>(null);
  const [newRuleText, setNewRuleText] = useState('');
  const [saving, setSaving] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt';
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);

  // Methodology rules editing states
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

  // Collapse/expand states for sections
  const [expandedSections, setExpandedSections] = useState({
    methodology: false,
    quality: false,
    pillars: false,
    systemPrompt: false
  });

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/?view=golden-examples';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    }
  };

  const fetchQualityRules = useCallback(async () => {
    try {
      const timestamp = new Date().getTime();
      const qualityRes = await fetch(`/api/v1/rules/quality-rules?t=${timestamp}`, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      if (qualityRes.ok) {
        const qualityData = await qualityRes.json();
        setQualityRules(qualityData);
      }
    } catch (error) {
      console.error('Failed to fetch quality rules:', error);
    }
  }, []);

  const fetchRules = useCallback(async (isRetry = false) => {
    try {
      if (isRetry) {
        setIsRetrying(true);
        addToast({
          type: 'info',
          title: 'Retrying...',
          message: 'Attempting to fetch rules again. Please wait.',
          duration: 3000
        });
      } else {
        setLoading(true);
      }
      
      const timestamp = new Date().getTime();
      const [methodologiesRes, qualityRes, systemPromptRes] = await Promise.all([
        fetch(`/api/v1/rules/methodologies?t=${timestamp}`, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }),
        fetch(`/api/v1/rules/quality-rules?t=${timestamp}`, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        }),
        fetch(`/api/v1/rules/system-prompt?t=${timestamp}`, {
          method: 'GET',
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        })
      ]);

      if (!methodologiesRes.ok || !qualityRes.ok) {
        throw new Error('Failed to fetch rules');
      }

      const methodologiesData = await methodologiesRes.json();
      const qualityData = await qualityRes.json();

      setMethodologies(methodologiesData.rules || {});
      setQualityRules(qualityData);

      // Fetch system prompt
      if (systemPromptRes.ok) {
        const systemPromptData = await systemPromptRes.json();
        setSystemPrompt(systemPromptData);
        setTempPromptText(systemPromptData.prompt_text || '');
      }

      setError(null);
      
      if (isRetry) {
        addToast({
          type: 'success',
          title: 'Rules Loaded Successfully',
          message: 'Rules have been fetched and loaded successfully.',
          duration: 5000
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch rules';
      setError(errorMessage);
      
      addToast({
        type: 'error',
        title: 'Failed to Load Rules',
        message: errorMessage,
        duration: 7000
      });
    } finally {
      setLoading(false);
      setIsRetrying(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  // Quality Rules Handlers
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
        // Refresh the rules from the server to ensure consistency
        await fetchRules();
        setEditingRule(null);
        setEditingText('');
      } else {
        alert('Failed to update quality rule');
      }
    } catch (error) {
      console.error('Failed to update quality rule:', error);
      alert('Failed to update quality rule');
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
        // Refresh data from server to get proper UUIDs instead of using temporary IDs
        await fetchQualityRules();
        setAddingRule(null);
        setNewRuleText('');
      } else {
        alert('Failed to add quality rule');
      }
    } catch (error) {
      console.error('Failed to add quality rule:', error);
      alert('Failed to add quality rule');
    } finally {
      setSaving(null);
    }
  };

  const deleteRule = async (category: string, ruleId: string) => {
    console.log('🗑️ [FRONTEND] Starting quality rule deletion:', { category, ruleId });
    
    setDeleteConfirm({
      show: true,
      type: 'rule',
      title: 'Delete Rule',
      message: 'Are you sure you want to delete this rule? This action cannot be undone.',
      onConfirm: async () => {
        setDeleteConfirm(null);
        await performRuleDeletion(category, ruleId);
      }
    });
  };

  const performRuleDeletion = async (category: string, ruleId: string) => {

    const saveKey = `delete-${category}-${ruleId}`;
    setSaving(saveKey);

    try {
      console.log('🗑️ [FRONTEND] Sending DELETE request with rule_id:', ruleId);

      const response = await fetch('/api/v1/rules/quality-rules', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rule_id: ruleId
        })
      });

      console.log('🗑️ [FRONTEND] Response status:', response.status, response.statusText);

      if (response.ok) {
        console.log('✅ [FRONTEND] Delete request successful');
        const responseData = await response.json();
        console.log('✅ [FRONTEND] Delete response:', responseData);
        
        // Refresh the data from server to ensure consistency
        console.log('🔄 [FRONTEND] Refreshing quality rules from server...');
        await fetchQualityRules();
        
        addToast({
          type: 'success',
          title: 'Rule Deleted',
          message: 'Quality rule has been deleted successfully',
          duration: 3000
        });
      } else {
        console.error('❌ [FRONTEND] Delete request failed:', response.status, response.statusText);
        let errorMessage = 'Failed to delete quality rule';
        try {
          const errorData = await response.json();
          console.error('❌ [FRONTEND] Error response data:', errorData);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (parseError) {
          console.error('❌ [FRONTEND] Failed to parse error response:', parseError);
        }
        
        addToast({
          type: 'error',
          title: 'Delete Failed',
          message: errorMessage,
          duration: 5000
        });
      }
    } catch (error) {
      console.error('❌ [FRONTEND] Network/Exception error during delete:', error);
      const errorMessage = error instanceof Error ? error.message : 'Network error occurred while deleting the rule';
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: errorMessage,
        duration: 5000
      });
    } finally {
      console.log('🔄 [FRONTEND] Delete operation completed, clearing saving state');
      setSaving(null);
    }
  };

  // System Prompt Handlers
  const handleEditSystemPrompt = () => {
    setIsEditingPrompt(true);
  };

  const handleSaveSystemPrompt = async () => {
    try {
      const response = await fetch('/api/v1/rules/system-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_text: tempPromptText })
      });

      if (response.ok) {
        const result = await response.json();
        setSystemPrompt({
          id: result.id,
          prompt_text: result.prompt_text,
          created_at: result.created_at || '',
          updated_at: result.updated_at || ''
        });
        setIsEditingPrompt(false);
      } else {
        alert('Failed to save system prompt');
      }
    } catch (error) {
      console.error('Failed to save system prompt:', error);
      alert('Failed to save system prompt');
    }
  };

  const handleCancelEdit = () => {
    setTempPromptText(systemPrompt.prompt_text);
    setIsEditingPrompt(false);
  };

  const handleDeleteSystemPrompt = async () => {
    setDeleteConfirm({
      show: true,
      type: 'system-prompt',
      title: 'Delete System Prompt',
      message: 'Are you sure you want to delete the system prompt? This action cannot be undone.',
      onConfirm: async () => {
        setDeleteConfirm(null);
        await performSystemPromptDeletion();
      }
    });
  };

  const performSystemPromptDeletion = async () => {
    try {
      const response = await fetch('/api/v1/rules/system-prompt', { method: 'DELETE' });
      if (response.ok) {
        setSystemPrompt({ id: '', prompt_text: '', created_at: '', updated_at: '' });
        setTempPromptText('');
        addToast({
          type: 'success',
          title: 'System Prompt Deleted',
          message: 'System prompt has been deleted successfully',
          duration: 3000
        });
      } else {
        addToast({
          type: 'error',
          title: 'Delete Failed',
          message: 'Failed to delete system prompt',
          duration: 5000
        });
      }
    } catch (error) {
      console.error('Failed to delete system prompt:', error);
      addToast({
        type: 'error',
        title: 'Delete Failed',
        message: 'Network error occurred while deleting system prompt',
        duration: 5000
      });
    }
  };

  // Methodology Rules Handlers
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
        setMethodologies(updatedMethodologies);
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
    setDeleteConfirm({
      show: true,
      type: 'methodology',
      title: 'Delete Methodology',
      message: `Are you sure you want to delete the '${methodologyName}' methodology? This action cannot be undone.`,
      onConfirm: async () => {
        setDeleteConfirm(null);
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
        setMethodologies(updatedMethodologies);
        addToast({
          type: 'success',
          title: 'Methodology Deleted',
          message: `Methodology '${methodologyName}' has been deleted successfully.`,
          duration: 3000
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
        setMethodologies(updatedMethodologies);
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

  const toggleSection = (section: 'methodology' | 'quality' | 'pillars' | 'systemPrompt') => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="rules" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="rules" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Rules</h3>
              <p className="text-red-600 mb-4">{error}</p>
              <button
                onClick={() => fetchRules(true)}
                disabled={isRetrying}
                className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isRetrying ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Retrying...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Try Again
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <Sidebar currentView="rules" onViewChange={handleViewChange} />
      <div className={mainContentClasses}>
        <div className="p-6 space-y-8">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Survey Rules & Guidelines</h1>
            <p className="text-lg text-gray-600">Configure methodology, quality standards, and AI instructions</p>
          </div>

          {/* Methodology Rules */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
            <div 
              className="bg-gradient-to-r from-emerald-500 via-emerald-600 to-teal-600 px-6 py-6 text-white cursor-pointer"
              onClick={() => toggleSection('methodology')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">Methodology Rules</h2>
                    <p className="text-emerald-100 mt-1">Predefined research methodologies and their requirements</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      startAddMethodology();
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors"
                  >
                    <PlusIcon className="w-5 h-5" />
                    <span>Add Methodology</span>
                  </button>
                  <ChevronDownIcon 
                    className={`w-6 h-6 transition-transform duration-200 ${
                      expandedSections.methodology ? 'rotate-180' : ''
                    }`} 
                  />
                </div>
              </div>
            </div>
            {expandedSections.methodology && (
              <div className="p-6">
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
              </div>
            )}
          </div>

          {/* Quality Rules */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
            <div 
              className="bg-gradient-to-r from-amber-500 via-orange-500 to-red-500 px-6 py-6 text-white cursor-pointer"
              onClick={() => toggleSection('quality')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">Quality Standards</h2>
                    <p className="text-amber-100 mt-1">Customizable quality rules for survey generation</p>
                  </div>
                </div>
                <ChevronDownIcon 
                  className={`w-6 h-6 transition-transform duration-200 ${
                    expandedSections.quality ? 'rotate-180' : ''
                  }`} 
                />
              </div>
            </div>
            {expandedSections.quality && (
              <div className="p-6">
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
              </div>
            )}
          </div>

          {/* Pillar Rules */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
            <div 
              className="bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-700 px-6 py-6 text-white cursor-pointer"
              onClick={() => toggleSection('pillars')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-2xl font-bold">5-Pillar Evaluation Rules</h2>
                      <span className="px-2 py-1 bg-white/20 rounded-full text-xs font-medium">NEW</span>
                    </div>
                    <p className="text-purple-100 mt-1">Customize evaluation criteria for the 5-pillar survey assessment framework</p>
                  </div>
                </div>
                <ChevronDownIcon 
                  className={`w-6 h-6 transition-transform duration-200 ${
                    expandedSections.pillars ? 'rotate-180' : ''
                  }`} 
                />
              </div>
            </div>
            {expandedSections.pillars && (
              <div className="p-6">
                <PillarRulesManager />
              </div>
            )}
          </div>

          {/* System Prompt - Advanced Section */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
            <div 
              className="bg-gradient-to-r from-purple-500 via-purple-600 to-pink-600 px-6 py-6 text-white cursor-pointer"
              onClick={() => toggleSection('systemPrompt')}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h2 className="text-2xl font-bold">System Prompt</h2>
                      <span className="px-2 py-1 bg-white/20 rounded-full text-xs font-medium">ADVANCED</span>
                    </div>
                    <p className="text-purple-100 mt-1">Add custom instructions that will be injected into every AI prompt</p>
                  </div>
                </div>
                <ChevronDownIcon 
                  className={`w-6 h-6 transition-transform duration-200 ${
                    expandedSections.systemPrompt ? 'rotate-180' : ''
                  }`} 
                />
              </div>
            </div>
            {expandedSections.systemPrompt && (
              <div className="p-6">
                <div className="mb-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-blue-900 mb-1">How System Prompt Works</h4>
                      <p className="text-sm text-blue-800">
                        Your custom system prompt will be added to every AI generation request, allowing you to provide
                        specific instructions, context, or requirements that will be followed consistently across all survey generations.
                      </p>
                    </div>
                  </div>
                </div>

                {!isEditingPrompt ? (
                  <div className="space-y-4">
                    {systemPrompt.prompt_text ? (
                      <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="text-sm font-medium text-gray-700">Current System Prompt</h4>
                          <div className="flex space-x-2">
                            <button
                              onClick={handleEditSystemPrompt}
                              className="px-3 py-1 text-sm text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors"
                            >
                              Edit
                            </button>
                            <button
                              onClick={handleDeleteSystemPrompt}
                              className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        <div className="whitespace-pre-wrap text-sm text-gray-600 leading-relaxed">
                          {systemPrompt.prompt_text}
                        </div>
                        {systemPrompt.updated_at && (
                          <div className="text-xs text-gray-500 mt-2">
                            Last updated: {new Date(systemPrompt.updated_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        <p className="text-lg font-medium">No system prompt yet</p>
                        <p className="text-sm mb-4">Add custom instructions to guide the AI</p>
                        <button
                          onClick={handleEditSystemPrompt}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                        >
                          Add System Prompt
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        System Prompt Instructions
                      </label>
                      <textarea
                        value={tempPromptText}
                        onChange={(e) => setTempPromptText(e.target.value)}
                        placeholder="Enter your custom system prompt instructions here. These will be added to every AI generation request..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent h-32 resize-y"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        These instructions will be injected into every AI prompt to guide survey generation.
                      </p>
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={handleSaveSystemPrompt}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                      >
                        Save Prompt
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {deleteConfirm.title}
                  </h3>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-500">
                  {deleteConfirm.message}
                </p>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setDeleteConfirm(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={deleteConfirm.onConfirm}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${
                    deleteConfirm.type === 'rule' || deleteConfirm.type === 'methodology' || deleteConfirm.type === 'system-prompt'
                      ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                      : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                  }`}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};