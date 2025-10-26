import React, { useState, useEffect, useCallback } from 'react';
import { XMarkIcon, ClockIcon, DocumentTextIcon, ArrowTopRightOnSquareIcon } from '@heroicons/react/24/outline';
import { apiService } from '../services/api';
import { QuestionUsage } from '../types';

interface QuestionUsageModalProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: string;
  questionText: string;
}

export const QuestionUsageModal: React.FC<QuestionUsageModalProps> = ({
  isOpen,
  onClose,
  questionId,
  questionText
}) => {
  const [usageHistory, setUsageHistory] = useState<QuestionUsage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadUsageHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const usage = await apiService.getGoldenQuestionUsage(questionId);
      setUsageHistory(usage);
    } catch (err) {
      console.error('Failed to load usage history:', err);
      setError('Failed to load usage history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [questionId]);

  useEffect(() => {
    if (isOpen && questionId) {
      loadUsageHistory();
    }
  }, [isOpen, questionId, loadUsageHistory]);

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  const handleNavigateToSurvey = (surveyId: string) => {
    window.location.href = `/surveys/${surveyId}`;
  };

  const handleNavigateToGoldenPair = (goldenPairId: string) => {
    window.location.href = `/golden-examples/${goldenPairId}/edit`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998] p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Usage History</h2>
            <p className="text-sm text-gray-600 line-clamp-2">{questionText}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="relative mb-4">
                  <div className="w-16 h-16 border-4 border-yellow-200 rounded-full"></div>
                  <div className="absolute top-0 left-0 w-16 h-16 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
                </div>
                <p className="text-gray-600">Loading usage history...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <XMarkIcon className="w-8 h-8 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading History</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <button
                  onClick={loadUsageHistory}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          ) : usageHistory.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <ClockIcon className="w-12 h-12 text-yellow-600" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-3">Not Used Yet</h3>
                <p className="text-gray-600 text-lg">
                  This question hasn't been used in any surveys yet.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {usageHistory.map((usage, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors border border-gray-200"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <DocumentTextIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                        <h4 className="font-medium text-gray-900">
                          {usage.rfq_title || 'Untitled Survey'}
                        </h4>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <ClockIcon className="w-4 h-4" />
                          <span>{formatRelativeTime(usage.used_at)}</span>
                        </div>
                        {usage.golden_pair_id && (
                          <button
                            onClick={() => handleNavigateToGoldenPair(usage.golden_pair_id!)}
                            className="text-purple-600 hover:text-purple-700 hover:underline flex items-center space-x-1"
                          >
                            <span>View Golden Pair</span>
                            <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleNavigateToSurvey(usage.survey_id)}
                      className="ml-4 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-colors flex items-center space-x-2"
                    >
                      <span>View Survey</span>
                      <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {!isLoading && !error && usageHistory.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <p className="text-sm text-gray-600">
              Showing {usageHistory.length} recent usage{usageHistory.length !== 1 ? 's' : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

