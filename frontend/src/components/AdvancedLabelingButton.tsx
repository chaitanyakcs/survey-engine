import React, { useState } from 'react';
import { SparklesIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface AdvancedLabelingButtonProps {
  surveyId: string;
  onLabelingComplete?: (results: any) => void;
  disabled?: boolean;
  className?: string;
}

interface LabelingResults {
  survey_id: string;
  processed_questions: number;
  processed_sections: number;
  updated_survey: boolean;
  errors: string[];
}

const AdvancedLabelingButton: React.FC<AdvancedLabelingButtonProps> = ({
  surveyId,
  onLabelingComplete,
  disabled = false,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [results, setResults] = useState<LabelingResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAdvancedLabeling = async () => {
    if (!surveyId || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`/api/annotations/survey/${surveyId}/advanced-labeling`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to apply advanced labeling: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.results);
      setShowResults(true);

      if (onLabelingComplete) {
        onLabelingComplete(data.results);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply advanced labeling';
      setError(errorMessage);
      console.error('Advanced labeling error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const closeResults = () => {
    setShowResults(false);
    setResults(null);
    setError(null);
  };

  if (showResults || error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {error ? 'Labeling Failed' : 'Advanced Labeling Complete'}
            </h3>
            <button
              onClick={closeResults}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>
          </div>

          {error ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-red-600">
                <ExclamationTriangleIcon className="w-5 h-5" />
                <span className="font-medium">Error occurred</span>
              </div>
              <p className="text-sm text-gray-600">{error}</p>
              <button
                onClick={closeResults}
                className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Close
              </button>
            </div>
          ) : results ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircleIcon className="w-5 h-5" />
                <span className="font-medium">Successfully applied advanced labeling</span>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Questions processed:</span>
                  <span className="font-medium">{results.processed_questions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Sections processed:</span>
                  <span className="font-medium">{results.processed_sections}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Survey updated:</span>
                  <span className={`font-medium ${results.updated_survey ? 'text-green-600' : 'text-gray-600'}`}>
                    {results.updated_survey ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>

              {results.errors && results.errors.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm font-medium text-yellow-600 mb-2">Warnings:</div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    {results.errors.map((error, index) => (
                      <div key={index} className="text-xs text-yellow-700">{error}</div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={closeResults}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Refresh Page
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={handleAdvancedLabeling}
      disabled={disabled || isLoading}
      className={`inline-flex items-center px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
        disabled || isLoading
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : 'bg-purple-600 text-white hover:bg-purple-700 hover:shadow-md active:transform active:scale-95'
      } ${className}`}
    >
      <SparklesIcon className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
      {isLoading ? 'Applying Labels...' : 'Apply Advanced Labeling'}
    </button>
  );
};

export default AdvancedLabelingButton;