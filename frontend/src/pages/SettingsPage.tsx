import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { useAppStore } from '../store/useAppStore';
import LLMAuditDashboard from '../components/LLMAuditDashboard';
import { 
  CogIcon, 
  CheckCircleIcon,
  InformationCircleIcon,
  UserIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface EvaluationSettings {
  evaluation_mode: 'single_call' | 'multiple_calls' | 'hybrid';
  enable_cost_tracking: boolean;
  enable_parallel_processing: boolean;
  enable_ab_testing: boolean;
  cost_threshold_daily: number;
  cost_threshold_monthly: number;
  fallback_mode: 'basic' | 'multiple_calls' | 'disabled';
  
  // Human Prompt Review Settings
  enable_prompt_review: boolean;
  prompt_review_mode: 'disabled' | 'blocking' | 'parallel';
  require_approval_for_generation: boolean;
  auto_approve_trusted_prompts: boolean;
  prompt_review_timeout_hours: number;
  // Model configuration
  generation_model: string;
  evaluation_model: string;
  embedding_model: string;
}

interface RFQParsingSettings {
  auto_apply_threshold: number;
  parsing_model: string;
}

export const SettingsPage: React.FC = () => {
  const { toasts, removeToast, addToast } = useAppStore();
  const { mainContentClasses } = useSidebarLayout();
  
  const [showLLMAuditDashboard, setShowLLMAuditDashboard] = useState(false);
  
  const [settings, setSettings] = useState<EvaluationSettings>({
    evaluation_mode: 'single_call',
    enable_cost_tracking: true,
    enable_parallel_processing: false,
    enable_ab_testing: false,
    cost_threshold_daily: 50,
    cost_threshold_monthly: 1000,
    fallback_mode: 'basic',
    
    // Human Prompt Review Settings
    enable_prompt_review: false,
    prompt_review_mode: 'disabled',
    require_approval_for_generation: false,
    auto_approve_trusted_prompts: false,
    prompt_review_timeout_hours: 24,
    generation_model: 'openai/gpt-5',
    evaluation_model: 'openai/gpt-5',
    embedding_model: 'all-MiniLM-L6-v2'
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rfqParsing, setRfqParsing] = useState<RFQParsingSettings>({ auto_apply_threshold: 0.8, parsing_model: 'openai/gpt-4o-mini' });
  const [rfqModels, setRfqModels] = useState<string[]>([]);
  const [generationModels, setGenerationModels] = useState<string[]>([]);
  const [evaluationModels, setEvaluationModels] = useState<string[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<string[]>([]);

  useEffect(() => {
    fetchSettings();
    fetchRfqParsingSettings();
    fetchRfqModels();
    fetchGenerationModels();
    fetchEvaluationModels();
    fetchEmbeddingModels();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/evaluation');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      addToast({
        type: 'error',
        title: 'Settings Error',
        message: 'Failed to load evaluation settings',
        duration: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/settings/evaluation', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        addToast({
          type: 'success',
          title: 'Settings Saved',
          message: 'Evaluation settings have been updated successfully',
          duration: 3000
        });
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: 'Failed to save evaluation settings',
        duration: 5000
      });
    } finally {
      setSaving(false);
    }
  };

  const fetchRfqParsingSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/rfq-parsing');
      if (response.ok) {
        const data = await response.json();
        setRfqParsing(data);
      }
    } catch (error) {
      console.error('Failed to fetch RFQ parsing settings:', error);
    }
  };

  const saveRfqParsingSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings/rfq-parsing', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rfqParsing)
      });
      if (!response.ok) throw new Error('Failed to save RFQ parsing settings');
      addToast({ type: 'success', title: 'Settings Saved', message: 'RFQ parsing settings updated', duration: 3000 });
    } catch (error) {
      addToast({ type: 'error', title: 'Save Failed', message: 'Failed to save RFQ parsing settings', duration: 5000 });
    }
  };

  const fetchRfqModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/rfq-parsing/models');
      if (response.ok) {
        const data = await response.json();
        setRfqModels(data);
      }
    } catch (error) {
      console.error('Failed to fetch RFQ models:', error);
    }
  };

  const fetchGenerationModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/generation/models');
      if (response.ok) {
        const data = await response.json();
        setGenerationModels(data);
      }
    } catch (error) {
      console.error('Failed to fetch generation models:', error);
    }
  };

  const fetchEvaluationModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/evaluation/models');
      if (response.ok) {
        const data = await response.json();
        setEvaluationModels(data);
      }
    } catch (error) {
      console.error('Failed to fetch evaluation models:', error);
    }
  };

  const fetchEmbeddingModels = async () => {
    try {
      const response = await fetch('/api/v1/settings/embedding/models');
      if (response.ok) {
        const data = await response.json();
        setEmbeddingModels(data);
      }
    } catch (error) {
      console.error('Failed to fetch embedding models:', error);
    }
  };

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    }
  };

  const resetToDefaults = () => {
    setSettings({
      evaluation_mode: 'single_call',
      enable_cost_tracking: true,
      enable_parallel_processing: false,
      enable_ab_testing: false,
      cost_threshold_daily: 50,
      cost_threshold_monthly: 1000,
      fallback_mode: 'basic',
      
      // Human Prompt Review Settings
      enable_prompt_review: false,
      prompt_review_mode: 'disabled',
      require_approval_for_generation: false,
      auto_approve_trusted_prompts: false,
      prompt_review_timeout_hours: 24,
      
      // Model configuration
      generation_model: 'openai/gpt-4o-mini',
      evaluation_model: 'openai/gpt-4o-mini',
      embedding_model: 'sentence-transformers/all-MiniLM-L6-v2'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar currentView="settings" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      <Sidebar currentView="settings" onViewChange={handleViewChange} />
      
      <div className={mainContentClasses}>
        <div className="space-y-8">
          {/* Header */}
          <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
            <div className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CogIcon className="w-8 h-8 text-indigo-600" />
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">Survey Generation Settings</h1>
                    <p className="text-gray-600">Configure human review and survey generation preferences</p>
                  </div>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowLLMAuditDashboard(true)}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2"
                  >
                    <ChartBarIcon className="w-4 h-4" />
                    <span>LLM Audit</span>
                  </button>
                  <button
                    onClick={resetToDefaults}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Reset to Defaults
                  </button>
                  <button
                    onClick={saveSettings}
                    disabled={saving}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {saving ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="p-6 space-y-8">
            {/* Model Configuration */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <CogIcon className="w-6 h-6 text-indigo-600" />
                <h2 className="text-xl font-semibold text-gray-900">Model Configuration</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Generation Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Survey Generation Model</label>
                  <select
                    value={settings.generation_model}
                    onChange={(e) => setSettings({ ...settings, generation_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {generationModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Used for generating surveys in workflows.</p>
                </div>

                {/* Evaluation Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation Model</label>
                  <select
                    value={settings.evaluation_model}
                    onChange={(e) => setSettings({ ...settings, evaluation_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {evaluationModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Used by pillar evaluators.</p>
                </div>

                {/* Embedding Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Embedding Model</label>
                  <select
                    value={settings.embedding_model}
                    onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {embeddingModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Used for semantic retrieval and similarity.</p>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={saveSettings}
                  disabled={saving}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Model Settings'}
                </button>
              </div>
            </div>
            {/* RFQ Parsing Settings */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <CogIcon className="w-6 h-6 text-indigo-600" />
                <h2 className="text-xl font-semibold text-gray-900">RFQ Parsing Settings</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Auto-apply threshold */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Auto-apply Threshold (0-1)</label>
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={rfqParsing.auto_apply_threshold}
                    onChange={(e) => setRfqParsing({ ...rfqParsing, auto_apply_threshold: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Fields with confidence ≥ threshold are auto-filled.</p>
                </div>

                {/* Parsing Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">LLM Model for Parsing</label>
                  <select
                    value={rfqParsing.parsing_model}
                    onChange={(e) => setRfqParsing({ ...rfqParsing, parsing_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    {rfqModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Top models fetched from Replicate.</p>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={saveRfqParsingSettings}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Save RFQ Parsing Settings
                </button>
              </div>
            </div>
            {/* Human Prompt Review Settings */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <UserIcon className="w-6 h-6 text-orange-600" />
                <h2 className="text-xl font-semibold text-gray-900">Human Prompt Review</h2>
              </div>
              
              {/* Enable Prompt Review */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl mb-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Enable Prompt Review</h3>
                  <p className="text-gray-600">Allow human review and approval of AI-generated system prompts</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enable_prompt_review}
                    onChange={(e) => setSettings({ 
                      ...settings, 
                      enable_prompt_review: e.target.checked,
                      // Reset dependent settings if disabling
                      prompt_review_mode: e.target.checked ? settings.prompt_review_mode : 'disabled',
                      require_approval_for_generation: e.target.checked ? settings.require_approval_for_generation : false
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                </label>
              </div>

              {/* Review Mode Selection */}
              {settings.enable_prompt_review && (
                <div className="space-y-4 mb-6">
                  <h3 className="text-lg font-medium text-gray-900">Review Mode</h3>
                  {[
                    {
                      value: 'parallel',
                      title: 'Parallel Review (Recommended)',
                      description: 'Survey generation continues while prompts are reviewed in parallel. No blocking delays.',
                      icon: '🔄',
                      pros: ['No generation delays', 'Continuous improvement', 'Better user experience'],
                      cons: ['Review happens after generation']
                    },
                    {
                      value: 'blocking',
                      title: 'Blocking Review',
                      description: 'Survey generation waits for prompt approval before proceeding. Ensures all prompts are reviewed.',
                      icon: '🛑',
                      pros: ['Complete control', 'All prompts reviewed', 'Quality assurance'],
                      cons: ['Significant delays', 'Blocks workflow']
                    }
                  ].map((mode) => (
                    <div
                      key={mode.value}
                      className={`border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 ${
                        settings.prompt_review_mode === mode.value
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                      onClick={() => setSettings({ ...settings, prompt_review_mode: mode.value as any })}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <input
                              type="radio"
                              name="prompt_review_mode"
                              value={mode.value}
                              checked={settings.prompt_review_mode === mode.value}
                              onChange={() => setSettings({ ...settings, prompt_review_mode: mode.value as any })}
                              className="w-4 h-4 text-indigo-600"
                            />
                            <span className="text-2xl">{mode.icon}</span>
                            <h4 className="text-lg font-medium text-gray-900">{mode.title}</h4>
                          </div>
                          <p className="text-gray-600 mb-3 ml-7">{mode.description}</p>
                          <div className="ml-7 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                            <div>
                              <p className="font-medium text-green-700 mb-1">Pros:</p>
                              <ul className="text-green-600 space-y-1">
                                {mode.pros.map((pro, idx) => (
                                  <li key={idx}>• {pro}</li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <p className="font-medium text-red-700 mb-1">Cons:</p>
                              <ul className="text-red-600 space-y-1">
                                {mode.cons.map((con, idx) => (
                                  <li key={idx}>• {con}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Additional Review Options */}
              {settings.enable_prompt_review && (
                <div className="space-y-4">
                  {/* Require Approval for Generation */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Require Approval for Generation</h3>
                      <p className="text-gray-600">Block survey generation until prompt is approved (only applies to blocking mode)</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.require_approval_for_generation}
                        disabled={settings.prompt_review_mode !== 'blocking'}
                        onChange={(e) => setSettings({ ...settings, require_approval_for_generation: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className={`w-11 h-6 rounded-full peer ${
                        settings.prompt_review_mode !== 'blocking' 
                          ? 'bg-gray-200 cursor-not-allowed' 
                          : 'bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 peer-checked:bg-indigo-600'
                      } peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all`}></div>
                    </label>
                  </div>

                  {/* Auto-approve Trusted Prompts */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Auto-approve Trusted Prompts</h3>
                      <p className="text-gray-600">Automatically approve prompts similar to previously approved ones</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.auto_approve_trusted_prompts}
                        onChange={(e) => setSettings({ ...settings, auto_approve_trusted_prompts: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                    </label>
                  </div>

                  {/* Review Timeout */}
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <label className="block text-lg font-medium text-gray-900 mb-2">
                      Review Timeout (Hours)
                    </label>
                    <div className="flex items-center space-x-3">
                      <ClockIcon className="w-5 h-5 text-gray-500" />
                      <input
                        type="number"
                        value={settings.prompt_review_timeout_hours}
                        onChange={(e) => setSettings({ ...settings, prompt_review_timeout_hours: Number(e.target.value) })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        min="1"
                        max="168"
                        step="1"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">How long to wait for review before auto-approval (1-168 hours)</p>
                  </div>
                </div>
              )}
            </div>

            {/* Survey Evaluation Mode */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Survey Evaluation</h2>
              
              <div className="space-y-4">
                {[
                  {
                    value: 'single_call',
                    title: 'Single Call (Recommended)',
                    description: 'One comprehensive AI evaluation for all quality pillars. Fast and cost-effective.',
                    color: 'green',
                    icon: <CheckCircleIcon className="w-6 h-6 text-green-600" />,
                    pros: ['Fastest evaluation', 'Lower API costs', 'Consistent scoring'],
                    cons: ['Less granular feedback']
                  },
                  {
                    value: 'multiple_calls',
                    title: 'Parallel Evaluation',
                    description: 'Separate AI evaluations for each quality pillar running in parallel. More detailed analysis.',
                    color: 'blue',
                    icon: <CogIcon className="w-6 h-6 text-blue-600" />,
                    pros: ['Detailed pillar feedback', 'Parallel processing', 'Specialized analysis'],
                    cons: ['Higher API costs', 'Slightly slower']
                  }
                ].map((mode) => (
                  <div
                    key={mode.value}
                    className={`border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 ${
                      settings.evaluation_mode === mode.value
                        ? `border-${mode.color}-500 bg-${mode.color}-50`
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => setSettings({ ...settings, evaluation_mode: mode.value as any })}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <input
                            type="radio"
                            name="evaluation_mode"
                            value={mode.value}
                            checked={settings.evaluation_mode === mode.value}
                            onChange={() => setSettings({ ...settings, evaluation_mode: mode.value as any })}
                            className="w-4 h-4 text-indigo-600"
                          />
                          {mode.icon}
                          <h3 className="text-lg font-medium text-gray-900">{mode.title}</h3>
                        </div>
                        <p className="text-gray-600 mb-3 ml-7">{mode.description}</p>
                        <div className="ml-7 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                          <div>
                            <p className="font-medium text-green-700 mb-1">Pros:</p>
                            <ul className="text-green-600 space-y-1">
                              {mode.pros.map((pro, idx) => (
                                <li key={idx}>• {pro}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="font-medium text-red-700 mb-1">Cons:</p>
                            <ul className="text-red-600 space-y-1">
                              {mode.cons.map((con, idx) => (
                                <li key={idx}>• {con}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Parallel Processing Toggle */}
              {settings.evaluation_mode === 'multiple_calls' && (
                <div className="mt-6 p-4 bg-blue-50 rounded-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Enable Parallel Processing</h3>
                      <p className="text-gray-600">Run pillar evaluations simultaneously for faster results</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.enable_parallel_processing}
                        onChange={(e) => setSettings({ ...settings, enable_parallel_processing: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Information Panel */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-start space-x-3">
                <InformationCircleIcon className="w-6 h-6 text-blue-600 mt-0.5" />
                <div>
                  <h3 className="text-lg font-medium text-blue-900 mb-2">About Human Review</h3>
                  <div className="text-blue-800 space-y-2">
                    <p><strong>Parallel Review:</strong> Allows continuous survey generation while building a prompt approval dataset for future improvements. Recommended for most workflows.</p>
                    <p><strong>Blocking Review:</strong> Ensures complete human oversight but introduces delays in the generation pipeline. Use when quality control is critical.</p>
                    <p><strong>Auto-approval:</strong> Uses machine learning to automatically approve prompts similar to previously approved ones, reducing manual review workload.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* LLM Audit Dashboard Modal */}
      {showLLMAuditDashboard && (
        <LLMAuditDashboard onClose={() => setShowLLMAuditDashboard(false)} />
      )}
    </div>
  );
};