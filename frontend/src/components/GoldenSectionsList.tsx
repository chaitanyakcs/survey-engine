import React, { useEffect, useState, useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { GoldenSection } from '../types';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { GoldenContentEditModal } from './GoldenContentEditModal';

export const GoldenSectionsList: React.FC = () => {
  const { 
    goldenSections, 
    fetchGoldenSections, 
    updateGoldenSection, 
    deleteGoldenSection
  } = useAppStore();
  
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sectionTypeFilter, setSectionTypeFilter] = useState<string>('all');
  const [methodologyFilter, setMethodologyFilter] = useState<string>('');
  const [qualityFilter, setQualityFilter] = useState<string>('all');
  const [humanVerifiedFilter, setHumanVerifiedFilter] = useState<string>('all');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [editingSection, setEditingSection] = useState<GoldenSection | null>(null);

  const loadSections = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters: any = {};
      
      if (sectionTypeFilter !== 'all') {
        filters.section_type = sectionTypeFilter;
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
      
      await fetchGoldenSections(filters);
    } catch (error) {
      console.error('Failed to load golden sections:', error);
    } finally {
      setIsLoading(false);
    }
  }, [fetchGoldenSections, sectionTypeFilter, methodologyFilter, qualityFilter, humanVerifiedFilter, searchQuery]);

  useEffect(() => {
    loadSections();
  }, [loadSections]);

  const handleUpdateSection = async (id: string, updates: Partial<GoldenSection>) => {
    try {
      await updateGoldenSection(id, updates);
      setEditingSection(null);
    } catch (error) {
      console.error('Failed to update section:', error);
    }
  };

  const handleEditClick = (section: GoldenSection) => {
    setEditingSection(section);
  };

  const handleDeleteSection = async (id: string) => {
    try {
      await deleteGoldenSection(id);
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete section:', error);
    }
  };

  const formatQualityScore = (score: number | null | undefined) => {
    if (score === null || score === undefined) {
      return 'Not rated';
    }
    return `${Math.round(score * 100)}%`;
  };


  const sectionTypes = [
    'demographics', 'pricing', 'satisfaction', 'behavioral', 
    'preferences', 'intent', 'awareness', 'loyalty'
  ];

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search sections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm"
          />
        </div>
        
        <div className="flex items-center space-x-3">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <select
            value={sectionTypeFilter}
            onChange={(e) => setSectionTypeFilter(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-yellow-500 focus:border-transparent transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          >
            <option value="all">All Types</option>
            {sectionTypes.map(type => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
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
            <p className="text-gray-600">Loading golden sections...</p>
          </div>
        </div>
      ) : goldenSections.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-3">
              No golden sections found
            </h3>
            <p className="text-gray-600 mb-8 text-lg">
              Try adjusting your search or filters to find sections
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {goldenSections.map((section) => (
            <div
              key={section.id}
              className="bg-white rounded-xl border-2 border-gray-200 hover:border-yellow-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {section.section_title || 'Untitled Section'}
                      </h3>
                      {section.human_verified && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                          <CheckCircleIcon className="w-3 h-3 mr-1" />
                          Human Verified
                        </span>
                      )}
                      {section.annotation_id && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                          <TagIcon className="w-3 h-3 mr-1" />
                          From Annotation #{section.annotation_id}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-4 mb-3">
                      <div className="flex items-center space-x-2">
                        {section.section_type && (
                          <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                            {section.section_type}
                          </span>
                        )}
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                          Used {section.usage_count} times
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{section.methodology_tags?.length || 0} methodologies</span>
                        <span>•</span>
                        <span>{new Date(section.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    
                    <p className="text-gray-700 text-sm mb-3 line-clamp-2">
                      {section.section_text}
                    </p>
                    
                    {/* Methodology Tags */}
                    {section.methodology_tags && section.methodology_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {section.methodology_tags.slice(0, 4).map((tag, index) => (
                          <span key={index} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                            {tag}
                          </span>
                        ))}
                        {section.methodology_tags.length > 4 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-md">
                            +{section.methodology_tags.length - 4} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    <div className="text-right mr-4">
                      <div className={`text-sm font-medium ${
                        section.quality_score === null || section.quality_score === undefined 
                          ? 'text-gray-500' 
                          : 'text-gray-900'
                      }`}>
                        {formatQualityScore(section.quality_score)}
                      </div>
                      <div className="text-xs text-gray-500">Quality</div>
                    </div>
                    
                    <button
                      onClick={() => handleEditClick(section)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit Section"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => setShowDeleteConfirm(section.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Section"
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
                <h3 className="text-lg font-semibold text-gray-900">Delete Golden Section</h3>
                <p className="text-sm text-gray-600">This action cannot be undone.</p>
              </div>
            </div>
            
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete this golden section? This will remove it permanently from the system.
            </p>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteSection(showDeleteConfirm)}
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
        isOpen={editingSection !== null}
        onClose={() => setEditingSection(null)}
        content={editingSection}
        type="section"
        onSave={handleUpdateSection}
      />
    </div>
  );
};
