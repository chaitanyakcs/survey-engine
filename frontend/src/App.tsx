import React, { useState } from 'react';
import { useAppStore } from './store/useAppStore';
import { RFQEditor } from './components/RFQEditor';
import { ProgressStepper } from './components/ProgressStepper';
import { SurveyPreview } from './components/SurveyPreview';
import { GoldenExamplesManager } from './components/GoldenExamplesManager';
import { ToastContainer } from './components/Toast';

function App() {
  const { workflow, currentSurvey, toasts, removeToast } = useAppStore();
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples'>('survey');

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

        {/* Survey Preview Phase */}
        {workflow.status === 'completed' && currentSurvey && (
          <div>
            <div className="max-w-6xl mx-auto px-4 mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-black mb-2">Survey Preview</h2>
                  <p className="text-gray-600">Review and refine your generated survey before finalizing.</p>
                </div>
                <button 
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 text-sm bg-black text-white rounded hover:bg-gray-800 transition-colors"
                >
                  Start New Survey
                </button>
              </div>
            </div>
            <SurveyPreview />
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
}

export default App;