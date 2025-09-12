import React from 'react';
import { XMarkIcon, LightBulbIcon, DocumentTextIcon, ChartBarIcon, CogIcon } from '@heroicons/react/24/outline';

interface AIEngineInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AIEngineInfoModal: React.FC<AIEngineInfoModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <DocumentTextIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">AI Survey Engine</h2>
                <p className="text-sm text-gray-500">v1.0.0 - Intelligent Learning System</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-8">
          {/* Overview */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <LightBulbIcon className="h-6 w-6 text-blue-600 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">How AI Survey Engine Learns</h3>
                <p className="text-gray-700 leading-relaxed">
                  The AI Survey Engine continuously improves through <strong>Reference Examples</strong> and user interactions. 
                  Every action you take in the dashboard contributes to making the AI smarter and more accurate.
                </p>
              </div>
            </div>
          </div>

          {/* Learning Mechanisms */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Reference Examples */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <DocumentTextIcon className="h-5 w-5 text-yellow-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Reference Examples</h3>
              </div>
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  <strong>What they are:</strong> Perfectly structured survey examples created from your RFQ documents.
                </p>
                <p className="text-sm text-gray-600">
                  <strong>How you create them:</strong> Upload DOCX → AI parses → You refine → Save as Golden Example
                </p>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>Learning Impact:</strong> Each Golden Example teaches the AI what constitutes a "perfect" survey 
                    for specific research contexts and methodologies.
                  </p>
                </div>
              </div>
            </div>

            {/* Dashboard Actions */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <ChartBarIcon className="h-5 w-5 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Dashboard Actions</h3>
              </div>
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  <strong>Every interaction teaches the AI:</strong>
                </p>
                <ul className="text-sm text-gray-600 space-y-1 ml-4">
                  <li>• Creating new Reference Examples</li>
                  <li>• Editing and refining AI-generated surveys</li>
                  <li>• Selecting specific methodologies</li>
                  <li>• Adjusting question structures</li>
                </ul>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-sm text-green-800">
                    <strong>Result:</strong> The AI becomes more accurate and context-aware with each use.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Technical Learning Process */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <CogIcon className="h-5 w-5 text-gray-600" />
              <span>Technical Learning Process</span>
            </h3>
            
            <div className="grid md:grid-cols-3 gap-4">
              {/* Step 1 */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-blue-600">1</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">Data Collection</h4>
                </div>
                <p className="text-sm text-gray-600">
                  Your Reference Examples and corrections are stored as high-quality training data with quality scores and methodology tags.
                </p>
              </div>

              {/* Step 2 */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-blue-600">2</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">Pattern Recognition</h4>
                </div>
                <p className="text-sm text-gray-600">
                  The system analyzes successful patterns, question structures, and methodology applications to identify what works best.
                </p>
              </div>

              {/* Step 3 */}
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-bold text-blue-600">3</span>
                  </div>
                  <h4 className="font-semibold text-gray-900">Model Enhancement</h4>
                </div>
                <p className="text-sm text-gray-600">
                  GPT-5 prompts are refined using your examples, making future survey generation more accurate and contextually appropriate.
                </p>
              </div>
            </div>
          </div>

          {/* Beyond LLM Calls */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Beyond Simple LLM Calls</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Intelligent Processing Pipeline</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Advanced DOCX text extraction and cleaning</li>
                  <li>• Multi-method JSON parsing with regex fallbacks</li>
                  <li>• Pydantic schema validation with auto-correction</li>
                  <li>• Graceful error handling and recovery</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Rule-Based Intelligence</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• 85 methodology rules for research guidance</li>
                  <li>• 84 quality rules for survey validation</li>
                  <li>• Dynamic rule refinement based on usage</li>
                  <li>• Context-aware prompt adaptation</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">Start Teaching the AI Today!</h3>
            <p className="text-blue-100 mb-4">
              Every survey you create, edit, or save as a Golden Example makes the AI smarter. 
              The more you use it, the better it becomes at understanding your specific needs.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                Upload DOCX files
              </span>
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                Create Reference Examples
              </span>
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                Refine AI output
              </span>
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full text-sm">
                Watch it improve
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
            >
              Got it, let's start!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIEngineInfoModal;


