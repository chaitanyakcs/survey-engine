import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { RFQEditor } from '../components/RFQEditor';
import { ProgressStepper } from '../components/ProgressStepper';
import { GoldenExamplesManager } from '../components/GoldenExamplesManager';
import { ToastContainer } from '../components/Toast';

export const SurveyGeneratorPage: React.FC = () => {
  const { workflow, currentSurvey, toasts, removeToast } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples'>('survey');
  const [showManualRedirect, setShowManualRedirect] = useState(false);

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

  // Show manual redirect button if survey is completed but auto-redirect hasn't happened
  React.useEffect(() => {
    if (workflow.status === 'completed' && currentSurvey && currentSurvey.survey_id) {
      console.log('⏰ [SurveyGeneratorPage] Survey completed, setting up manual redirect fallback');
      
      const timer = setTimeout(() => {
        console.log('⚠️ [SurveyGeneratorPage] Auto-redirect timeout, showing manual redirect button');
        setShowManualRedirect(true);
      }, 3000); // Show manual redirect after 3 seconds

      return () => clearTimeout(timer);
    } else {
      setShowManualRedirect(false);
    }
  }, [workflow.status, currentSurvey]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
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

      <main className="py-8">
        {/* Golden Examples Manager View */}
        {currentView === 'golden-examples' && (
          <GoldenExamplesManager />
        )}
        
        {/* Survey Generator View */}
        {currentView === 'survey' && (
          <>
            {/* RFQ Input Phase */}
            {workflow.status === 'idle' && (
              <div>
                <div className="max-w-4xl mx-auto px-4 mb-8">
                  <h2 className="text-xl font-semibold text-black mb-2">Create New Survey</h2>
                  <p className="text-gray-600">Enter your RFQ details to generate a professional market research survey.</p>
                </div>
                <RFQEditor />
              </div>
            )}

            {/* Generation Progress Phase */}
            {(workflow.status === 'started' || workflow.status === 'in_progress') && (
              <div>
                <div className="max-w-4xl mx-auto px-4 mb-8 text-center">
                  <h2 className="text-xl font-semibold text-black mb-2">Generating Your Survey</h2>
                  <p className="text-gray-600">Our AI is creating your survey using advanced methodologies and best practices.</p>
                </div>
                
                <div className="max-w-4xl mx-auto px-4">
                  <ProgressStepper />
                </div>

                {/* Cancel Button */}
                <div className="max-w-4xl mx-auto px-4 mt-8 text-center">
                  <button 
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-black transition-colors"
                  >
                    Cancel Generation
                  </button>
                </div>
              </div>
            )}

            {/* Survey Completed Phase */}
            {workflow.status === 'completed' && currentSurvey && (
              <div>
                <div className="max-w-6xl mx-auto px-4 mb-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-black mb-2">Survey Generated Successfully!</h2>
                      <p className="text-gray-600">Your survey has been created and is ready for review.</p>
                      <p className="text-sm text-gray-500 mt-1">Survey ID: {currentSurvey.survey_id}</p>
                    </div>
                    <div className="flex space-x-3">
                      <a
                        href={`/preview?surveyId=${currentSurvey.survey_id}`}
                        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        onClick={() => console.log('🔗 [SurveyGeneratorPage] Manual preview link clicked:', currentSurvey.survey_id)}
                      >
                        View Full Preview
                      </a>
                      <button 
                        onClick={() => window.location.reload()}
                        className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                      >
                        Start New Survey
                      </button>
                    </div>
                  </div>
                  
                  {/* Manual Redirect Fallback */}
                  {showManualRedirect && (
                    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3">
                          <p className="text-sm text-yellow-800">
                            Auto-redirect didn't work. Click below to go to preview:
                          </p>
                          <button
                            onClick={() => {
                              console.log('🔄 [SurveyGeneratorPage] Manual redirect triggered');
                              window.location.href = `/preview?surveyId=${currentSurvey.survey_id}`;
                            }}
                            className="mt-2 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors text-sm"
                          >
                            Go to Preview Now
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Quick Preview */}
                <div className="max-w-4xl mx-auto px-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {currentSurvey.title}
                    </h3>
                    <p className="text-gray-600 mb-4">
                      {currentSurvey.description}
                    </p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                      <span>⏱️ ~{currentSurvey.estimated_time || 0} minutes</span>
                      <span>📊 {currentSurvey.questions?.length || 0} questions</span>
                      <span>🎯 {Math.round((currentSurvey.confidence_score || 0) * 100)}% confidence</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(currentSurvey.methodologies || []).map((method) => (
                        <span 
                          key={method}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                        >
                          {method.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
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
