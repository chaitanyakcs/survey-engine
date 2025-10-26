import React, { useState } from 'react';
import { useQNRLabels } from '../hooks/useQNRLabels';
import { QNRLabelEditModal } from './QNRLabelEditModal';
import { 
  BookOpenIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon,
  MagnifyingGlassIcon,
  TagIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface QNRTaxonomyManagementProps {
  // No props needed - self-contained
}

export const QNRTaxonomyManagement: React.FC<QNRTaxonomyManagementProps> = () => {
  const [activeTab, setActiveTab] = useState<'sections' | 'labels'>('sections');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [mandatoryOnly, setMandatoryOnly] = useState(false);
  const [editingLabel, setEditingLabel] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; label: any }>({ show: false, label: null });
  
  const { 
    labels, 
    sections, 
    loading, 
    error, 
    refetch 
  } = useQNRLabels({
    category: selectedCategory !== 'all' ? selectedCategory : undefined,
    mandatory_only: mandatoryOnly,
    search: searchQuery
  });

  // Filter labels by active filters
  const filteredLabels = labels.filter(label => {
    const matchesSearch = !searchQuery || 
      label.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      label.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || label.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['all', 'screener', 'brand', 'concept', 'methodology', 'additional'];

  const categoryColors: Record<string, string> = {
    screener: 'bg-blue-100 text-blue-800',
    brand: 'bg-green-100 text-green-800',
    concept: 'bg-purple-100 text-purple-800',
    methodology: 'bg-yellow-100 text-yellow-800',
    additional: 'bg-gray-100 text-gray-800'
  };

  // Handlers
  const handleCreateLabel = () => {
    setEditingLabel(null);
    setIsModalOpen(true);
  };

  const handleEditLabel = (label: any) => {
    setEditingLabel(label);
    setIsModalOpen(true);
  };

  const handleDeleteLabel = (label: any) => {
    setDeleteConfirm({ show: true, label });
  };

  const handleSaveLabel = async (labelData: any) => {
    // API call will be implemented in useQNRLabels hook
    console.log('Saving label:', labelData);
    await refetch();
  };

  const handleConfirmDelete = async () => {
    if (deleteConfirm.label) {
      // API call will be implemented in useQNRLabels hook
      console.log('Deleting label:', deleteConfirm.label);
      await refetch();
      setDeleteConfirm({ show: false, label: null });
    }
  };

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('sections')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'sections'
                ? 'border-yellow-500 text-yellow-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <BookOpenIcon className="w-5 h-5" />
              <span>Sections ({sections.length})</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('labels')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'labels'
                ? 'border-yellow-500 text-yellow-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center space-x-2">
              <TagIcon className="w-5 h-5" />
              <span>Labels ({filteredLabels.length})</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600"></div>
          <span className="ml-3 text-gray-600">Loading taxonomy...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button
            onClick={() => refetch()}
            className="mt-2 text-sm text-red-600 hover:text-red-800"
          >
            Retry
          </button>
        </div>
      )}

      {/* Sections Tab */}
      {activeTab === 'sections' && !loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">QNR Sections</h3>
            <button
              className="inline-flex items-center px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
              disabled
              title="Coming soon"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Edit Section
            </button>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
            ℹ️ Section editing coming soon. Currently managing 7 standard QNR sections.
          </div>

          <div className="grid gap-4">
            {sections.map((section) => {
              const sectionLabels = labels.filter(l => {
                const sectionMap: Record<number, string> = {
                  1: 'screener',
                  2: 'screener',
                  3: 'brand',
                  4: 'concept',
                  5: 'methodology',
                  6: 'additional',
                  7: 'screener'
                };
                return sectionMap[section.id] === l.category;
              });
              const mandatoryCount = sectionLabels.filter(l => l.mandatory).length;

              return (
                <div
                  key={section.id}
                  className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h4 className="text-lg font-semibold text-gray-900">
                          {section.name}
                        </h4>
                        {section.mandatory && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                            Mandatory
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 mt-2">{section.description}</p>
                      <div className="flex items-center space-x-4 mt-4">
                        <span className="text-sm text-gray-500">
                          <strong>{sectionLabels.length}</strong> labels
                        </span>
                        <span className="text-sm text-gray-500">
                          <strong>{mandatoryCount}</strong> mandatory
                        </span>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                        onClick={() => {
                          setActiveTab('labels');
                          // Could add section filter here
                        }}
                        title="View labels for this section"
                      >
                        View Labels
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Labels Tab */}
      {activeTab === 'labels' && !loading && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-4">
            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search labels..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                )}
              </div>
              
              {/* Category Filter */}
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>
                    {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>

              {/* Mandatory Filter */}
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mandatoryOnly}
                  onChange={(e) => setMandatoryOnly(e.target.checked)}
                  className="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
                />
                <span className="text-sm text-gray-700">Mandatory only</span>
              </label>
            </div>
          </div>

          {/* Add Label Button */}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              QNR Labels ({filteredLabels.length})
            </h3>
            <button
              onClick={handleCreateLabel}
              className="inline-flex items-center px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Label
            </button>
          </div>

          {/* Labels List */}
          <div className="space-y-3">
            {filteredLabels.map((label) => (
              <div
                key={label.name}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[label.category]}`}>
                        {label.category}
                      </span>
                      <h4 className="text-base font-semibold text-gray-900">
                        {label.name}
                      </h4>
                      {label.mandatory && (
                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                          MANDATORY
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 mt-2 text-sm">{label.description}</p>
                    <div className="flex items-center space-x-4 mt-3">
                      <span className="text-xs text-gray-500">
                        Type: <strong>{label.type}</strong>
                      </span>
                      {label.applicableLabels && label.applicableLabels.length > 0 && (
                        <span className="text-xs text-gray-500">
                          Applicable to: <strong>{label.applicableLabels.join(', ')}</strong>
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEditLabel(label)}
                      className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit label"
                    >
                      <PencilIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteLabel(label)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete label"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {filteredLabels.length === 0 && (
            <div className="text-center py-12">
              <TagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No labels match your filters</p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                  setMandatoryOnly(false);
                }}
                className="mt-2 text-sm text-yellow-600 hover:text-yellow-700"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      )}

      {/* Edit Modal */}
      <QNRLabelEditModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleSaveLabel}
        label={editingLabel}
        mode={editingLabel ? 'edit' : 'create'}
      />

      {/* Delete Confirmation */}
      {deleteConfirm.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Confirm Delete</h3>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete the label <strong>"{deleteConfirm.label?.name}"</strong>?
                This action cannot be undone.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setDeleteConfirm({ show: false, label: null })}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmDelete}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

