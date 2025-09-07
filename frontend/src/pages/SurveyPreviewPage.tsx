import React from 'react';
import { SurveyPreview } from '../components/SurveyPreview';

export const SurveyPreviewPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-black">Survey Preview</h1>
              <p className="text-sm text-gray-600">Review and refine your generated survey</p>
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Survey Generation Engine - Powered by AI & Golden Standard Examples
          </p>
        </div>
      </footer>
    </div>
  );
};
