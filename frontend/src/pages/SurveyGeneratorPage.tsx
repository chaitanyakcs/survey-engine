import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { RFQEditor } from '../components/RFQEditor';
import { EnhancedRFQApp } from '../components/EnhancedRFQApp';
import { ProgressStepper } from '../components/ProgressStepper';
import { HumanReviewPanel } from '../components/HumanReviewPanel';
import { Sidebar } from '../components/Sidebar';
import { ToastContainer } from '../components/Toast';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { ErrorBanner } from '../components/ErrorBanner';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { RecoveryAction } from '../types';

export const SurveyGeneratorPage: React.FC = () => {
  const { workflow, currentSurvey, toasts, removeToast, addToast, resetWorkflow, clearEnhancedRfqState } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings'>('survey');
  const [useEnhancedRFQ, setUseEnhancedRFQ] = useState<boolean>(false);
  const { mainContentClasses } = useSidebarLayout();

  // Debug logging
  React.useEffect(() => {
    console.log('🔍 [SurveyGeneratorPage] State update:', {
      workflowStatus: workflow.status,
      hasSurvey: !!currentSurvey,
      surveyId: currentSurvey?.survey_id,
      workflowSurveyId: workflow.survey_id,
      currentView
    });
  }, [workflow.status, currentSurvey, currentView]);

  // Fallback: Fetch survey if workflow is completed but survey is not loaded
  React.useEffect(() => {
    if (workflow.status === 'completed' && !currentSurvey && workflow.survey_id) {
      console.log('🔄 [SurveyGeneratorPage] Workflow completed but survey not loaded, fetching survey:', workflow.survey_id);
      useAppStore.getState().fetchSurvey(workflow.survey_id).catch((error) => {
        console.error('❌ [SurveyGeneratorPage] Failed to fetch survey:', error);
        // If survey doesn't exist, clean up the workflow state
        if (error.message.includes('404') || error.message.includes('Not Found')) {
          console.log('🧹 [SurveyGeneratorPage] Survey not found, cleaning up workflow state');
          resetWorkflow();
        }
      });
    }
  }, [workflow.status, currentSurvey, workflow.survey_id, resetWorkflow]);

  // Load survey from URL parameters if present
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const surveyId = urlParams.get('surveyId');
    const view = urlParams.get('view');
    
    console.log('🔍 [SurveyGeneratorPage] Checking URL parameters:', {
      currentUrl: window.location.href,
      search: window.location.search,
      surveyId: surveyId,
      view,
      hasCurrentSurvey: !!currentSurvey
    });
    
    // Handle view parameter
    if (view === 'golden-examples') {
      setCurrentView('golden-examples');
    } else {
      setCurrentView('survey');
    }
    
    if (surveyId && surveyId !== 'undefined' && surveyId !== 'null' && !currentSurvey) {
      console.log('📥 [SurveyGeneratorPage] Loading survey from URL parameter:', surveyId);
      useAppStore.getState().fetchSurvey(surveyId).then(async () => {
        // Load annotations after survey is loaded
        try {
          console.log('🔍 [SurveyGeneratorPage] Loading annotations for survey:', surveyId);
          await useAppStore.getState().loadAnnotations(surveyId);
          console.log('✅ [SurveyGeneratorPage] Annotations loaded successfully');
        } catch (error) {
          console.warn('⚠️ [SurveyGeneratorPage] Failed to load annotations:', error);
        }
      });
    } else if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
      console.log('⚠️ [SurveyGeneratorPage] No valid survey ID found in URL parameters');
    } else if (currentSurvey) {
      console.log('✅ [SurveyGeneratorPage] Survey already loaded, skipping fetch');
    }
  }, [currentSurvey]);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => {
    if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else {
      setCurrentView(view);
    }
  };

  return (
    <div className="min-h-screen bg-white flex">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Sidebar */}
      <Sidebar currentView={currentView} onViewChange={handleViewChange} />

      {/* Main Content */}
      <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
          <div className="px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-xl flex items-center justify-center shadow-lg">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                    Survey Generator
                  </h1>
                  <p className="text-gray-600">Create AI-powered surveys with advanced methodologies</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="py-4">
        {/* Survey Generator View */}
        {currentView === 'survey' && (
          <>
            {/* RFQ Input Phase */}
            {workflow.status === 'idle' && (
              <div>
                {/* RFQ Interface Toggle */}
                <div className="px-6 mb-4">
                  <div className="bg-white/70 backdrop-blur-sm rounded-2xl p-4 shadow-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-gray-900">Survey Builder Mode</h3>
                        <p className="text-sm text-gray-600">Choose between quick setup or comprehensive requirements builder</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => setUseEnhancedRFQ(false)}
                          className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                            !useEnhancedRFQ
                              ? 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          🚀 Quick Mode
                        </button>
                        <button
                          onClick={() => setUseEnhancedRFQ(true)}
                          className={`px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                            useEnhancedRFQ
                              ? 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          ✨ Enhanced Mode
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* RFQ Interface */}
                {useEnhancedRFQ ? <EnhancedRFQApp /> : <RFQEditor />}
              </div>
            )}

            {/* Generation Progress Phase */}
            {(workflow.status === 'started' || workflow.status === 'in_progress') && (
              <div>
                <div className="px-6 mb-6 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Generating Your Survey</h2>
                  <p className="text-gray-600">Our AI is creating your survey using advanced methodologies and best practices.</p>
                </div>
                
                <div className="px-6">
                  <ProgressStepper 
                    onShowSurvey={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to surveys section with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/surveys?id=${currentSurvey.survey_id}`;
                      }
                    }}
                    onShowSummary={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to summary with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/summary/${currentSurvey.survey_id}`;
                      }
                    }}
                    onCancelGeneration={() => {
                      console.log('🔄 [SurveyGeneratorPage] Canceling generation');
                      resetWorkflow();
                    }}
                  />
                </div>
              </div>
            )}

            {/* Human Review Phase */}
            {workflow.status === 'paused' && (
              <div>
                <div className="px-6 mb-6 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Human Review Required</h2>
                  <p className="text-gray-600">Please review the AI-generated system prompt before survey generation continues.</p>
                </div>

                <div className="px-6">
                  <ProgressStepper
                    onShowSurvey={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to surveys section with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/surveys?id=${currentSurvey.survey_id}`;
                      }
                    }}
                    onShowSummary={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to summary with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/summary/${currentSurvey.survey_id}`;
                      }
                    }}
                    onCancelGeneration={() => {
                      console.log('🔄 [SurveyGeneratorPage] Canceling generation');
                      resetWorkflow();
                    }}
                  />
                </div>
              </div>
            )}

            {/* Survey Completed Phase */}
            {workflow.status === 'completed' && (
              <div>
                <div className="px-6 mb-6 text-center">
                  <div className="mb-6">
                    <div className="w-16 h-16 bg-gradient-to-r from-yellow-500 to-amber-500 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-3">🎉 Your Survey is Ready!</h2>
                    <p className="text-lg text-gray-600 mb-2">We've crafted a professional survey tailored to your needs</p>
                    <p className="text-sm text-gray-500">Ready to collect valuable insights from your target audience</p>
                  </div>
                  
                  {/* Survey Loading State */}
                  {!currentSurvey && workflow.survey_id && (
                    <div className="mb-8">
                      <div className="inline-flex items-center px-6 py-3 bg-blue-50 text-blue-700 rounded-xl">
                        <div className="w-5 h-5 border-2 border-blue-500 rounded-full border-t-transparent animate-spin mr-3"></div>
                        <span className="font-medium">Loading your survey...</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Survey Not Found State */}
                  {!currentSurvey && !workflow.survey_id && (
                    <div className="mb-8">
                      <div className="inline-flex items-center px-6 py-3 bg-yellow-50 text-yellow-700 rounded-xl">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <span className="font-medium">Survey generation completed but survey data is not available. Please try refreshing the page.</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Primary Action Button - View Survey */}
                  <div className="mt-8">
                    <button
                      onClick={() => {
                        if (currentSurvey?.survey_id) {
                          console.log('🔍 [SurveyGeneratorPage] Navigating to surveys section with survey ID:', currentSurvey.survey_id);
                          window.location.href = `/surveys?id=${currentSurvey.survey_id}`;
                        }
                      }}
                      className="inline-flex items-center px-10 py-5 bg-gradient-to-r from-yellow-500 to-amber-500 text-white rounded-2xl font-bold text-xl shadow-2xl hover:shadow-yellow-300 transform hover:scale-105 transition-all duration-300"
                    >
                      <svg className="w-7 h-7 mr-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      Take a Look at Your Survey
                      <span className="ml-3 text-emerald-200 text-2xl">✨</span>
                    </button>
                  </div>
                  
                  {/* Secondary Action Button - Generate Another */}
                  <div className="mt-6">
                    <button
                      onClick={() => {
                        console.log('🔄 [SurveyGeneratorPage] Starting new survey');
                        resetWorkflow();
                      }}
                      className="inline-flex items-center px-8 py-4 bg-white border-2 border-gray-200 text-gray-700 rounded-xl font-semibold text-lg hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 transition-all duration-200"
                    >
                      <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Create Another Survey
                    </button>
                  </div>
                  
                  {/* Success Stats */}
                  <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 px-6">
                    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-600">✓</div>
                      <div className="text-sm font-medium text-yellow-800 mt-1">Quality Assured</div>
                      <div className="text-xs text-yellow-600">5-pillar evaluation</div>
                    </div>
                    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-600">🎯</div>
                      <div className="text-sm font-medium text-yellow-800 mt-1">Tailored</div>
                      <div className="text-xs text-yellow-600">To your needs</div>
                    </div>
                    <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-yellow-600">⚡</div>
                      <div className="text-sm font-medium text-yellow-800 mt-1">Ready to Deploy</div>
                      <div className="text-xs text-yellow-600">Start collecting data</div>
                    </div>
                  </div>
                </div>
                
                
              </div>
            )}

            {/* Enhanced Error State */}
            {workflow.status === 'failed' && workflow.detailedError && (
              <div className="px-6">
                <ErrorDisplay
                  error={workflow.detailedError}
                  onRecoveryAction={(action: RecoveryAction) => {
                    switch (action) {
                      case 'retry':
                        addToast({
                          type: 'info',
                          title: 'Retrying Generation',
                          message: 'Restarting survey generation with same parameters.',
                          duration: 3000
                        });
                        resetWorkflow();
                        break;

                      case 'return_to_form':
                        addToast({
                          type: 'info',
                          title: 'Returning to Form',
                          message: 'Please review and modify your RFQ before trying again.',
                          duration: 3000
                        });
                        resetWorkflow();
                        break;

                      case 'contact_support':
                        window.open('mailto:support@surveyengine.com?subject=Survey Generation Error&body=Debug Code: ' + encodeURIComponent(JSON.stringify(workflow.detailedError?.debugInfo || {})), '_blank');
                        break;

                      case 'refresh_page':
                        window.location.reload();
                        break;

                      default:
                        console.log('Recovery action not implemented:', action);
                    }
                  }}
                  onRetry={() => {
                    addToast({
                      type: 'info',
                      title: 'Retrying Generation',
                      message: 'Restarting survey generation.',
                      duration: 3000
                    });
                    resetWorkflow();
                  }}
                  onDismiss={() => {
                    clearEnhancedRfqState();
                    resetWorkflow();
                    window.location.href = '/';
                  }}
                />
              </div>
            )}

            {/* Fallback Error State (for errors without detailed info) */}
            {workflow.status === 'failed' && !workflow.detailedError && (
              <div className="px-6">
                <ErrorBanner
                  error={{
                    code: 'UNK_001' as any,
                    severity: 'high' as any,
                    message: workflow.error || 'Unknown error occurred',
                    userMessage: workflow.error || 'An unexpected error occurred during survey generation. Please try again.',
                    debugInfo: {
                      sessionId: 'legacy',
                      timestamp: new Date().toISOString(),
                      errorCode: 'UNK_001' as any,
                      userAgent: navigator.userAgent
                    },
                    retryable: true,
                    suggestedActions: ['retry' as any, 'return_to_form' as any]
                  }}
                  onRetry={() => {
                    addToast({
                      type: 'info',
                      title: 'Retrying Generation',
                      message: 'Restarting survey generation.',
                      duration: 3000
                    });
                    resetWorkflow();
                  }}
                  onDismiss={() => {
                    clearEnhancedRfqState();
                    resetWorkflow();
                    window.location.href = '/';
                  }}
                />
              </div>
            )}
          </>
        )}
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-300 mt-16">
          <div className="px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-500">
              Survey Generation Engine - Powered by AI & Golden Standard Examples
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};
