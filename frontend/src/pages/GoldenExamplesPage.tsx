import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Sidebar } from '../components/Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { 
  ArrowPathIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { GoldenSectionsList } from '../components/GoldenSectionsList';
import { GoldenQuestionsList } from '../components/GoldenQuestionsList';

export const GoldenExamplesPage: React.FC = () => {
  const { goldenExamples, fetchGoldenExamples, deleteGoldenExample, toasts, removeToast } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'pairs' | 'sections' | 'questions'>('pairs');
  const { mainContentClasses } = useSidebarLayout();

  const loadGoldenExamples = useCallback(async () => {
    setIsLoading(true);
    try {
      await fetchGoldenExamples();
    } catch (error) {
      console.error('Failed to load golden examples:', error);
    } finally {
      setIsLoading(false);
    }
  }, [fetchGoldenExamples]);

  useEffect(() => {
    loadGoldenExamples();
  }, [loadGoldenExamples]);

  const handleDeleteExample = async (id: string) => {
    setIsLoading(true);
    try {
      await deleteGoldenExample(id);
      await loadGoldenExamples();
    } catch (error) {
      console.error('Failed to delete golden example:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatQualityScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) {
      return 'Not rated';
    }
    return `${(score * 100).toFixed(0)}%`;
  };

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings' | 'annotation-insights' | 'llm-review') => {
    if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'survey') {
      window.location.href = '/';
    } else if (view === 'annotation-insights') {
      window.location.href = '/annotation-insights';
    } else if (view === 'llm-review') {
      window.location.href = '/llm-audit';
    }
  };

  // Filter golden examples based on search and category
  const filteredGoldenExamples = goldenExamples.filter(example => {
    const matchesSearch = 
      (example.rfq_text && example.rfq_text.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (example.industry_category && example.industry_category.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (example.research_goal && example.research_goal.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (example.methodology_tags && example.methodology_tags.some(tag => 
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      ));
    
    const matchesCategory = categoryFilter === 'all' || 
      (categoryFilter === 'with-rfq' && example.rfq_text) ||
      (categoryFilter === 'survey-only' && !example.rfq_text) ||
      (categoryFilter === 'rated' && example.quality_score !== null && example.quality_score !== undefined);
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      <div className="flex">
        {/* Sidebar */}
        <Sidebar currentView="golden-examples" onViewChange={handleViewChange} />
        
        {/* Main Content */}
        <div className={`flex-1 ${mainContentClasses} transition-all duration-300 ease-in-out`}>
          <main className="py-8 px-6">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                    <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                      Reference Examples
                    </h1>
                    <p className="text-gray-600">Manage reference examples for survey generation</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={loadGoldenExamples}
                    disabled={isLoading}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50"
                  >
                    <ArrowPathIcon className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                  <button
                    onClick={() => window.location.href = '/golden-examples/new'}
                    className="px-8 py-4 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create Reference Example
                  </button>
                </div>
              </div>
              
              {/* Search and Filters */}
              <div className="flex items-center space-x-4 mt-6">
                <div className="relative flex-1 max-w-md">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search examples..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
                  />
                </div>
                
                <div className="flex items-center space-x-3">
                  <FunnelIcon className="h-5 w-5 text-gray-400" />
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
                  >
                    <option value="all">All Examples</option>
                    <option value="with-rfq">With RFQ</option>
                    <option value="survey-only">Survey Only</option>
                    <option value="rated">Rated Examples</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex space-x-2 border-b border-gray-200 mb-6">
              <button
                onClick={() => setActiveTab('pairs')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'pairs'
                    ? 'border-b-2 border-yellow-600 text-yellow-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Golden Pairs
              </button>
              <button
                onClick={() => setActiveTab('sections')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'sections'
                    ? 'border-b-2 border-yellow-600 text-yellow-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Sections
              </button>
              <button
                onClick={() => setActiveTab('questions')}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === 'questions'
                    ? 'border-b-2 border-yellow-600 text-yellow-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Questions
              </button>
            </div>

            {/* Content */}
            {activeTab === 'pairs' && (
              <>
                {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="relative mb-4">
                    <div className="w-16 h-16 border-4 border-yellow-200 rounded-full"></div>
                    <div className="absolute top-0 left-0 w-16 h-16 border-4 border-yellow-600 rounded-full border-t-transparent animate-spin"></div>
                  </div>
                  <p className="text-gray-600">Loading reference examples...</p>
                </div>
              </div>
            ) : filteredGoldenExamples.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                    {goldenExamples.length === 0 ? 'No reference examples yet' : 'No examples found'}
                  </h3>
                  <p className="text-gray-600 mb-8 text-lg">
                    {goldenExamples.length === 0 
                      ? 'Get started by creating your first reference example'
                      : 'Try adjusting your search or filters to find examples'
                    }
                  </p>
                  <button
                    onClick={() => window.location.href = '/golden-examples/new'}
                    className="px-8 py-4 bg-gradient-to-r from-yellow-600 to-orange-600 text-white rounded-xl hover:from-yellow-700 hover:to-orange-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Create Reference Example
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredGoldenExamples.map((example) => (
                  <div
                    key={example.id}
                    onClick={() => window.location.href = `/golden-examples/${example.id}/edit`}
                    className="bg-white rounded-xl border-2 border-gray-200 hover:border-yellow-300 hover:shadow-lg transition-all duration-200 cursor-pointer"
                  >
                    <div className="p-6">
                      <div className="flex items-center space-x-4">
                        {/* Golden Example Icon */}
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                        </div>
                        
                        {/* Golden Example Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-3 mb-2">
                                <h3 className="text-lg font-semibold text-gray-900 truncate">
                                  {example.rfq_text ? 
                                    `${example.rfq_text.substring(0, 50)}...` : 
                                    example.survey_json?.final_output?.title || 
                                    example.survey_json?.title || 
                                    'Untitled Example'
                                  }
                                </h3>
                                {!example.rfq_text && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
                                    Survey Only
                                  </span>
                                )}
                              </div>
                              
                              <div className="flex items-center space-x-4 mb-3">
                                <div className="flex items-center space-x-2">
                                  <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                                    {example.industry_category || 'General'}
                                  </span>
                                  <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                                    {example.research_goal || 'Research'}
                                  </span>
                                </div>
                                
                                <div className="flex items-center space-x-4 text-sm text-gray-500">
                                  <span>Used {example.usage_count} times</span>
                                  <span>•</span>
                                  <span>{example.methodology_tags?.length || 0} methodologies</span>
                                  <span>•</span>
                                  <span>{new Date(example.created_at).toLocaleDateString()}</span>
                                </div>
                              </div>
                              
                              {/* Methodology Tags */}
                              {example.methodology_tags && example.methodology_tags.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {example.methodology_tags.slice(0, 4).map((tag, index) => (
                                    <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                                      {tag}
                                    </span>
                                  ))}
                                  {example.methodology_tags.length > 4 && (
                                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                                      +{example.methodology_tags.length - 4} more
                                    </span>
                                  )}
                                </div>
                              )}
                            </div>
                            
                            {/* Actions */}
                            <div className="flex items-center space-x-2 ml-4">
                              <div className="text-right mr-4">
                                <div className={`text-sm font-medium ${
                                  example.quality_score === null || example.quality_score === undefined 
                                    ? 'text-gray-500' 
                                    : 'text-gray-900'
                                }`}>
                                  {formatQualityScore(example.quality_score)}
                                </div>
                                <div className="text-xs text-gray-500">Quality</div>
                              </div>
                              
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setShowDeleteConfirm(example.id);
                                }}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="Delete Example"
                              >
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
              </>
            )}

            {activeTab === 'sections' && <GoldenSectionsList />}

            {activeTab === 'questions' && <GoldenQuestionsList />}
          </main>
        </div>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <TrashIcon className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Delete Golden Example</h3>
                <p className="text-sm text-gray-600">This action cannot be undone.</p>
              </div>
            </div>
            
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete this golden example? This will remove it permanently from the system.
            </p>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  await handleDeleteExample(showDeleteConfirm);
                  setShowDeleteConfirm(null);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <TrashIcon className="w-4 h-4" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};