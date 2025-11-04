import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { useAppStore } from '../store/useAppStore';
import { RetrievalWeightsAccordion } from '../components/RetrievalWeightsAccordion';
import { MethodologyRules } from '../components/MethodologyRules';
import { PillarRulesSection } from '../components/PillarRulesSection';
import { SystemPromptComponent } from '../components/SystemPrompt';
import { QNRTaxonomyManagement } from '../components/QNRTaxonomyManagement';
import { 
  CogIcon, 
  ClockIcon,
  ChartBarIcon,
  DocumentTextIcon,
  BeakerIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';

interface EvaluationSettings {
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
  
  // Model configuration
  generation_model: string;
  evaluation_model: string;
  embedding_model: string;
  llm_provider: 'replicate' | 'openai';
}

interface RFQParsingSettings {
  parsing_model: string;
}

interface RetrievalWeights {
  id: string;
  context_type: 'global' | 'methodology' | 'industry';
  context_value: string;
  semantic_weight: number;
  methodology_weight: number;
  industry_weight: number;
  quality_weight: number;
  annotation_weight: number;
  enabled: boolean;
}

interface MethodologyRule {
  description: string;
  required_questions: number;
  validation_rules: string[];
  question_flow?: string[];
  best_practices?: string[];
}

interface SystemPrompt {
  id: string;
  prompt_text: string;
  created_at?: string;
  updated_at?: string;
}

export const SettingsPage: React.FC = () => {
  const { toasts, removeToast, addToast } = useAppStore();
  const { mainContentClasses } = useSidebarLayout();
  
  // Tab management
  const [activeTab, setActiveTab] = useState<'survey-generation' | 'evaluation'>('survey-generation');
  
  // Rules state
  const [methodologies, setMethodologies] = useState<Record<string, MethodologyRule>>({});
  const [systemPrompt, setSystemPrompt] = useState<SystemPrompt>({ id: '', prompt_text: '', created_at: '', updated_at: '' });
  const [expandedSections, setExpandedSections] = useState({
    qnrTaxonomy: false,
    aiModels: false,
    qualityControl: false,
    retrievalWeights: false,
    methodology: false,
    pillars: false,
    systemPrompt: false
  });
  const [saving, setSaving] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt' | 'pillar-rule';
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);
  
  const [settings, setSettings] = useState<EvaluationSettings>({
    enable_cost_tracking: false,
    enable_parallel_processing: false,
    enable_ab_testing: false,
    cost_threshold_daily: 50,
    cost_threshold_monthly: 1000,
    fallback_mode: 'basic',
    
    // Human Prompt Review Settings
    enable_prompt_review: false,
    prompt_review_mode: 'disabled',
    prompt_review_timeout_hours: 24,
    
    generation_model: 'openai/gpt-5',
    evaluation_model: 'openai/gpt-5',
    embedding_model: 'all-MiniLM-L6-v2',
    llm_provider: 'replicate'
  });
  
  const [loading, setLoading] = useState(true);
  const [rfqParsing, setRfqParsing] = useState<RFQParsingSettings>({ parsing_model: 'openai/gpt-4o-mini' });
  const [rfqModels, setRfqModels] = useState<string[]>([]);
  const [generationModels, setGenerationModels] = useState<string[]>([]);
  const [evaluationModels, setEvaluationModels] = useState<string[]>([]);
  const [embeddingModels, setEmbeddingModels] = useState<string[]>([]);
  const [retrievalWeights, setRetrievalWeights] = useState<RetrievalWeights[]>([]);

  const fetchSettings = useCallback(async () => {
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
  }, [addToast]);

  const saveSettings = async () => {
    setSaving('saving');
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
      setSaving(null);
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

  const fetchGenerationModels = async (provider?: string) => {
    try {
      const providerParam = provider || settings.llm_provider;
      const response = await fetch(`/api/v1/settings/generation/models?provider=${providerParam}`);
      if (response.ok) {
        const data = await response.json();
        setGenerationModels(data);
        // If no model selected or selected model not in list, select first one
        if (!generationModels.includes(settings.generation_model) || providerParam !== settings.llm_provider) {
          if (data.length > 0) {
            setSettings({ ...settings, generation_model: data[0] });
          }
        }
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

  const fetchRetrievalWeights = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/retrieval-weights/');
      if (response.ok) {
        const data = await response.json();
        setRetrievalWeights(data);
      }
    } catch (error) {
      console.error('Failed to fetch retrieval weights:', error);
      addToast({
        type: 'error',
        title: 'Settings Error',
        message: 'Failed to load retrieval weights',
        duration: 5000
      });
    }
  }, [addToast]);

  const fetchRules = useCallback(async () => {
    try {
      const timestamp = new Date().getTime();
      
      const [methodologiesRes, systemPromptRes] = await Promise.all([
        fetch(`/api/v1/rules/methodologies?t=${timestamp}`, {
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

      if (methodologiesRes.ok) {
        const methodologiesData = await methodologiesRes.json();
        setMethodologies(methodologiesData.rules || {});
      }

      if (systemPromptRes.ok) {
        const systemPromptData = await systemPromptRes.json();
        setSystemPrompt(systemPromptData);
      }
    } catch (error) {
      console.error('Failed to fetch rules:', error);
      addToast({
        type: 'error',
        title: 'Rules Error',
        message: 'Failed to load rules data',
        duration: 5000
      });
    }
  }, [addToast]);

  const updateRetrievalWeight = async (weightId: string, updates: Partial<RetrievalWeights>) => {
    try {
      const response = await fetch(`/api/v1/retrieval-weights/${weightId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        // Update local state
        setRetrievalWeights(prev => 
          prev.map(w => w.id === weightId ? { ...w, ...updates } : w)
        );
      } else {
        throw new Error('Failed to update weights');
      }
    } catch (error) {
      console.error('Failed to update retrieval weights:', error);
      throw error; // Re-throw to let the carousel handle the error
    }
  };

  const toggleSection = (section: 'qnrTaxonomy' | 'aiModels' | 'qualityControl' | 'retrievalWeights' | 'methodology' | 'pillars' | 'systemPrompt') => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const showDeleteConfirm = (config: {
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt' | 'pillar-rule';
    title: string;
    message: string;
    onConfirm: () => void;
  }) => {
    setDeleteConfirm(config);
  };

  useEffect(() => {
    fetchSettings();
    fetchRfqParsingSettings();
    fetchRfqModels();
    fetchGenerationModels(settings.llm_provider);
    fetchEvaluationModels();
    fetchEmbeddingModels();
    fetchRetrievalWeights();
    fetchRules();
  }, [fetchSettings, fetchRetrievalWeights, fetchRules]);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
    }
  };

  const resetToDefaults = () => {
    setSettings({
      enable_cost_tracking: false,
      enable_parallel_processing: false,
      enable_ab_testing: false,
      cost_threshold_daily: 50,
      cost_threshold_monthly: 1000,
      fallback_mode: 'basic',
      
      // Human Prompt Review Settings
      enable_prompt_review: false,
      prompt_review_mode: 'disabled',
      prompt_review_timeout_hours: 24,
      
      // Model configuration
      generation_model: 'openai/gpt-4o-mini',
      evaluation_model: 'openai/gpt-4o-mini',
      embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
      llm_provider: 'replicate'
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
                    <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                    <p className="text-gray-600">Configure survey generation and evaluation preferences</p>
                  </div>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={resetToDefaults}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Reset to Defaults
                  </button>
                  <button
                    onClick={saveSettings}
                    disabled={saving === 'saving'}
                    className="px-6 py-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-white rounded-lg hover:from-yellow-600 hover:to-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg"
                  >
                    {saving === 'saving' ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </div>
            </div>
          </header>

          {/* Tab Navigation */}
          <div className="bg-white border-b border-gray-200">
            <div className="px-6">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('survey-generation')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'survey-generation'
                      ? 'border-yellow-500 text-yellow-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <DocumentTextIcon className="w-5 h-5" />
                    <span>Survey Generation</span>
                  </div>
                </button>
                <button
                  onClick={() => setActiveTab('evaluation')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === 'evaluation'
                      ? 'border-yellow-500 text-yellow-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <BeakerIcon className="w-5 h-5" />
                    <span>Evaluation</span>
                  </div>
                </button>
              </nav>
            </div>
          </div>

          <div className="p-6 space-y-8">
            {/* Survey Generation Tab */}
            {activeTab === 'survey-generation' && (
              <div className="space-y-8">
                {/* Survey Structure Rules */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('qnrTaxonomy')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                          </svg>
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">Survey Structure Rules</h2>
                          <p className="text-gray-600 mt-1">Define which question types must appear in each survey section. Edit labels to customize what questions AI generates for your industry or methodology.</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.qnrTaxonomy ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.qnrTaxonomy && (
                    <div className="p-6">
                      <QNRTaxonomyManagement />
                    </div>
                  )}
                </div>

                {/* AI Models Configuration */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('aiModels')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <CogIcon className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">AI Models</h2>
                          <p className="text-gray-600 mt-1">Configure AI models for survey generation and processing</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.aiModels ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.aiModels && (
                    <div className="p-6">
                      {/* LLM Provider Selection */}
                      <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-700 mb-2">LLM Provider</label>
                        <select
                          value={settings.llm_provider}
                          onChange={(e) => {
                            const newProvider = e.target.value as 'replicate' | 'openai';
                            setSettings({ ...settings, llm_provider: newProvider });
                            // Fetch models for the new provider
                            fetchGenerationModels(newProvider);
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                        >
                          <option value="replicate">Replicate</option>
                          <option value="openai">OpenAI</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                          {settings.llm_provider === 'openai' 
                            ? 'Requires OPENAI_API_KEY environment variable' 
                            : 'Requires REPLICATE_API_TOKEN environment variable'}
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {/* Generation Model */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Survey Generation</label>
                          <select
                            value={settings.generation_model}
                            onChange={(e) => setSettings({ ...settings, generation_model: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-yellow-500 focus:border-yellow-500"
                          >
                            {generationModels.map((m) => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                          <p className="text-xs text-gray-500 mt-1">Generates surveys</p>
                        </div>

                        {/* Embedding Model */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Embeddings</label>
                          <select
                            value={settings.embedding_model}
                            disabled
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed"
                          >
                            {embeddingModels.map((m) => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                          <p className="text-xs text-gray-500 mt-1">Semantic search (Read-only)</p>
                        </div>

                        {/* RFQ Parsing Model */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">RFQ Parsing</label>
                          <select
                            value={rfqParsing.parsing_model}
                            disabled
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed"
                          >
                            {rfqModels.map((m) => (
                              <option key={m} value={m}>{m}</option>
                            ))}
                          </select>
                          <p className="text-xs text-gray-500 mt-1">Parses documents (Read-only)</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                {/* Quality Control & Review */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('qualityControl')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <ChartBarIcon className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">Quality Control & Review</h2>
                          <p className="text-gray-600 mt-1">Configure human review and quality control settings</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.qualityControl ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.qualityControl && (
                    <div className="p-6">
                      <div className="space-y-6">
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
                  )}
                </div>

                {/* Retrieval Weights Configuration */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('retrievalWeights')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <CogIcon className="w-6 h-6 text-gray-600" />
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">Retrieval Weights</h2>
                          <p className="text-gray-600 mt-1">Configure semantic search and retrieval preferences</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.retrievalWeights ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.retrievalWeights && (
                    <div className="p-6">
                      <RetrievalWeightsAccordion
                        weights={retrievalWeights}
                        onUpdateWeight={updateRetrievalWeight}
                        onError={(message) => addToast({
                          type: 'error',
                          title: 'Update Failed',
                          message,
                          duration: 5000
                        })}
                        onSuccess={(message) => addToast({
                          type: 'success',
                          title: 'Weights Updated',
                          message,
                          duration: 3000
                        })}
                      />
                    </div>
                  )}
                </div>

                {/* Methodology Rules */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('methodology')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <h2 className="text-2xl font-bold text-gray-900">Methodology Rules</h2>
                          <p className="text-gray-600 mt-1">Predefined research methodologies and their requirements</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.methodology ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.methodology && (
                    <div className="p-6">
                      <MethodologyRules
                        methodologies={methodologies}
                        onUpdateMethodologies={setMethodologies}
                        onFetchRules={fetchRules}
                        saving={saving}
                        setSaving={setSaving}
                        onShowDeleteConfirm={showDeleteConfirm}
                      />
                    </div>
                  )}
                </div>

                {/* Pillar Rules */}
                <PillarRulesSection
                  expandedSections={expandedSections}
                  onToggleSection={toggleSection}
                  onShowDeleteConfirm={showDeleteConfirm}
                />

                {/* System Prompt */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
                  <div 
                    className="bg-gray-50 border-b border-gray-200 px-6 py-6 cursor-pointer hover:bg-gray-100 transition-colors"
                    onClick={() => toggleSection('systemPrompt')}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h2 className="text-2xl font-bold text-gray-900">System Prompt</h2>
                            <span className="px-2 py-1 bg-gray-200 text-gray-700 rounded-full text-xs font-medium">ADVANCED</span>
                          </div>
                          <p className="text-gray-600 mt-1">Add custom instructions that will be injected into every AI prompt</p>
                        </div>
                      </div>
                      <ChevronDownIcon 
                        className={`w-6 h-6 text-gray-500 transition-transform duration-200 ${
                          expandedSections.systemPrompt ? 'rotate-180' : ''
                        }`} 
                      />
                    </div>
                  </div>
                  {expandedSections.systemPrompt && (
                    <div className="p-6">
                      <SystemPromptComponent
                        systemPrompt={systemPrompt}
                        onUpdateSystemPrompt={setSystemPrompt}
                        onShowDeleteConfirm={showDeleteConfirm}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Evaluation Tab */}
            {activeTab === 'evaluation' && (
              <div className="space-y-8">
                {/* Evaluation AI Models */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
                  <div className="flex items-center space-x-3 mb-6">
                    <BeakerIcon className="w-6 h-6 text-purple-600" />
                    <h2 className="text-xl font-semibold text-gray-900">Evaluation AI Models</h2>
                  </div>
                  
                  <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <p className="text-sm text-yellow-800 font-medium">Evaluation settings are read-only and cannot be modified</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Evaluation Model */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Evaluation Model</label>
                      <select
                        value={settings.evaluation_model}
                        disabled
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed"
                      >
                        {evaluationModels.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">Evaluates survey quality (Read-only)</p>
                    </div>
                  </div>
                </div>

                {/* Evaluation Settings */}
                <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
                  <div className="flex items-center space-x-3 mb-6">
                    <ChartBarIcon className="w-6 h-6 text-green-600" />
                    <h2 className="text-xl font-semibold text-gray-900">Evaluation Configuration</h2>
                  </div>
                  
                  <div className="space-y-6">
                    <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                      <p className="text-sm text-blue-800">
                        AI quality evaluation is available on-demand from the Survey Preview page. 
                        Click "Run Evaluation" to assess survey quality using pillar-based scoring.
                      </p>
                    </div>
                  </div>
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
                  className="px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors bg-red-600 hover:bg-red-700 focus:ring-red-500"
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