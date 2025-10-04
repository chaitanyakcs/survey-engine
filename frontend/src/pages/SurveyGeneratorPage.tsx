import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
// RFQEditor removed - only using EnhancedRFQApp
import { EnhancedRFQApp } from '../components/EnhancedRFQApp';
import { ProgressStepper } from '../components/ProgressStepper';
import { Sidebar } from '../components/Sidebar';
import { ToastContainer } from '../components/Toast';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { ErrorBanner } from '../components/ErrorBanner';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { RecoveryAction } from '../types';


export const SurveyGeneratorPage: React.FC = () => {
  const { workflow, currentSurvey, toasts, removeToast, addToast, resetWorkflow, clearEnhancedRfqState, loadPillarScoresAsync } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings'>('survey');
  const { mainContentClasses } = useSidebarLayout();

  // Debug logging (reduced frequency to prevent render loops)
  React.useEffect(() => {
    const surveyId = currentSurvey?.survey_id;
    console.log('🔍 [SurveyGeneratorPage] State update:', {
      workflowStatus: workflow.status,
      hasSurvey: !!currentSurvey,
      surveyId: surveyId,
      workflowSurveyId: workflow.survey_id,
      currentView
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow.status, currentSurvey?.survey_id, workflow.survey_id, currentView]); // Only watch survey_id, not entire object


  // Fallback: Fetch survey if workflow is completed but survey is not loaded
  React.useEffect(() => {
    // Only attempt to fetch if survey hasn't failed before
    if (workflow.status === 'completed' && !currentSurvey && workflow.survey_id && !workflow.survey_fetch_failed) {
      console.log('🔄 [SurveyGeneratorPage] Workflow completed but survey not loaded, fetching survey:', workflow.survey_id);
      useAppStore.getState().fetchSurvey(workflow.survey_id).then(() => {
        // After successfully fetching the survey, load pillar scores with a small delay
        console.log('🏛️ [SurveyGeneratorPage] Survey fetched, loading pillar scores');
        if (workflow.survey_id) {
          // Add a small delay to prevent API call conflicts
          setTimeout(() => {
            if (workflow.survey_id) {
              loadPillarScoresAsync(workflow.survey_id).catch((error) => {
                console.warn('⚠️ [SurveyGeneratorPage] Failed to load pillar scores after fallback fetch:', error);
              });
            }
          }, 2000); // Increased delay to 2 seconds to prevent overwhelming backend
        }
      }).catch((error) => {
        console.error('❌ [SurveyGeneratorPage] Failed to fetch survey:', error);
        // If survey doesn't exist, clean up the workflow state
        if (error.message.includes('404') || error.message.includes('Not Found')) {
          console.log('🧹 [SurveyGeneratorPage] Survey not found, cleaning up workflow state');
          resetWorkflow();
        }
      });
    }
  }, [workflow.status, currentSurvey, workflow.survey_id, workflow.survey_fetch_failed, resetWorkflow, loadPillarScoresAsync]);

  // Load survey from URL parameters if present (run once on mount)
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const surveyId = urlParams.get('surveyId');
    const view = urlParams.get('view');
    const currentSurveyId = currentSurvey?.survey_id;
    
    console.log('🔍 [SurveyGeneratorPage] Checking URL parameters:', {
      currentUrl: window.location.href,
      search: window.location.search,
      surveyId: surveyId,
      view,
      hasCurrentSurvey: !!currentSurvey,
      currentSurveyId: currentSurveyId
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
      // Only log this warning if we're not in a completed workflow state
      if (workflow.status !== 'completed') {
        console.log('⚠️ [SurveyGeneratorPage] No valid survey ID found in URL parameters');
      }
    } else if (currentSurvey) {
      console.log('✅ [SurveyGeneratorPage] Survey already loaded, skipping fetch');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSurvey?.survey_id, workflow.status]); // Only watch survey_id, not the entire object

  // Load pillar scores asynchronously when survey is available (non-blocking)
  React.useEffect(() => {
    if (currentSurvey && !currentSurvey.pillar_scores) {
      console.log('🏛️ [SurveyGeneratorPage] Loading pillar scores in background');
      loadPillarScoresAsync(currentSurvey.survey_id).catch((error) => {
        console.warn('⚠️ [SurveyGeneratorPage] Background pillar scores loading failed:', error);
        // Don't show error to user - this is a background operation
      });
    }
  }, [currentSurvey, loadPillarScoresAsync]);

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
              
              <div className="flex items-center space-x-4">
                {/* Progress Status and Cancel - Only show during generation */}
                {(workflow.status === 'started' || workflow.status === 'in_progress') && (
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center px-4 py-2 bg-gradient-to-r from-yellow-100 to-amber-100 text-amber-800 rounded-lg border border-amber-200">
                      <div className="w-2 h-2 bg-gradient-to-r from-yellow-500 to-amber-600 rounded-full animate-pulse mr-2" />
                      <span className="text-sm font-medium">Generating Survey...</span>
                    </div>
                    <button
                      onClick={async () => {
                        console.log('🔄 [SurveyGeneratorPage] Canceling generation');
                        await resetWorkflow();
                      }}
                      className="inline-flex items-center px-4 py-2 rounded-lg font-medium transition-all duration-200 bg-red-100 hover:bg-red-200 text-red-700 border border-red-300 hover:border-red-400"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="py-2">
        {/* Survey Generator View */}
        {currentView === 'survey' && (
          <>
            {/* RFQ Input Phase */}
            {workflow.status === 'idle' && (
              <div>
                {/* RFQ Interface */}
                <EnhancedRFQApp key="enhanced-rfq" />
              </div>
            )}

            {/* Generation Progress Phase */}
            {(workflow.status === 'started' || workflow.status === 'in_progress') && (
              <div className="px-6">
                <ProgressStepper 
                  onCancelGeneration={() => {
                    console.log('🔄 [SurveyGeneratorPage] Canceling generation');
                    resetWorkflow();
                  }}
                />
              </div>
            )}

            {/* Human Review Phase */}
            {workflow.status === 'paused' && (
              <div>
                <div className="px-6 mb-4 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Human Review Required</h2>
                  <p className="text-gray-600">Please review the AI-generated system prompt before survey generation continues.</p>
                </div>

                <div className="px-6">
                  <ProgressStepper
                    onCancelGeneration={() => {
                      console.log('🔄 [SurveyGeneratorPage] Canceling generation');
                      resetWorkflow();
                    }}
                  />
                </div>
              </div>
            )}

            {/* Survey Completion Phase */}
            {workflow.status === 'completed' && (
              <div className="px-6">
                <ProgressStepper
                  onCancelGeneration={() => {
                    console.log('🔄 [SurveyGeneratorPage] Resetting workflow');
                    resetWorkflow();
                  }}
                />
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
