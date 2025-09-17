import React from 'react';
import { SurveyPreview } from '../components/SurveyPreview';

export const SurveyPreviewPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-30 shadow-sm">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Survey Preview
                </h1>
                <p className="text-gray-600">Review and refine your generated survey</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <a
                href="/"
                className="px-4 py-2 text-sm bg-gray-200 text-black rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Generator
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="py-8">
        <SurveyPreview />
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
  );
};











