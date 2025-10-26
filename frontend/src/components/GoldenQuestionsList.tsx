import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenQuestion } from '../types';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  TagIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { GoldenContentEditModal } from './GoldenContentEditModal';
import { QuestionUsageModal } from './QuestionUsageModal';

export const GoldenQuestionsList: React.FC = () => {
  const { 
    goldenQuestions, 
    fetchGoldenQuestions, 
    updateGoldenQuestion, 
    deleteGoldenQuestion
  } = useAppStore();
  
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [questionTypeFilter, setQuestionTypeFilter] = useState<string>('all');
  const [questionSubtypeFilter, setQuestionSubtypeFilter] = useState<string>('all');
  const [methodologyFilter, setMethodologyFilter] = useState<string>('');
  const [qualityFilter, setQualityFilter] = useState<string>('all');
  const [humanVerifiedFilter, setHumanVerifiedFilter] = useState<string>('all');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<GoldenQuestion | null>(null);
  const [showUsageModal, setShowUsageModal] = useState<GoldenQuestion | null>(null);

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters: any = {};
      
      if (questionTypeFilter !== 'all') {
        filters.question_type = questionTypeFilter;
      }
      if (questionSubtypeFilter !== 'all') {
        filters.question_subtype = questionSubtypeFilter;
      }
      if (methodologyFilter) {
        filters.methodology_tags = methodologyFilter;
      }
      if (qualityFilter !== 'all') {
        filters.min_quality_score = parseFloat(qualityFilter);
      }
      if (humanVerifiedFilter !== 'all') {
        filters.human_verified = humanVerifiedFilter === 'verified';
      }
      if (searchQuery) {
        filters.search = searchQuery;
      }
      
      await fetchGoldenQuestions(filters);
    } catch (error) {
      console.error('Failed to load golden questions:', error);
    } finally {
      setIsLoading(false);
    }
  }, [fetchGoldenQuestions, questionTypeFilter, questionSubtypeFilter, methodologyFilter, qualityFilter, humanVerifiedFilter, searchQuery]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const handleUpdateQuestion = async (id: string, updates: Partial<GoldenQuestion>) => {
    try {
      await updateGoldenQuestion(id, updates);
      setEditingQuestion(null);
    } catch (error) {
      console.error('Failed to update question:', error);
    }
  };

  const handleEditClick = (question: GoldenQuestion) => {
    setEditingQuestion(question);
  };

  const handleDeleteQuestion = async (id: string) => {
    try {
      await deleteGoldenQuestion(id);
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete question:', error);
    }
  };

  const formatQualityScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) {
      return 'Not rated';
    }
    return `${Math.round(score * 100)}%`;
  };


  const questionTypes = [
    'multiple_choice', 'rating_scale', 'open_text', 'yes_no',
    'single_choice', 'matrix', 'ranking', 'slider'
  ];

  const questionSubtypes = [
    'likert_5', 'likert_7', 'binary', 'text_input',
    'dropdown', 'radio', 'checkbox', 'nps'
  ];

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search questions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
          />
        </div>
        
        <div className="flex items-center space-x-3">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <select
            value={questionTypeFilter}
            onChange={(e) => setQuestionTypeFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          >
            <option value="all">All Types</option>
            {questionTypes.map(type => (
              <option key={type} value={type}>
                {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
          
          <select
            value={questionSubtypeFilter}
            onChange={(e) => setQuestionSubtypeFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          >
            <option value="all">All Subtypes</option>
            {questionSubtypes.map(subtype => (
              <option key={subtype} value={subtype}>
                {subtype.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
          
          <input
            type="text"
            placeholder="Methodology tags..."
            value={methodologyFilter}
            onChange={(e) => setMethodologyFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
          
          <select
            value={qualityFilter}
            onChange={(e) => setQualityFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          >
            <option value="all">All Quality</option>
            <option value="0.8">80%+ Quality</option>
            <option value="0.6">60%+ Quality</option>
            <option value="0.4">40%+ Quality</option>
          </select>
          
          <select
            value={humanVerifiedFilter}
            onChange={(e) => setHumanVerifiedFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          >
            <option value="all">All</option>
            <option value="verified">Human Verified</option>
            <option value="unverified">AI Generated</option>
          </select>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="relative mb-4">
              <div className="w-16 h-16 border-4 border-yellow-200 rounded-full"></div>
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
            </div>
            <p className="text-gray-600">Loading golden questions...</p>
          </div>
        </div>
      ) : goldenQuestions.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-3">
              No golden questions found
            </h3>
            <p className="text-gray-600 mb-8 text-lg">
              Try adjusting your search or filters to find questions
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {goldenQuestions.map((question) => (
            <div
              key={question.id}
              className="bg-white rounded-xl border-2 border-gray-200 hover:border-yellow-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    {/* Compact Header - Status Badges Only */}
                    <div className="flex items-center space-x-3 mb-3">
                      {/* Status Badges */}
                      {question.human_verified && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                          <CheckCircleIcon className="w-3 h-3 mr-1" />
                          Human Verified
                        </span>
                      )}
                      {question.annotation_id && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                          <TagIcon className="w-3 h-3 mr-1" />
                          From Annotation #{question.annotation_id}
                        </span>
                      )}
                    </div>
                    
                    {/* Question Text */}
                    <p className="text-gray-700 text-sm mb-3 line-clamp-2">
                      {question.question_text}
                    </p>
                    
                    {/* Tags Row */}
                    <div className="flex items-center space-x-2 mb-3">
                      {/* Question Type Tags */}
                      {question.question_type && (
                        <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                          {question.question_type.replace('_', ' ')}
                        </span>
                      )}
                      {question.question_subtype && (
                        <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                          {question.question_subtype.replace('_', ' ')}
                        </span>
                      )}
                      
                      {/* Usage Count */}
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                        Used {question.usage_count} times
                      </span>
                      
                      {/* Methodology Tags (first 2 + hover for more) */}
                      {question.methodology_tags && question.methodology_tags.length > 0 && (
                        <div className="flex items-center space-x-1">
                          {question.methodology_tags.slice(0, 2).map((tag, index) => (
                            <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                              {tag}
                            </span>
                          ))}
                          {question.methodology_tags.length > 2 && (
                            <div className="group relative">
                              <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md cursor-help">
                                +{question.methodology_tags.length - 2} more
                              </span>
                              <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-10">
                                <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap">
                                  {question.methodology_tags.slice(2).join(', ')}
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    {/* Recently Used Section */}
                    {question.last_used_at && (
                      <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
                        <ClockIcon className="w-4 h-4" />
                        <span>Last used: {new Date(question.last_used_at).toLocaleDateString()}</span>
                        <button
                          onClick={() => setShowUsageModal(question)}
                          className="text-yellow-600 hover:text-yellow-700 hover:underline"
                        >
                          View usage history
                        </button>
                      </div>
                    )}
                    
                    {/* Question ID and Creation Date */}
                    <div className="flex items-center space-x-3 text-xs text-gray-500">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono bg-gray-100 text-gray-600 px-2 py-1 rounded">
                          {question.question_id}
                        </span>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(question.question_id);
                            // Could add toast notification here
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Copy Question ID"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        </button>
                      </div>
                      <div>
                        Created: {new Date(question.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  
                  {/* Right Side Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    {/* Suitability Score (only if exists) */}
                    {question.quality_score !== null && question.quality_score !== undefined && (
                      <div className="text-right mr-4">
                        <div className="text-sm font-medium text-gray-900">
                          {formatQualityScore(question.quality_score)}
                        </div>
                        <div className="text-xs text-gray-500" title="Combines quality rating and relevance assessment">
                          Suitability
                        </div>
                      </div>
                    )}
                    
                    <button
                      onClick={() => handleEditClick(question)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit Question"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => setShowDeleteConfirm(question.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Question"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <TrashIcon className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Golden Question</h3>
                <p className="text-sm text-gray-600">This action cannot be undone.</p>
              </div>
            </div>
            
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete this golden question? This will remove it permanently from the system.
            </p>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteQuestion(showDeleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <TrashIcon className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      <GoldenContentEditModal
        isOpen={editingQuestion !== null}
        onClose={() => setEditingQuestion(null)}
        content={editingQuestion}
        type="question"
        onSave={handleUpdateQuestion}
      />

      {/* Usage History Modal */}
      {showUsageModal && (
        <QuestionUsageModal
          isOpen={true}
          onClose={() => setShowUsageModal(null)}
          questionId={showUsageModal.id}
          questionText={showUsageModal.question_text}
        />
      )}
    </div>
  );
};
