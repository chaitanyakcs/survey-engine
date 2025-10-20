import React, { useState, useCallback } from 'react';
import { ChevronDownIcon, ChevronRightIcon, PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface RetrievalWeights {
  id: string;
  context_type: 'global' | 'methodology' | 'industry';
  context_value: string;
  semantic_weight: number;
  methodology_weight: number;
  industry_weight: number;
  quality_weight: number;
  annotation_weight: number;
  enabled: boolean;
}

interface RetrievalWeightsAccordionProps {
  weights: RetrievalWeights[];
  onUpdateWeight: (weightId: string, updates: Partial<RetrievalWeights>) => Promise<void>;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
}

export const RetrievalWeightsAccordion: React.FC<RetrievalWeightsAccordionProps> = ({
  weights,
  onUpdateWeight,
  onError,
  onSuccess
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [editingItem, setEditingItem] = useState<string | null>(null);
  const [editingWeights, setEditingWeights] = useState<Partial<RetrievalWeights>>({});
  const [saving, setSaving] = useState(false);

  const toggleExpanded = useCallback((itemId: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  }, []);

  const startEditing = useCallback((weight: RetrievalWeights) => {
    setEditingItem(weight.id);
    setEditingWeights({ ...weight });
  }, []);

  const cancelEditing = useCallback(() => {
    setEditingItem(null);
    setEditingWeights({});
  }, []);

  const saveChanges = useCallback(async () => {
    if (!editingItem) return;

    setSaving(true);
    try {
      await onUpdateWeight(editingItem, editingWeights);
      setEditingItem(null);
      setEditingWeights({});
      onSuccess('Weights updated successfully!');
    } catch (error) {
      onError('Failed to update weights. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [editingItem, editingWeights, onUpdateWeight, onError, onSuccess]);

  const updateWeight = useCallback((key: keyof RetrievalWeights, value: number) => {
    setEditingWeights(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);

  // Group weights by context type
  const groupedWeights = weights.reduce((acc, weight) => {
    if (!acc[weight.context_type]) {
      acc[weight.context_type] = [];
    }
    acc[weight.context_type].push(weight);
    return acc;
  }, {} as Record<string, RetrievalWeights[]>);

  // Calculate total weight for validation
  const getTotalWeight = useCallback((weight: Partial<RetrievalWeights>, baseWeight: RetrievalWeights) => {
    const semantic = Number(weight.semantic_weight ?? baseWeight.semantic_weight ?? 0);
    const methodology = Number(weight.methodology_weight ?? baseWeight.methodology_weight ?? 0);
    const industry = Number(weight.industry_weight ?? baseWeight.industry_weight ?? 0);
    const quality = Number(weight.quality_weight ?? baseWeight.quality_weight ?? 0);
    const annotation = Number(weight.annotation_weight ?? baseWeight.annotation_weight ?? 0);
    
    return semantic + methodology + industry + quality + annotation;
  }, []);

  const getContextIcon = (contextType: string) => {
    switch (contextType) {
      case 'global': return '🌐';
      case 'methodology': return '🔬';
      case 'industry': return '🏢';
      default: return '⚙️';
    }
  };


  const weightConfigs = [
    { key: 'semantic_weight', label: 'Semantic Similarity', color: 'purple', description: 'How similar the RFQ text is to golden examples' },
    { key: 'methodology_weight', label: 'Methodology Match', color: 'green', description: 'How well the research methodology aligns' },
    { key: 'industry_weight', label: 'Industry Relevance', color: 'blue', description: 'How relevant the industry context is' },
    { key: 'quality_weight', label: 'Quality Score', color: 'yellow', description: 'The pillar-based quality rating of the example' },
    { key: 'annotation_weight', label: 'Annotation Score', color: 'red', description: 'Human annotation feedback and labels' }
  ];

  return (
    <div className="space-y-4">
      {Object.entries(groupedWeights).map(([contextType, contextWeights]) => (
        <div key={contextType} className="bg-white rounded-lg border border-gray-200 shadow-sm">
          {/* Context Type Header */}
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <span className="text-xl">{getContextIcon(contextType)}</span>
              <span className="capitalize">{contextType} Configurations</span>
              <span className="text-sm text-gray-500">({contextWeights.length})</span>
            </h3>
          </div>

          {/* Weight Items */}
          <div className="divide-y divide-gray-200">
            {contextWeights.map((weight) => {
              const isExpanded = expandedItems.has(weight.id);
              const isEditing = editingItem === weight.id;
              const totalWeight = isEditing ? getTotalWeight(editingWeights, weight) : 
                Number(weight.semantic_weight) + Number(weight.methodology_weight) + Number(weight.industry_weight) + 
                Number(weight.quality_weight) + Number(weight.annotation_weight);
              const isValidTotal = Math.abs(totalWeight - 1) < 0.01;

              return (
                <div key={weight.id} className="transition-all duration-200">
                  {/* Item Header */}
                  <div 
                    className="px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => toggleExpanded(weight.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {isExpanded ? (
                          <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                        )}
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {weight.context_value || 'Default'}
                          </h4>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>Semantic: {Math.round(weight.semantic_weight * 100)}%</span>
                            <span>Methodology: {Math.round(weight.methodology_weight * 100)}%</span>
                            <span>Industry: {Math.round(weight.industry_weight * 100)}%</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          weight.enabled 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {weight.enabled ? 'Active' : 'Disabled'}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (!isExpanded) {
                              toggleExpanded(weight.id);
                            }
                            startEditing(weight);
                          }}
                          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors flex items-center space-x-1"
                        >
                          <PencilIcon className="w-4 h-4" />
                          <span>Edit</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="px-4 pb-4 bg-gray-50">
                      {isEditing ? (
                        /* Editing Mode */
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                            {weightConfigs.map(({ key, label, color, description }) => {
                              const currentValue = editingWeights[key as keyof RetrievalWeights] ?? weight[key as keyof RetrievalWeights];
                              const numericValue = Number(currentValue);

                              return (
                                <div key={key} className="space-y-2">
                                  <label className="block text-sm font-medium text-gray-700">
                                    {label}
                                  </label>
                                  <div className="space-y-2">
                                    <div className="flex items-center space-x-2">
                                      <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.05"
                                        value={numericValue}
                                        onChange={(e) => updateWeight(key as keyof RetrievalWeights, parseFloat(e.target.value))}
                                        className="flex-1 h-2 rounded-lg appearance-none cursor-pointer"
                                        style={{
                                          background: `linear-gradient(to right, #${color === 'purple' ? '8b5cf6' : color === 'green' ? '10b981' : color === 'blue' ? '3b82f6' : color === 'yellow' ? 'f59e0b' : 'ef4444'} 0%, #${color === 'purple' ? '8b5cf6' : color === 'green' ? '10b981' : color === 'blue' ? '3b82f6' : color === 'yellow' ? 'f59e0b' : 'ef4444'} ${numericValue * 100}%, #e5e7eb ${numericValue * 100}%, #e5e7eb 100%)`,
                                          WebkitAppearance: 'none',
                                          appearance: 'none',
                                          outline: 'none',
                                          opacity: 1
                                        }}
                                      />
                                      <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                        {Math.round(numericValue * 100)}%
                                      </span>
                                    </div>
                                    <p className="text-xs text-gray-500">{description}</p>
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Weight Validation */}
                          <div className={`p-3 rounded-lg border ${
                            isValidTotal 
                              ? 'bg-green-50 border-green-200' 
                              : 'bg-yellow-50 border-yellow-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${
                                isValidTotal ? 'bg-green-500' : 'bg-yellow-500'
                              }`}></div>
                              <span className={`text-sm font-medium ${
                                isValidTotal ? 'text-green-800' : 'text-yellow-800'
                              }`}>
                                Total: {Math.round(totalWeight * 100)}%
                                {!isValidTotal && (
                                  <span className="text-red-600 ml-2">(Should total 100%)</span>
                                )}
                              </span>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="flex items-center justify-end space-x-3 pt-2 border-t border-gray-200">
                            <button
                              onClick={cancelEditing}
                              className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2"
                            >
                              <XMarkIcon className="w-4 h-4" />
                              <span>Cancel</span>
                            </button>
                            <button
                              onClick={saveChanges}
                              disabled={saving || !isValidTotal}
                              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                            >
                              <CheckIcon className="w-4 h-4" />
                              <span>{saving ? 'Saving...' : 'Save'}</span>
                            </button>
                          </div>
                        </div>
                      ) : (
                        /* View Mode */
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            {weightConfigs.map(({ key, label, color }) => {
                              const value = weight[key as keyof RetrievalWeights];
                              const numericValue = Number(value);

                              return (
                                <div key={key} className="text-center">
                                  <div className="text-2xl font-bold text-gray-900">
                                    {Math.round(numericValue * 100)}%
                                  </div>
                                  <div className="text-sm text-gray-600">{label}</div>
                                  <div className={`w-full h-2 mt-1 rounded-full bg-${color}-100`}>
                                    <div 
                                      className={`h-2 rounded-full bg-${color}-500`}
                                      style={{ width: `${numericValue * 100}%` }}
                                    ></div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                          
                          {/* Total Weight Display in View Mode */}
                          <div className={`p-3 rounded-lg border ${
                            isValidTotal 
                              ? 'bg-green-50 border-green-200' 
                              : 'bg-yellow-50 border-yellow-200'
                          }`}>
                            <div className="flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${
                                isValidTotal ? 'bg-green-500' : 'bg-yellow-500'
                              }`}></div>
                              <span className={`text-sm font-medium ${
                                isValidTotal ? 'text-green-800' : 'text-yellow-800'
                              }`}>
                                Total: {Math.round(totalWeight * 100)}%
                                {!isValidTotal && (
                                  <span className="text-red-600 ml-2">(Should total 100%)</span>
                                )}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
