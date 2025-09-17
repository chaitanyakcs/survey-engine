import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenExample } from '../types';
import { Sidebar } from '../components/Sidebar';
import { useSidebarLayout } from '../hooks/useSidebarLayout';
import { ToastContainer } from '../components/Toast';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckIcon,
  PencilIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

export const GoldenExamplesPage: React.FC = () => {
  const { goldenExamples, fetchGoldenExamples, deleteGoldenExample, toasts, removeToast, addToast } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [currentView, setCurrentView] = useState<'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings'>('golden-examples');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
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

  const formatQualityScore = (score: number) => {
    return `${(score * 100).toFixed(0)}%`;
  };

  const handleViewChange = (view: 'survey' | 'golden-examples' | 'rules' | 'surveys' | 'settings') => {
    if (view === 'rules') {
      window.location.href = '/rules';
    } else if (view === 'surveys') {
      window.location.href = '/surveys';
    } else if (view === 'golden-examples') {
      window.location.href = '/golden-examples';
    } else if (view === 'survey') {
      window.location.href = '/';
    }
  };

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
            </div>

            {/* Content */}
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
            ) : goldenExamples.length === 0 ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-3">No reference examples yet</h3>
                  <p className="text-gray-600 mb-8 text-lg">Get started by creating your first reference example</p>
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
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {goldenExamples.map((example) => (
                  <div 
                    key={example.id} 
                    onClick={() => window.location.href = `/golden-examples/${example.id}/edit`}
                    className="group bg-white rounded-xl border-2 border-gray-200 hover:border-yellow-300 hover:shadow-lg transition-all duration-200 bg-gradient-to-br from-white to-yellow-50/20 cursor-pointer"
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-yellow-700 transition-colors">
                            {example.rfq_text?.substring(0, 60)}...
                          </h3>
                          <div className="flex items-center space-x-2 mb-3">
                            <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                              {example.industry_category || 'General'}
                            </span>
                            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                              {example.research_goal || 'Research'}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              {formatQualityScore(example.quality_score)}
                            </div>
                            <div className="text-xs text-gray-500">Quality</div>
                          </div>
                          <div className="flex items-center space-x-1">
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
                      
                      <div className="space-y-3">
                        <div className="flex flex-wrap gap-1">
                          {example.methodology_tags?.slice(0, 3).map((tag, index) => (
                            <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                              {tag}
                            </span>
                          ))}
                          {example.methodology_tags && example.methodology_tags.length > 3 && (
                            <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                              +{example.methodology_tags.length - 3} more
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center justify-between text-sm text-gray-500">
                          <span>Used {example.usage_count} times</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
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