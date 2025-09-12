import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { RFQEditor } from '../components/RFQEditor';
import { ProgressStepper } from '../components/ProgressStepper';
import { SurveyPreview } from '../components/SurveyPreview';
import { Sidebar } from '../components/Sidebar';
import { ToastContainer } from '../components/Toast';
import { useSidebarLayout } from '../hooks/useSidebarLayout';

export const SurveyGeneratorPage: React.FC = () => {
  const { workflow, currentSurvey, toasts, removeToast, addToast } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples' | 'rules' | 'surveys'>('survey');
  const { mainContentClasses } = useSidebarLayout();

  // Debug logging
  React.useEffect(() => {
    console.log('🔍 [SurveyGeneratorPage] State update:', {
      workflowStatus: workflow.status,
      hasSurvey: !!currentSurvey,
      surveyId: currentSurvey?.survey_id,
      currentView
    });
  }, [workflow.status, currentSurvey, currentView]);

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
      useAppStore.getState().fetchSurvey(surveyId);
    } else if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
      console.log('⚠️ [SurveyGeneratorPage] No valid survey ID found in URL parameters');
    } else if (currentSurvey) {
      console.log('✅ [SurveyGeneratorPage] Survey already loaded, skipping fetch');
    }
  }, [currentSurvey]);

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys') => {
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
    <div className="min-h-screen bg-gray-50 flex">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Sidebar */}
      <Sidebar currentView={currentView} onViewChange={handleViewChange} />

      {/* Main Content */}
      <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>

        <main className="py-4">
        {/* Survey Generator View */}
        {currentView === 'survey' && (
          <>
            {/* RFQ Input Phase */}
            {workflow.status === 'idle' && (
              <RFQEditor />
            )}

            {/* Generation Progress Phase */}
            {(workflow.status === 'started' || workflow.status === 'in_progress') && (
              <div>
                <div className="max-w-4xl mx-auto px-4 mb-8 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Generating Your Survey</h2>
                  <p className="text-gray-600">Our AI is creating your survey using advanced methodologies and best practices.</p>
                </div>
                
                <div className="max-w-4xl mx-auto px-4">
                  <ProgressStepper 
                    onShowSurvey={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to preview with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/preview?surveyId=${currentSurvey.survey_id}`;
                      }
                    }}
                    onCancelGeneration={() => {
                      console.log('🔄 [SurveyGeneratorPage] Canceling generation and reloading');
                      window.location.reload();
                    }}
                  />
                </div>
              </div>
            )}

            {/* Survey Completed Phase */}
            {workflow.status === 'completed' && currentSurvey && (
              <div>
                <div className="max-w-6xl mx-auto px-4 mb-8 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Survey Generated Successfully!</h2>
                  <p className="text-gray-600">Your survey has been created and is ready for review.</p>
                  <p className="text-sm text-gray-500 mt-1">Survey ID: {currentSurvey.survey_id}</p>
                </div>
                
                {/* Progress Stepper with Action Buttons */}
                <div className="max-w-4xl mx-auto px-4 mb-8">
                  <ProgressStepper 
                    onShowSurvey={() => {
                      if (currentSurvey?.survey_id) {
                        console.log('🔍 [SurveyGeneratorPage] Navigating to preview with survey ID:', currentSurvey.survey_id);
                        window.location.href = `/preview?surveyId=${currentSurvey.survey_id}`;
                      }
                    }}
                    onCancelGeneration={() => {
                      console.log('🔄 [SurveyGeneratorPage] Starting new survey');
                      window.location.reload();
                    }}
                  />
                </div>
                
              </div>
            )}

            {/* Error State */}
            {workflow.status === 'failed' && (
              <div className="max-w-4xl mx-auto px-4 text-center">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <div className="flex items-center justify-center mb-4">
                    <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h2 className="text-lg font-semibold text-red-900 mb-2">Generation Failed</h2>
                  <p className="text-red-700 mb-4">
                    {workflow.error || 'An error occurred during survey generation.'}
                  </p>
                  <button
                    onClick={() => {
                      addToast({
                        type: 'info',
                        title: 'Restarting Generation',
                        message: 'Reloading the page to start a new survey generation.',
                        duration: 3000
                      });
                      setTimeout(() => window.location.reload(), 1000);
                    }}
                    className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Try Again
                  </button>
                </div>
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
