import React, { useState, useEffect, useMemo } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Question, QuestionAnnotation } from '../types';
import MatrixLikert from './MatrixLikert';
import ConstantSum from './ConstantSum';
import GaborGranger from './GaborGranger';
import NumericGrid from './NumericGrid';
import NumericOpen from './NumericOpen';
import { ChevronDownIcon, ChevronUpIcon, TagIcon } from '@heroicons/react/24/outline';

interface QuestionCardProps {
  question: Question;
  index: number;
  onUpdate: (updatedQuestion: Question) => void;
  onDelete: () => void;
  onMove: (questionId: string, direction: 'up' | 'down') => void;
  canMoveUp: boolean;
  canMoveDown: boolean;
  isEditingSurvey: boolean;
  isAnnotationMode: boolean;
  onOpenAnnotation?: (question: Question) => void;
  annotation?: QuestionAnnotation;
  disableHighlighting?: boolean; // New prop to disable selection highlighting
}

const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  index,
  onUpdate,
  onDelete,
  onMove,
  canMoveUp,
  canMoveDown,
  isEditingSurvey,
  isAnnotationMode,
  onOpenAnnotation,
  annotation,
  disableHighlighting = false
}) => {
  const { selectedQuestionId, setSelectedQuestion } = useAppStore();
  const isSelected = selectedQuestionId === question.id;
  
  // Inline editing states for each field
  const [isEditingText, setIsEditingText] = useState(false);
  const [editedText, setEditedText] = useState(question.text);
  
  const [isEditingDescription, setIsEditingDescription] = useState(false);
  const [editedDescription, setEditedDescription] = useState(question.description || '');
  
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [editedLabel, setEditedLabel] = useState(question.label || '');
  
  const [isEditingCategory, setIsEditingCategory] = useState(false);
  const [editedCategory, setEditedCategory] = useState(question.category || '');
  
  const [editingOptionIndex, setEditingOptionIndex] = useState<number | null>(null);
  const [editedOptionValue, setEditedOptionValue] = useState('');
  
  const [isSaving, setIsSaving] = useState(false);

  // Generate question text fallback - use text, label, or generate from ID
  const getQuestionText = useMemo(() => {
    if (question.text && question.text.trim()) {
      return question.text;
    }
    // Fallback to label if available
    if (question.label && question.label.trim()) {
      // Convert label to readable format (e.g., "informed_consent" -> "Informed Consent")
      const labelText = question.label
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
      return labelText;
    }
    // Fallback to question ID or default message
    if (question.id) {
      // Extract meaningful part from ID (e.g., "Q1 validation_check" -> "Validation Check")
      const idParts = question.id.replace(/^Q\d+\s*/i, '').replace('_', ' ').split(' ');
      const readableId = idParts.map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
      return readableId || `${question.id} - Please answer the question below`;
    }
    return 'Question text not available';
  }, [question.text, question.label, question.id]);

  // Sync state when question changes
  useEffect(() => {
    setEditedText(getQuestionText);
    setEditedDescription(question.description || '');
    setEditedLabel(question.label || '');
    setEditedCategory(question.category || '');
  }, [question, getQuestionText]);

  // Handler functions for inline editing
  const handleTextSave = async () => {
    if (editedText.trim() === '') {
      alert('Question text cannot be empty');
      return;
    }
    setIsSaving(true);
    try {
      const updated = { ...question, text: editedText };
      await onUpdate(updated);
      setIsEditingText(false);
    } catch (error) {
      console.error('Failed to save question text:', error);
      alert('Failed to save question text');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTextCancel = () => {
    setEditedText(question.text);
    setIsEditingText(false);
  };

  const handleDescriptionSave = async () => {
    setIsSaving(true);
    try {
      const updated = { ...question, description: editedDescription || undefined };
      await onUpdate(updated);
      setIsEditingDescription(false);
    } catch (error) {
      console.error('Failed to save description:', error);
      alert('Failed to save description');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDescriptionCancel = () => {
    setEditedDescription(question.description || '');
    setIsEditingDescription(false);
  };

  const handleLabelSave = async () => {
    setIsSaving(true);
    try {
      const updated = { ...question, label: editedLabel || undefined };
      await onUpdate(updated);
      setIsEditingLabel(false);
    } catch (error) {
      console.error('Failed to save label:', error);
      alert('Failed to save label');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLabelCancel = () => {
    setEditedLabel(question.label || '');
    setIsEditingLabel(false);
  };

  const handleCategorySave = async () => {
    setIsSaving(true);
    try {
      const updated = { ...question, category: editedCategory || '' };
      await onUpdate(updated);
      setIsEditingCategory(false);
    } catch (error) {
      console.error('Failed to save category:', error);
      alert('Failed to save category');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCategoryCancel = () => {
    setEditedCategory(question.category || '');
    setIsEditingCategory(false);
  };

  const handleOptionSave = async (index: number) => {
    if (editedOptionValue.trim() === '') {
      alert('Option cannot be empty');
      return;
    }
    setIsSaving(true);
    try {
      const newOptions = [...(question.options || [])];
      newOptions[index] = editedOptionValue;
      const updated = { ...question, options: newOptions };
      await onUpdate(updated);
      setEditingOptionIndex(null);
      setEditedOptionValue('');
    } catch (error) {
      console.error('Failed to save option:', error);
      alert('Failed to save option');
    } finally {
      setIsSaving(false);
    }
  };

  const handleOptionCancel = () => {
    setEditingOptionIndex(null);
    setEditedOptionValue('');
  };

  const handleOptionEdit = (index: number, value: string) => {
    setEditingOptionIndex(index);
    setEditedOptionValue(value);
  };


  return (
    <div 
      className={`
        border rounded-lg p-4 transition-all duration-200
        ${disableHighlighting 
          ? 'border-gray-200' 
          : `cursor-pointer ${isSelected ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'}`
        }
      `}
      onClick={disableHighlighting ? undefined : () => {
        if (isAnnotationMode && onOpenAnnotation) {
          // Open annotation pane
          onOpenAnnotation(question);
        } else {
          // Normal selection behavior
          setSelectedQuestion(isSelected ? undefined : question.id);
        }
      }}
    >
      {/* Question Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {question.type !== 'instruction' && (
            <span className="text-sm font-medium text-gray-500">Q{index + 1}</span>
          )}
          {question.methodology && question.type !== 'instruction' && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
              {question.methodology}
            </span>
          )}
          <span className={`
            inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
            ${question.category === 'screening' ? 'bg-yellow-100 text-yellow-800' :
              question.category === 'pricing' ? 'bg-green-100 text-green-800' :
              question.category === 'features' ? 'bg-blue-100 text-blue-800' :
              'bg-gray-100 text-gray-800'}
          `}>
            {question.category}
          </span>
          {annotation && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              <TagIcon className="w-3 h-3" />
            </span>
          )}
          {/* Display labels from annotations (single source of truth) */}
          {(() => {
            // Use annotation labels if available, otherwise show nothing
            const labels = annotation?.labels;
            const removedLabels = new Set(annotation?.removedLabels || []);
            
            if (labels && Array.isArray(labels) && labels.length > 0) {
              const visibleLabels = labels.filter(label => !removedLabels.has(label));
              
              if (visibleLabels.length > 0) {
                return (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {visibleLabels.map((label, index) => (
                      <span 
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                );
              }
            }
            return null;
          })()}
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditingSurvey && (
            <>
              <div className="flex flex-col space-y-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMove(question.id, 'up');
                  }}
                  disabled={!canMoveUp}
                  className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  title="Move up"
                >
                  <ChevronUpIcon className="h-3 w-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onMove(question.id, 'down');
                  }}
                  disabled={!canMoveDown}
                  className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  title="Move down"
                >
                  <ChevronDownIcon className="h-3 w-3" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Question Content */}
      <div className="mb-4">
        <div>
          {/* Question Text - Always show question text for all question types (except instructions which have their own display, and specialized types which render their own) */}
          {!isAnnotationMode && question.type !== 'instruction' && !['matrix_likert', 'constant_sum', 'gabor_granger', 'numeric_grid', 'numeric_open'].includes(question.type) && (
            <div className="mb-3">
              {isEditingSurvey && isEditingText ? (
                <div className="flex items-start space-x-2">
                  <div className="flex-1">
                    <textarea
                      value={editedText}
                      onChange={(e) => setEditedText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          handleTextSave();
                        } else if (e.key === 'Escape') {
                          handleTextCancel();
                        }
                      }}
                      className="w-full text-lg font-medium text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      rows={3}
                      autoFocus
                      disabled={isSaving}
                    />
                  </div>
                  <div className="flex flex-col space-y-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTextSave();
                      }}
                      disabled={isSaving}
                      className="text-green-600 hover:text-green-800 disabled:opacity-50"
                      title="Save"
                    >
                      ✓
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleTextCancel();
                      }}
                      disabled={isSaving}
                      className="text-red-600 hover:text-red-800 disabled:opacity-50"
                      title="Cancel"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <h3 
                  className={`text-lg font-medium text-gray-900 mb-2 ${isEditingSurvey ? 'cursor-pointer hover:bg-gray-100 px-2 py-1 rounded' : ''}`}
                  onClick={(e) => {
                    if (isEditingSurvey) {
                      e.stopPropagation();
                      setIsEditingText(true);
                    }
                  }}
                  title={isEditingSurvey ? "Click to edit question text" : ""}
                >
                  {getQuestionText}
                </h3>
              )}
            </div>
          )}

          {/* AI Annotation Information */}
          {annotation && annotation.aiGenerated && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    🤖 AI Annotated
                  </span>
                  {annotation.aiConfidence && (
                    <span className="text-xs text-blue-600">
                      Confidence: {Math.round(annotation.aiConfidence * 100)}%
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2 text-xs text-gray-600">
                  <span>Quality: {annotation.quality}/5</span>
                  <span>•</span>
                  <span>Relevant: {annotation.relevant}/5</span>
                </div>
              </div>
              {annotation.comment && (
                <p className="text-sm text-gray-700 italic">
                  "{annotation.comment}"
                </p>
              )}
              <div className="mt-2 grid grid-cols-5 gap-2 text-xs">
                <div className="text-center">
                  <div className="font-medium text-gray-600">Methodology</div>
                  <div className="text-blue-600">{annotation.pillars.methodologicalRigor}/5</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-gray-600">Content</div>
                  <div className="text-blue-600">{annotation.pillars.contentValidity}/5</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-gray-600">Experience</div>
                  <div className="text-blue-600">{annotation.pillars.respondentExperience}/5</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-gray-600">Analytics</div>
                  <div className="text-blue-600">{annotation.pillars.analyticalValue}/5</div>
                </div>
                <div className="text-center">
                  <div className="font-medium text-gray-600">Business</div>
                  <div className="text-blue-600">{annotation.pillars.businessImpact}/5</div>
                </div>
              </div>
              {/* Debug logging for q1 */}
              {question.id === 'q1' && (
                <div className="text-xs text-red-600 mt-1">
                  Debug: AI Generated: {annotation.aiGenerated ? 'Yes' : 'No'}, 
                  Confidence: {annotation.aiConfidence}, 
                  Quality: {annotation.quality}, 
                  Relevant: {annotation.relevant}
                </div>
              )}
            </div>
          )}

          {/* Question Type - Non-Editable */}
          <div className="text-sm text-gray-600 mb-3">
            Type: <span className="font-medium">{question.type}</span>
            {isEditingSurvey && <span className="text-xs text-gray-500 ml-2">(non-editable)</span>}
          </div>

          {/* Question Category - Inline Editable */}
          {isEditingSurvey && (
            <div className="mb-3">
              <label className="text-xs font-medium text-gray-500 mb-1 block">Category</label>
              {isEditingCategory ? (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={editedCategory}
                    onChange={(e) => setEditedCategory(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCategorySave();
                      } else if (e.key === 'Escape') {
                        handleCategoryCancel();
                      }
                    }}
                    className="flex-1 text-sm text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter category..."
                    autoFocus
                    disabled={isSaving}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCategorySave();
                    }}
                    disabled={isSaving}
                    className="text-green-600 hover:text-green-800 disabled:opacity-50"
                    title="Save"
                  >
                    ✓
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCategoryCancel();
                    }}
                    disabled={isSaving}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    title="Cancel"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div 
                  className="text-sm text-gray-700 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditingCategory(true);
                  }}
                  title="Click to edit category"
                >
                  {question.category || <span className="text-gray-400 italic">Click to add category...</span>}
                </div>
              )}
            </div>
          )}

          {/* Question Description - Inline Editable */}
          {isEditingSurvey && (
            <div className="mb-3">
              <label className="text-xs font-medium text-gray-500 mb-1 block">Description</label>
              {isEditingDescription ? (
                <div className="flex items-start space-x-2">
                  <textarea
                    value={editedDescription}
                    onChange={(e) => setEditedDescription(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.ctrlKey) {
                        handleDescriptionSave();
                      } else if (e.key === 'Escape') {
                        handleDescriptionCancel();
                      }
                    }}
                    className="flex-1 text-sm text-gray-600 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={2}
                    placeholder="Enter description..."
                    autoFocus
                    disabled={isSaving}
                  />
                  <div className="flex flex-col space-y-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDescriptionSave();
                      }}
                      disabled={isSaving}
                      className="text-green-600 hover:text-green-800 disabled:opacity-50"
                      title="Save"
                    >
                      ✓
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDescriptionCancel();
                      }}
                      disabled={isSaving}
                      className="text-red-600 hover:text-red-800 disabled:opacity-50"
                      title="Cancel"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ) : (
                <div 
                  className="text-sm text-gray-600 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditingDescription(true);
                  }}
                  title="Click to edit description"
                >
                  {question.description || <span className="text-gray-400 italic">Click to add description...</span>}
                </div>
              )}
            </div>
          )}

          {/* Question Label (Programming Notes) - Inline Editable */}
          {isEditingSurvey && (
            <div className="mb-3">
              <label className="text-xs font-medium text-gray-500 mb-1 block">Label / Programming Notes</label>
              {isEditingLabel ? (
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={editedLabel}
                    onChange={(e) => setEditedLabel(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleLabelSave();
                      } else if (e.key === 'Escape') {
                        handleLabelCancel();
                      }
                    }}
                    className="flex-1 text-sm text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter label or programming notes..."
                    autoFocus
                    disabled={isSaving}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLabelSave();
                    }}
                    disabled={isSaving}
                    className="text-green-600 hover:text-green-800 disabled:opacity-50"
                    title="Save"
                  >
                    ✓
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLabelCancel();
                    }}
                    disabled={isSaving}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                    title="Cancel"
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <div 
                  className="text-sm text-gray-700 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditingLabel(true);
                  }}
                  title="Click to edit label"
                >
                  {question.label || <span className="text-gray-400 italic">Click to add label...</span>}
                </div>
              )}
            </div>
          )}
            
            {/* Specialized Question Type Components */}
            {question.type === 'matrix_likert' && (
              <MatrixLikert 
                question={question} 
                isPreview={true}
                showQuestionText={!isAnnotationMode}
              />
            )}
            
            {question.type === 'constant_sum' && (
              <ConstantSum 
                question={question} 
                isPreview={true}
                showQuestionText={!isAnnotationMode}
              />
            )}
            
            {question.type === 'gabor_granger' && (
              <GaborGranger 
                question={question} 
                isPreview={true}
                showQuestionText={!isAnnotationMode}
              />
            )}
            
            {question.type === 'numeric_grid' && (
              <NumericGrid 
                question={question} 
                isPreview={true}
                showQuestionText={!isAnnotationMode}
              />
            )}
            
            {question.type === 'numeric_open' && (
              <NumericOpen 
                question={question} 
                isPreview={true}
                showQuestionText={!isAnnotationMode}
              />
            )}
            
            {question.type === 'maxdiff' && question.features && question.features.length > 0 && (
              <div className="space-y-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-blue-900 mb-4">
                    Select ONE feature as MOST important and ONE as LEAST important:
                  </p>
                  
                  {/* Header row */}
                  <div className="grid grid-cols-[1fr_auto_auto] gap-4 mb-2 pb-2 border-b border-blue-300">
                    <div className="text-xs font-semibold text-blue-900">Feature</div>
                    <div className="text-xs font-semibold text-green-700 text-center w-20">MOST</div>
                    <div className="text-xs font-semibold text-red-700 text-center w-20">LEAST</div>
                  </div>
                  
                  {/* Feature rows */}
                  <div className="space-y-1">
                    {question.features.map((feature, idx) => (
                      <div key={idx} className="grid grid-cols-[1fr_auto_auto] gap-4 items-center p-2 bg-white rounded hover:bg-gray-50">
                        <span className="text-sm text-gray-700">{feature}</span>
                        <div className="flex justify-center w-20">
                          <input 
                            type="radio" 
                            name={`${question.id}_most`} 
                            value={feature}
                            disabled 
                            className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300" 
                          />
                        </div>
                        <div className="flex justify-center w-20">
                          <input 
                            type="radio" 
                            name={`${question.id}_least`} 
                            value={feature}
                            disabled 
                            className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300" 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Multiple Select Questions */}
            {question.type === 'multiple_select' && question.options && question.options.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-700">Options:</h4>
                {question.options.map((option, idx) => (
                  <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <input
                      type="checkbox"
                      disabled
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-3"
                    />
                    {isEditingSurvey && editingOptionIndex === idx ? (
                      <div className="flex items-center space-x-2 flex-1">
                        <input
                          type="text"
                          value={editedOptionValue}
                          onChange={(e) => setEditedOptionValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleOptionSave(idx);
                            } else if (e.key === 'Escape') {
                              handleOptionCancel();
                            }
                          }}
                          className="flex-1 text-sm text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          autoFocus
                          disabled={isSaving}
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOptionSave(idx);
                          }}
                          disabled={isSaving}
                          className="text-green-600 hover:text-green-800 disabled:opacity-50"
                          title="Save"
                        >
                          ✓
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOptionCancel();
                          }}
                          disabled={isSaving}
                          className="text-red-600 hover:text-red-800 disabled:opacity-50"
                          title="Cancel"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <span 
                        className={`text-sm text-gray-700 flex-1 ${isEditingSurvey ? 'cursor-pointer hover:bg-gray-100 px-2 py-1 rounded' : ''}`}
                        onClick={(e) => {
                          if (isEditingSurvey) {
                            e.stopPropagation();
                            handleOptionEdit(idx, option);
                          }
                        }}
                        title={isEditingSurvey ? "Click to edit option" : ""}
                      >
                        {option}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Standard Question Types */}
            {!['matrix_likert', 'constant_sum', 'gabor_granger', 'numeric_grid', 'numeric_open', 'likert', 'multiple_select', 'yes_no'].includes(question.type) && (
              <>
                {/* Question Options */}
                {question.options && question.options.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">Options:</h4>
                    {question.options.map((option, idx) => (
                      <div key={idx} className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-600 rounded-full text-sm font-medium mr-3">
                          {idx + 1}
                        </div>
                        {isEditingSurvey && editingOptionIndex === idx ? (
                          <div className="flex items-center space-x-2 flex-1">
                            <input
                              type="text"
                              value={editedOptionValue}
                              onChange={(e) => setEditedOptionValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleOptionSave(idx);
                                } else if (e.key === 'Escape') {
                                  handleOptionCancel();
                                }
                              }}
                              className="flex-1 text-sm text-gray-900 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              autoFocus
                              disabled={isSaving}
                            />
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOptionSave(idx);
                              }}
                              disabled={isSaving}
                              className="text-green-600 hover:text-green-800 disabled:opacity-50"
                              title="Save"
                            >
                              ✓
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOptionCancel();
                              }}
                              disabled={isSaving}
                              className="text-red-600 hover:text-red-800 disabled:opacity-50"
                              title="Cancel"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <span 
                            className={`text-sm text-gray-700 flex-1 ${isEditingSurvey ? 'cursor-pointer hover:bg-gray-100 px-2 py-1 rounded' : ''}`}
                            onClick={(e) => {
                              if (isEditingSurvey) {
                                e.stopPropagation();
                                handleOptionEdit(idx, option);
                              }
                            }}
                            title={isEditingSurvey ? "Click to edit option" : ""}
                          >
                            {option}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Special Question Types - Instruction */}
                {question.type === 'instruction' && (
                  <>
                    {question.label && (question.label.includes('Technical') || question.label.includes('Programmer')) ? (
                      // Technical instruction - distinct styling
                      <div className="bg-gray-100 border-l-4 border-gray-500 p-4 rounded-r-lg">
                        <div className="mb-2">
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="w-5 h-5 bg-gray-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-xs font-bold">i</span>
                            </div>
                            <h4 className="text-sm font-semibold text-gray-700">Instructions</h4>
                          </div>
                        </div>
                        {isEditingSurvey && isEditingText ? (
                          <div className="flex items-start space-x-2">
                            <textarea
                              value={editedText}
                              onChange={(e) => setEditedText(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && e.ctrlKey) {
                                  handleTextSave();
                                } else if (e.key === 'Escape') {
                                  handleTextCancel();
                                }
                              }}
                              className="flex-1 text-xs text-gray-700 font-mono bg-white border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                              rows={3}
                              autoFocus
                              disabled={isSaving}
                            />
                            <div className="flex flex-col space-y-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTextSave();
                                }}
                                disabled={isSaving}
                                className="text-green-600 hover:text-green-800 disabled:opacity-50"
                                title="Save"
                              >
                                ✓
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTextCancel();
                                }}
                                disabled={isSaving}
                                className="text-red-600 hover:text-red-800 disabled:opacity-50"
                                title="Cancel"
                              >
                                ✕
                              </button>
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-gray-700 font-mono whitespace-pre-wrap bg-white p-3 rounded border border-gray-300">
                            {question.text}
                          </p>
                        )}
                        {question.description && (
                          <p className="text-xs text-gray-500 italic mt-2">
                            {question.description}
                          </p>
                        )}
                      </div>
                    ) : (
                      // Regular respondent-facing instruction - friendly styling
                      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/>
                          </svg>
                          <h4 className="text-sm font-semibold text-blue-800">Instruction</h4>
                        </div>
                        {isEditingSurvey && isEditingText ? (
                          <div className="flex items-start space-x-2">
                            <textarea
                              value={editedText}
                              onChange={(e) => setEditedText(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && e.ctrlKey) {
                                  handleTextSave();
                                } else if (e.key === 'Escape') {
                                  handleTextCancel();
                                }
                              }}
                              className="flex-1 text-sm text-blue-700 bg-white border border-blue-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                              rows={3}
                              autoFocus
                              disabled={isSaving}
                            />
                            <div className="flex flex-col space-y-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTextSave();
                                }}
                                disabled={isSaving}
                                className="text-green-600 hover:text-green-800 disabled:opacity-50"
                                title="Save"
                              >
                                ✓
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleTextCancel();
                                }}
                                disabled={isSaving}
                                className="text-red-600 hover:text-red-800 disabled:opacity-50"
                                title="Cancel"
                              >
                                ✕
                              </button>
                            </div>
                          </div>
                        ) : (
                          <p 
                            className={`text-sm text-blue-700 ${isEditingSurvey ? 'cursor-pointer hover:bg-blue-100 px-2 py-1 rounded' : ''}`}
                            onClick={(e) => {
                              if (isEditingSurvey) {
                                e.stopPropagation();
                                setIsEditingText(true);
                              }
                            }}
                            title={isEditingSurvey ? "Click to edit instruction text" : ""}
                          >
                            {question.text}
                          </p>
                        )}
                      </div>
                    )}
                  </>
                )}
              </>
            )}

            {/* Van Westendorp Questions */}
            {question.type === 'van_westendorp' && (
              <div className="space-y-3">
                {!isAnnotationMode && (
                  <div className="text-base font-medium text-gray-900">
                    {question.text}
                  </div>
                )}
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-orange-900 mb-2">Van Westendorp Price Sensitivity</div>
                  <div className="text-xs text-orange-800">
                    This question helps determine optimal pricing by asking about price perceptions.
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Price:</span>
                  <input
                    type="text"
                    disabled={true}
                    className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                    placeholder="$0.00"
                  />
                </div>
              </div>
            )}

            {/* Dropdown Questions */}
            {question.type === 'dropdown' && (
              <div className="space-y-3">
                {!isAnnotationMode && (
                  <div className="text-base font-medium text-gray-900">
                    {question.text}
                  </div>
                )}
                <div className="relative">
                  <select
                    disabled={true}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  >
                    <option value="">Select an option...</option>
                    {question.options?.map((option, index) => (
                      <option key={index} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Conjoint Questions */}
            {question.type === 'conjoint' && (
              <div className="space-y-3">
                {!isAnnotationMode && (
                  <div className="text-base font-medium text-gray-900">
                    {question.text}
                  </div>
                )}
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-purple-900 mb-2">Conjoint Analysis</div>
                  <div className="text-xs text-purple-800">
                    This question presents product combinations to understand feature preferences.
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  Conjoint analysis requires specialized presentation. Please review the raw JSON for detailed configuration.
                </div>
              </div>
            )}

            {/* Yes/No Questions */}
            {question.type === 'yes_no' && (
              <div className="space-y-2">
                {question.options?.map((option, index) => (
                  <label key={index} className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name={question.id}
                      value={option}
                      disabled={true}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{option}</span>
                  </label>
                ))}
              </div>
            )}

            {/* Unknown Question Type */}
            {!['multiple_choice', 'scale', 'ranking', 'text', 'instruction', 'single_choice', 'matrix', 'numeric', 'date', 'boolean', 'open_text', 'multiple_select', 'matrix_likert', 'constant_sum', 'numeric_grid', 'numeric_open', 'likert', 'open_end', 'display_only', 'single_open', 'multiple_open', 'open_ended', 'gabor_granger', 'maxdiff', 'van_westendorp', 'dropdown', 'conjoint', 'yes_no'].includes(question.type) && (
              <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-warning-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium text-warning-800">Unknown Question Type: {question.type}</span>
                </div>
                <p className="text-xs text-warning-700 mt-2">
                  This question type is not yet supported for preview. Please review the raw JSON.
                </p>
              </div>
            )}
          </div>
      </div>
    </div>
  );
};

export default QuestionCard;

