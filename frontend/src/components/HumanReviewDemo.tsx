import React, { useState } from 'react';
import { HumanReviewPanel } from './HumanReviewPanel';

export const HumanReviewDemo: React.FC = () => {
  const [showDemo, setShowDemo] = useState(false);

  if (!showDemo) {
    return (
      <div className="p-8">
        <button
          onClick={() => setShowDemo(true)}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Demo Human Review Interface
        </button>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Left Panel - Demo Info */}
      <div className="w-1/2 border-r border-gray-200/50 bg-white/40 backdrop-blur-sm p-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Human Review Demo</h2>
        <div className="space-y-4 text-sm text-gray-700">
          <p>This demonstrates the human review interface that appears when:</p>
          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>Human prompt review is enabled in settings</li>
            <li>The survey generation reaches the human review step</li>
            <li>An AI-generated system prompt needs expert validation</li>
          </ul>
          <p className="mt-6 font-medium">Features demonstrated:</p>
          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>AI-generated prompt display with expand/collapse</li>
            <li>Original RFQ context for reference</li>
            <li>Review criteria checklist</li>
            <li>Approval/rejection workflow</li>
            <li>Review notes and feedback</li>
            <li>Status tracking and completion states</li>
          </ul>
          <button
            onClick={() => setShowDemo(false)}
            className="mt-6 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Back to Survey Generator
          </button>
        </div>
      </div>

      {/* Right Panel - Human Review Interface */}
      <div className="w-1/2 bg-white/60 backdrop-blur-sm">
        <div className="h-full overflow-y-auto">
          <div className="p-8">
            <HumanReviewPanel 
              isActive={true}
              surveyId="demo-survey-123"
            />
          </div>
        </div>
      </div>
    </div>
  );
};