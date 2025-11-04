import React, { useState, useEffect, useRef } from 'react';
import { useQNRLabels } from '../hooks/useQNRLabels';
import { QNRLabelEditModal } from './QNRLabelEditModal';
import { 
  ChevronDownIcon,
  ChevronRightIcon,
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
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const [sectionLabelsMap, setSectionLabelsMap] = useState<Record<number, any[]>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [mandatoryOnly, setMandatoryOnly] = useState(false);
  const [editingLabel, setEditingLabel] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ show: boolean; label: any }>({ show: false, label: null });
  const [editingSectionId, setEditingSectionId] = useState<number | null>(null);
  const [editingSectionName, setEditingSectionName] = useState('');
  const [editingSectionDesc, setEditingSectionDesc] = useState('');
  const hasFetchedLabelsRef = useRef(false);
  
  const { 
    sections, 
    loading, 
    error, 
    refetch,
    fetchLabelsBySection 
  } = useQNRLabels({
    active_only: true
  });

  // Fetch all labels on mount and when sections change to calculate counts
  useEffect(() => {
    if (!loading && sections.length > 0 && !hasFetchedLabelsRef.current) {
      hasFetchedLabelsRef.current = true;
      // Fetch labels for all sections to get counts
      const fetchAllLabelCounts = async () => {
        const labelsMap: Record<number, any[]> = {};
        for (const section of sections) {
          try {
            const labels = await fetchLabelsBySection(section.id);
            labelsMap[section.id] = labels;
          } catch (err) {
            console.error(`Failed to fetch labels for section ${section.id}:`, err);
            labelsMap[section.id] = [];
          }
        }
        setSectionLabelsMap(labelsMap);
      };
      fetchAllLabelCounts();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, sections, fetchLabelsBySection]);

  const categoryColors: Record<string, string> = {
    screener: 'bg-blue-100 text-blue-800',
    brand: 'bg-green-100 text-green-800',
    concept: 'bg-purple-100 text-purple-800',
    methodology: 'bg-yellow-100 text-yellow-800',
    additional: 'bg-gray-100 text-gray-800',
    programmer_instructions: 'bg-orange-100 text-orange-800'
  };

  // Toggle section expansion
  const toggleSection = (sectionId: number) => {
    const newExpanded = new Set(expandedSections);
    const wasExpanded = newExpanded.has(sectionId);
    
    if (wasExpanded) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
      // Labels are already loaded from initial fetch, no need to fetch again
    }
    
    setExpandedSections(newExpanded);
  };

  // Get filtered labels for a section
  const getFilteredLabels = (sectionId: number) => {
    const labels = sectionLabelsMap[sectionId] || [];
    return labels.filter(label => {
      const matchesSearch = !searchQuery || 
        label.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        label.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesMandatory = !mandatoryOnly || label.mandatory;
      return matchesSearch && matchesMandatory;
    });
  };

  // Handlers
  const handleCreateLabel = (sectionId: number) => {
    setEditingLabel({ section_id: sectionId });
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
    // Refresh labels for the section
    if (labelData.section_id) {
      try {
        const labels = await fetchLabelsBySection(labelData.section_id);
        setSectionLabelsMap(prev => ({ ...prev, [labelData.section_id]: labels }));
      } catch (err) {
        console.error(`Failed to refresh labels for section ${labelData.section_id}:`, err);
      }
    }
    setIsModalOpen(false);
    setEditingLabel(null);
  };

  const handleConfirmDelete = async () => {
    if (deleteConfirm.label) {
      // API call will be implemented in useQNRLabels hook
      console.log('Deleting label:', deleteConfirm.label);
      await refetch();
      // Refresh labels for the section
      if (deleteConfirm.label.section_id) {
        try {
          const labels = await fetchLabelsBySection(deleteConfirm.label.section_id);
          setSectionLabelsMap(prev => ({ ...prev, [deleteConfirm.label.section_id]: labels }));
        } catch (err) {
          console.error(`Failed to refresh labels for section ${deleteConfirm.label.section_id}:`, err);
        }
      }
      setDeleteConfirm({ show: false, label: null });
    }
  };

  // Section editing
  const startEditingSection = (section: any) => {
    setEditingSectionId(section.id);
    setEditingSectionName(section.name);
    setEditingSectionDesc(section.description || '');
  };

  const saveSectionEdit = async () => {
    if (editingSectionId) {
      // TODO: API call to update section
      console.log('Saving section:', { id: editingSectionId, name: editingSectionName, description: editingSectionDesc });
      // await updateSection(editingSectionId, { name: editingSectionName, description: editingSectionDesc });
      await refetch();
      setEditingSectionId(null);
      setEditingSectionName('');
      setEditingSectionDesc('');
    }
  };

  const cancelSectionEdit = () => {
    setEditingSectionId(null);
    setEditingSectionName('');
    setEditingSectionDesc('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">QNR Taxonomy</h2>
          <p className="text-sm text-gray-600 mt-1">
            Manage sections and labels for survey generation. Expand sections to view and edit labels.
          </p>
        </div>
      </div>

      {/* Global Filters */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-4 border border-gray-200">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search labels across all sections..."
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

      {/* Sections List */}
      {!loading && !error && (
        <div className="space-y-4">
          {sections.map((section) => {
            const isExpanded = expandedSections.has(section.id);
            const isEditing = editingSectionId === section.id;
            const allLabels = sectionLabelsMap[section.id] || [];
            const labels = getFilteredLabels(section.id);
            const mandatoryCount = allLabels.filter(l => l.mandatory).length;

            return (
              <div
                key={section.id}
                className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
              >
                {/* Section Header */}
                <div
                  className="bg-gradient-to-r from-yellow-50 to-yellow-100 px-6 py-4 border-b border-gray-200 cursor-pointer hover:from-yellow-100 hover:to-yellow-200 transition-colors"
                  onClick={() => !isEditing && toggleSection(section.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="flex items-center justify-center w-8 h-8 bg-yellow-200 text-yellow-700 rounded-full font-semibold text-sm">
                        {section.id}
                      </div>
                      <div className="flex-1">
                        {isEditing ? (
                          <div className="space-y-2">
                            <input
                              type="text"
                              value={editingSectionName}
                              onChange={(e) => setEditingSectionName(e.target.value)}
                              className="text-lg font-semibold text-gray-900 bg-white border border-yellow-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-yellow-500 w-full"
                              onClick={(e) => e.stopPropagation()}
                              autoFocus
                            />
                            <textarea
                              value={editingSectionDesc}
                              onChange={(e) => setEditingSectionDesc(e.target.value)}
                              className="text-sm text-gray-600 bg-white border border-yellow-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-yellow-500 w-full"
                              rows={2}
                              onClick={(e) => e.stopPropagation()}
                            />
                            <div className="flex space-x-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  saveSectionEdit();
                                }}
                                className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700"
                              >
                                Save
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  cancelSectionEdit();
                                }}
                                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-center space-x-2">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {section.name}
                              </h3>
                              {section.mandatory && (
                                <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                                  Mandatory
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{section.description}</p>
                            <div className="flex items-center space-x-4 mt-2">
                              <span className="text-xs text-gray-500">
                                <strong>{allLabels.length}</strong> labels
                              </span>
                              <span className="text-xs text-gray-500">
                                <strong>{mandatoryCount}</strong> mandatory
                              </span>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {!isEditing && (
                        <>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              startEditingSection(section);
                            }}
                            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Edit section"
                          >
                            <PencilIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSection(section.id);
                            }}
                            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                          >
                            {isExpanded ? (
                              <ChevronDownIcon className="w-5 h-5" />
                            ) : (
                              <ChevronRightIcon className="w-5 h-5" />
                            )}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Section Labels (Expanded) */}
                {isExpanded && !isEditing && (
                  <div className="p-6 space-y-4">
                    {/* Section-specific search and add button */}
                    <div className="flex items-center justify-between pb-4 border-b border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700">
                        {labels.length > 0 ? `${labels.length} label${labels.length !== 1 ? 's' : ''} found` : 'No labels found'}
                      </h4>
                      <button
                        onClick={() => handleCreateLabel(section.id)}
                        className="inline-flex items-center px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
                      >
                        <PlusIcon className="w-4 h-4 mr-1" />
                        Add Label
                      </button>
                    </div>

                    {/* Labels List */}
                    {labels.length > 0 ? (
                      <div className="space-y-3">
                        {labels.map((label) => (
                          <div
                            key={label.id || label.name}
                            className="bg-gray-50 rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-3">
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[label.category] || 'bg-gray-100 text-gray-800'}`}>
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
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <TagIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                        <p>No labels found{searchQuery || mandatoryOnly ? ' matching your filters' : ''}</p>
                        <button
                          onClick={() => handleCreateLabel(section.id)}
                          className="mt-4 inline-flex items-center px-3 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors text-sm"
                        >
                          <PlusIcon className="w-4 h-4 mr-1" />
                          Add First Label
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Modal */}
      <QNRLabelEditModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingLabel(null);
        }}
        onSave={handleSaveLabel}
        label={editingLabel}
        mode={editingLabel?.id ? 'edit' : 'create'}
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
