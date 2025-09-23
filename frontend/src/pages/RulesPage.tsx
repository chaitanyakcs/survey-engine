import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from '../components/Sidebar';
import { ExclamationTriangleIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { useAppStore } from '../store/useAppStore';
import { MethodologyRules } from '../components/MethodologyRules';
import { QualityRules } from '../components/QualityRules';
import { PillarRulesSection } from '../components/PillarRulesSection';
import { SystemPromptComponent } from '../components/SystemPrompt';

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
  const [loading, setLoading] = useState(true);
  const { mainContentClasses } = useSidebarLayout();
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    show: boolean;
    type: 'rule' | 'methodology' | 'system-prompt' | 'pillar-rule';
    title: string;
    message: string;
    onConfirm: () => void;
  } | null>(null);

  // Collapse/expand states for sections
  const [expandedSections, setExpandedSections] = useState({
    methodology: false,
    quality: false,
    pillars: false,
    systemPrompt: false
  });

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => {
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
      
      // Add timeout to prevent stuck requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const [methodologiesRes, qualityRes, systemPromptRes] = await Promise.all([
          fetch(`/api/v1/rules/methodologies?t=${timestamp}`, {
            method: 'GET',
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            signal: controller.signal
          }),
          fetch(`/api/v1/rules/quality-rules?t=${timestamp}`, {
            method: 'GET',
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            signal: controller.signal
          }),
          fetch(`/api/v1/rules/system-prompt?t=${timestamp}`, {
            method: 'GET',
            headers: {
              'Cache-Control': 'no-cache',
              'Pragma': 'no-cache'
            },
            signal: controller.signal
          })
        ]);

        clearTimeout(timeoutId);

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
      } catch (fetchError) {
        clearTimeout(timeoutId);
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          throw new Error('Request timed out. Please check your connection and try again.');
        }
        throw fetchError;
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
  }, []); // Remove addToast from dependencies to prevent infinite loop

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const toggleSection = (section: 'methodology' | 'quality' | 'pillars' | 'systemPrompt') => {
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

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <ToastContainer toasts={toasts} onRemove={removeToast} />
        <Sidebar currentView="rules" onViewChange={handleViewChange} />
        <div className={mainContentClasses}>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white">
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
        <div className="space-y-8">
          {/* Header */}
          <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
            <div className="px-6 py-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      Survey Rules & Guidelines
                    </h1>
                    <p className="text-gray-600">Configure methodology, quality standards, and AI instructions</p>
                  </div>
                </div>
              </div>
            </div>
          </header>
          
          <div className="p-6 space-y-8">

            {/* Methodology Rules */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div 
                className="bg-gradient-to-r from-yellow-500 via-amber-600 to-orange-600 px-6 py-6 text-white cursor-pointer"
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
                        // Add methodology logic will be handled by the component
                      }}
                      className="flex items-center space-x-2 px-4 py-2 bg-white/20 backdrop-blur-sm rounded-lg hover:bg-white/30 transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
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

            {/* Quality Rules */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden hover:shadow-xl transition-all duration-300">
              <div 
                className="bg-gradient-to-r from-yellow-500 via-amber-500 to-orange-500 px-6 py-6 text-white cursor-pointer"
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
                  <QualityRules
                    qualityRules={qualityRules}
                    onUpdateQualityRules={setQualityRules}
                    onFetchQualityRules={fetchQualityRules}
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
                className="bg-gradient-to-r from-yellow-500 via-amber-600 to-orange-600 px-6 py-6 text-white cursor-pointer"
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
                  <SystemPromptComponent
                    systemPrompt={systemPrompt}
                    onUpdateSystemPrompt={setSystemPrompt}
                    onShowDeleteConfirm={showDeleteConfirm}
                  />
                </div>
              )}
            </div>
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