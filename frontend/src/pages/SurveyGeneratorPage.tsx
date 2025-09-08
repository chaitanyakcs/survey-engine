import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { RFQEditor } from '../components/RFQEditor';
import { ProgressStepper } from '../components/ProgressStepper';
import { GoldenExamplesManager } from '../components/GoldenExamplesManager';
import { SurveyPreview } from '../components/SurveyPreview';
import { ToastContainer } from '../components/Toast';

export const SurveyGeneratorPage: React.FC = () => {
  const { workflow, currentSurvey, toasts, removeToast } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples'>('survey');

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
    
    console.log('🔍 [SurveyGeneratorPage] Checking URL parameters:', {
      currentUrl: window.location.href,
      search: window.location.search,
      surveyId: surveyId,
      hasCurrentSurvey: !!currentSurvey
    });
    
    if (surveyId && surveyId !== 'undefined' && surveyId !== 'null' && !currentSurvey) {
      console.log('📥 [SurveyGeneratorPage] Loading survey from URL parameter:', surveyId);
      useAppStore.getState().fetchSurvey(surveyId);
    } else if (!surveyId || surveyId === 'undefined' || surveyId === 'null') {
      console.log('⚠️ [SurveyGeneratorPage] No valid survey ID found in URL parameters');
    } else if (currentSurvey) {
      console.log('✅ [SurveyGeneratorPage] Survey already loaded, skipping fetch');
    }
  }, [currentSurvey]);


  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-black">Survey Generation Engine</h1>
              <p className="text-sm text-gray-600">Transform RFQs into professional surveys with AI</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Navigation */}
              <nav className="flex space-x-4">
                <button
                  onClick={() => setCurrentView('survey')}
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentView === 'survey'
                      ? 'bg-gray-200 text-black'
                      : 'text-gray-600 hover:text-black'
                  }`}
                >
                  Survey Generator
                </button>
                <button
                  onClick={() => setCurrentView('golden-examples')}
                  className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    currentView === 'golden-examples'
                      ? 'bg-gray-200 text-black'
                      : 'text-gray-600 hover:text-black'
                  }`}
                >
                  Golden Examples
                </button>
                <a
                  href="/rules"
                  className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-black transition-colors"
                >
                  Rules
                </a>
              </nav>
              
              {/* Status Badge */}
              {workflow.status !== 'idle' && currentView === 'survey' && (
                <div className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${workflow.status === 'completed' ? 'bg-green-100 text-green-800' :
                    workflow.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-200 text-gray-800'}
                `}>
                  {workflow.status === 'in_progress' ? 'Generating...' : 
                   workflow.status === 'completed' ? 'Generated' :
                   workflow.status === 'failed' ? 'Failed' : workflow.status}
                </div>
              )}

              {/* Preview Button - only show when survey is completed */}
              {workflow.status === 'completed' && currentSurvey && (
                <a
                  href="/preview"
                  className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  View Preview
                </a>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="py-4">
        {/* Golden Examples Manager View */}
        {currentView === 'golden-examples' && (
          <GoldenExamplesManager />
        )}
        
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
                  <h2 className="text-lg font-semibold text-red-900 mb-2">Generation Failed</h2>
                  <p className="text-red-700 mb-4">
                    {workflow.error || 'An error occurred during survey generation.'}
                  </p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  >
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Survey Generation Engine - Powered by AI & Golden Standard Examples
          </p>
        </div>
      </footer>

    </div>
  );
};
