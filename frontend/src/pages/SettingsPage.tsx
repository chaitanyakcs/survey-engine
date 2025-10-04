import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { useAppStore } from '../store/useAppStore';
import LLMAuditDashboard from '../components/LLMAuditDashboard';
import { 
  CogIcon, 
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface EvaluationSettings {
  evaluation_mode: 'single_call' | 'multiple_calls' | 'hybrid' | 'aira_v1';
  enable_cost_tracking: boolean;
  enable_parallel_processing: boolean;
  enable_ab_testing: boolean;
  cost_threshold_daily: number;
  cost_threshold_monthly: number;
  fallback_mode: 'basic' | 'multiple_calls' | 'disabled';
  
  // Human Prompt Review Settings
  enable_prompt_review: boolean;
  prompt_review_mode: 'disabled' | 'blocking' | 'parallel';
  prompt_review_timeout_hours: number;
  
  // LLM Evaluation Settings
  enable_llm_evaluation: boolean;
  
  
  // Model configuration
  generation_model: string;
  evaluation_model: string;
  embedding_model: string;
}

interface RFQParsingSettings {
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
    prompt_review_timeout_hours: 24,
    
    // LLM Evaluation Settings
    enable_llm_evaluation: true,
    
    
    generation_model: 'openai/gpt-5',
    evaluation_model: 'openai/gpt-5',
    embedding_model: 'all-MiniLM-L6-v2'
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rfqParsing, setRfqParsing] = useState<RFQParsingSettings>({ parsing_model: 'openai/gpt-4o-mini' });
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
      // Save evaluation settings
      const settingsResponse = await fetch('/api/v1/settings/evaluation', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      // Save RFQ parsing settings
      const rfqResponse = await fetch('/api/v1/settings/rfq-parsing', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rfqParsing)
      });

      if (settingsResponse.ok && rfqResponse.ok) {
        addToast({
          type: 'success',
          title: 'Settings Saved',
          message: 'All settings have been updated successfully',
          duration: 3000
        });
      } else {
        const settingsError = settingsResponse.ok ? null : await settingsResponse.json();
        const rfqError = rfqResponse.ok ? null : await rfqResponse.json();
        
        if (settingsError && rfqError) {
          addToast({
            type: 'error',
            title: 'Save Failed',
            message: `Failed to save settings: ${settingsError.detail} and ${rfqError.detail}`,
            duration: 5000
          });
        } else if (settingsError) {
          addToast({
            type: 'error',
            title: 'Save Failed',
            message: `Failed to save evaluation settings: ${settingsError.detail}`,
            duration: 5000
          });
        } else if (rfqError) {
          addToast({
            type: 'error',
            title: 'Save Failed',
            message: `Failed to save RFQ parsing settings: ${rfqError.detail}`,
            duration: 5000
          });
        }
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: 'Failed to save settings. Please try again.',
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
        // Filter out any Anthropics/Claude models if present
        setGenerationModels(data.filter((m: string) => !m.toLowerCase().includes('anthropic') && !m.toLowerCase().includes('claude')));
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
        // Filter out any Anthropics/Claude models if present
        setEvaluationModels(data.filter((m: string) => !m.toLowerCase().includes('anthropic') && !m.toLowerCase().includes('claude')));
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
      prompt_review_timeout_hours: 24,
      
      // LLM Evaluation Settings
      enable_llm_evaluation: true,
      
      
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
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500"></div>
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
                  <CogIcon className="w-8 h-8 text-yellow-600" />
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
                    className="px-6 py-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-white rounded-lg hover:from-yellow-600 hover:to-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
                  >
                    {saving ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <div className="p-6 space-y-8">

            {/* AI Models Configuration */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <CogIcon className="w-6 h-6 text-purple-600" />
                <h2 className="text-xl font-semibold text-gray-900">AI Models</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Generation Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Survey Generation</label>
                  <select
                    value={settings.generation_model}
                    onChange={(e) => setSettings({ ...settings, generation_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    {generationModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Generates surveys</p>
                </div>

                {/* Evaluation Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation</label>
                  <select
                    value={settings.evaluation_model}
                    onChange={(e) => setSettings({ ...settings, evaluation_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    {evaluationModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Evaluates quality</p>
                </div>

                {/* Embedding Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Embeddings</label>
                  <select
                    value={settings.embedding_model}
                    onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    {embeddingModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Semantic search</p>
                </div>

                {/* RFQ Parsing Model */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">RFQ Parsing</label>
                  <select
                    value={rfqParsing.parsing_model}
                    onChange={(e) => setRfqParsing({ ...rfqParsing, parsing_model: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  >
                    {rfqModels.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Parses documents</p>
                </div>
              </div>
            </div>
            {/* Quality Control & Review */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <ChartBarIcon className="w-6 h-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">Quality Control & Review</h2>
              </div>
              
              <div className="space-y-6">
                {/* Enable LLM Evaluation */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Enable AI Quality Evaluation</h3>
                    <p className="text-gray-600">Run AI-powered quality evaluation on generated surveys using pillar-based scoring</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.enable_llm_evaluation}
                      onChange={(e) => setSettings({ ...settings, enable_llm_evaluation: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-green-500 peer-checked:to-emerald-500"></div>
                  </label>
                </div>

                {/* Enable Human Review */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Enable Human Prompt Review</h3>
                    <p className="text-gray-600">Allow human review and approval of AI-generated system prompts</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.enable_prompt_review}
                      onChange={(e) => setSettings({ 
                        ...settings, 
                        enable_prompt_review: e.target.checked,
                        prompt_review_mode: e.target.checked ? settings.prompt_review_mode : 'disabled'
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-green-500 peer-checked:to-emerald-500"></div>
                  </label>
                </div>

                {/* Review Mode Selection */}
                {settings.enable_prompt_review && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Review Mode</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          value: 'parallel',
                          title: 'Parallel Review',
                          description: 'Survey generation continues while prompts are reviewed in parallel',
                          icon: '🔄',
                          recommended: true
                        },
                        {
                          value: 'blocking',
                          title: 'Blocking Review',
                          description: 'Survey generation waits for prompt approval before proceeding',
                          icon: '🛑',
                          recommended: false
                        }
                      ].map((mode) => (
                        <div
                          key={mode.value}
                          className={`border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 ${
                            settings.prompt_review_mode === mode.value
                              ? 'border-green-500 bg-gradient-to-br from-green-50 to-emerald-50'
                              : 'border-gray-200 hover:border-green-300 hover:bg-green-50'
                          }`}
                          onClick={() => setSettings({ ...settings, prompt_review_mode: mode.value as any })}
                        >
                          <div className="flex items-center space-x-3 mb-2">
                            <input
                              type="radio"
                              name="prompt_review_mode"
                              value={mode.value}
                              checked={settings.prompt_review_mode === mode.value}
                              onChange={() => setSettings({ ...settings, prompt_review_mode: mode.value as any })}
                              className="w-4 h-4 text-green-600"
                            />
                            <span className="text-2xl">{mode.icon}</span>
                            <h4 className="text-lg font-medium text-gray-900">{mode.title}</h4>
                            {mode.recommended && (
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Recommended</span>
                            )}
                          </div>
                          <p className="text-gray-600 text-sm ml-7">{mode.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Review Timeout */}
                {settings.enable_prompt_review && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-900">Review Settings</h3>
                    <div className="p-4 bg-gray-50 rounded-xl">
                      <label className="block font-medium text-gray-900 mb-2">
                        Review Timeout (Hours)
                      </label>
                      <div className="flex items-center space-x-3">
                        <ClockIcon className="w-5 h-5 text-gray-500" />
                        <input
                          type="number"
                          value={settings.prompt_review_timeout_hours}
                          onChange={(e) => setSettings({ ...settings, prompt_review_timeout_hours: Number(e.target.value) })}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                          min="1"
                          max="168"
                          step="1"
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Auto-approval timeout (1-168 hours)</p>
                    </div>
                  </div>
                )}
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