import React, { useState } from 'react';
import { DocumentAnalysisResponse, RFQFieldMapping } from '../types';

interface DocumentAnalysisPreviewProps {
  analysisResult: DocumentAnalysisResponse;
  onAcceptMapping: (field: string, value: any) => void;
  onRejectMapping: (field: string) => void;
  onEditMapping: (field: string, value: any) => void;
  onApplyAll: () => void;
  className?: string;
}

export const DocumentAnalysisPreview: React.FC<DocumentAnalysisPreviewProps> = ({
  analysisResult,
  onAcceptMapping,
  onRejectMapping,
  onEditMapping,
  onApplyAll,
  className = ''
}) => {
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [expandedMappings, setExpandedMappings] = useState<Set<string>>(new Set());

  const { document_content, rfq_analysis } = analysisResult;
  const { field_mappings = [], confidence = 0 } = rfq_analysis;

  // Confidence display removed - all fields are accepted regardless of confidence

  const handleEditStart = (mapping: RFQFieldMapping) => {
    setEditingField(mapping.field);
    setEditValue(typeof mapping.value === 'string' ? mapping.value : JSON.stringify(mapping.value));
  };

  const handleEditSave = (field: string) => {
    try {
      // Try to parse as JSON first, then fall back to string
      let parsedValue;
      try {
        parsedValue = JSON.parse(editValue);
      } catch {
        parsedValue = editValue;
      }

      onEditMapping(field, parsedValue);
      setEditingField(null);
      setEditValue('');
    } catch (error) {
      console.error('Error saving edit:', error);
    }
  };

  const handleEditCancel = () => {
    setEditingField(null);
    setEditValue('');
  };

  const toggleMappingExpansion = (field: string) => {
    const newExpanded = new Set(expandedMappings);
    if (newExpanded.has(field)) {
      newExpanded.delete(field);
    } else {
      newExpanded.add(field);
    }
    setExpandedMappings(newExpanded);
  };

  const formatFieldName = (field: string) => {
    return field
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .toLowerCase()
      .replace(/^./, str => str.toUpperCase());
  };

  const acceptedMappings = field_mappings.filter(m => m.user_action === 'accepted');
  const pendingMappings = field_mappings.filter(m => !m.user_action || m.user_action === 'edited');
  const rejectedMappings = field_mappings.filter(m => m.user_action === 'rejected');

  return (
    <div className={`bg-white rounded-2xl border border-gray-200 shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 flex items-center">
              <span className="text-2xl mr-3">🔍</span>
              Document Analysis Results
            </h3>
            <p className="text-gray-600 mt-1">
              Extracted from {document_content.filename} ({document_content.word_count} words)
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="px-3 py-1 rounded-full text-sm font-medium border text-green-600 bg-green-50 border-green-200">
              Document Analysis Complete
            </div>

            {pendingMappings.length > 0 && (
              <button
                onClick={onApplyAll}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <span>✅</span>
                <span>Apply All ({pendingMappings.length})</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-6 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{acceptedMappings.length}</div>
            <div className="text-sm text-gray-600">Accepted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{pendingMappings.length}</div>
            <div className="text-sm text-gray-600">Pending Review</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{rejectedMappings.length}</div>
            <div className="text-sm text-gray-600">Rejected</div>
          </div>
        </div>
      </div>

      {/* Field Mappings */}
      <div className="p-6">
        <h4 className="font-semibold text-gray-900 mb-4">Field Mappings</h4>

        {field_mappings.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📄</div>
            <p>No field mappings found in the document.</p>
            <p className="text-sm mt-2">The document may not contain structured RFQ information.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {field_mappings.map((mapping, index) => {
              const isExpanded = expandedMappings.has(mapping.field);
              const isEditing = editingField === mapping.field;

              return (
                <div
                  key={`${mapping.field}-${index}`}
                  className={`border rounded-xl p-4 transition-all duration-200 ${
                    mapping.user_action === 'accepted'
                      ? 'border-green-200 bg-green-50'
                      : mapping.user_action === 'rejected'
                      ? 'border-red-200 bg-red-50'
                      : 'border-gray-200 bg-white hover:border-blue-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h5 className="font-medium text-gray-900">
                          {formatFieldName(mapping.field)}
                        </h5>
                        <div className="px-2 py-1 rounded text-xs font-medium text-green-600 bg-green-50">
                          Extracted
                        </div>
                        {mapping.needs_review && (
                          <div className="px-2 py-1 rounded text-xs font-medium bg-orange-50 text-orange-600 border border-orange-200">
                            Needs Review
                          </div>
                        )}
                      </div>

                      <div className="mb-3">
                        {isEditing ? (
                          <div className="space-y-2">
                            <textarea
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              className="w-full p-3 border border-gray-300 rounded-lg resize-none"
                              rows={3}
                              placeholder="Edit the extracted value..."
                            />
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleEditSave(mapping.field)}
                                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                              >
                                Save
                              </button>
                              <button
                                onClick={handleEditCancel}
                                className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                            <div className="text-sm text-gray-900 font-mono">
                              {typeof mapping.value === 'string'
                                ? mapping.value
                                : JSON.stringify(mapping.value, null, 2)
                              }
                            </div>
                          </div>
                        )}
                      </div>

                      {isExpanded && (
                        <div className="space-y-3 text-sm">
                          <div>
                            <label className="font-medium text-gray-700">Source Text:</label>
                            <div className="mt-1 p-2 bg-blue-50 rounded border border-blue-200 text-gray-800">
                              "{mapping.source}"
                            </div>
                          </div>

                          <div>
                            <label className="font-medium text-gray-700">AI Reasoning:</label>
                            <div className="mt-1 p-2 bg-purple-50 rounded border border-purple-200 text-gray-800">
                              {mapping.reasoning}
                            </div>
                          </div>

                          {mapping.suggestions && mapping.suggestions.length > 0 && (
                            <div>
                              <label className="font-medium text-gray-700">Suggestions:</label>
                              <ul className="mt-1 list-disc list-inside text-gray-600">
                                {mapping.suggestions.map((suggestion, idx) => (
                                  <li key={idx}>{suggestion}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col space-y-2 ml-4">
                      <button
                        onClick={() => toggleMappingExpansion(mapping.field)}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                        title={isExpanded ? 'Collapse details' : 'Expand details'}
                      >
                        {isExpanded ? '📐' : '🔍'}
                      </button>

                      {mapping.user_action !== 'accepted' && !isEditing && (
                        <button
                          onClick={() => onAcceptMapping(mapping.field, mapping.value)}
                          className="p-2 text-green-600 hover:text-green-700 hover:bg-green-100 rounded"
                          title="Accept mapping"
                        >
                          ✅
                        </button>
                      )}

                      {mapping.user_action !== 'rejected' && !isEditing && (
                        <button
                          onClick={() => onRejectMapping(mapping.field)}
                          className="p-2 text-red-600 hover:text-red-700 hover:bg-red-100 rounded"
                          title="Reject mapping"
                        >
                          ❌
                        </button>
                      )}

                      {!isEditing && (
                        <button
                          onClick={() => handleEditStart(mapping)}
                          className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-100 rounded"
                          title="Edit value"
                        >
                          ✏️
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};