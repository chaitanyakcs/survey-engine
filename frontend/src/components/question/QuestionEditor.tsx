import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Question } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { 
  questionTypeLabels, 
  requiresOptions, 
  requiresScaleLabels,
  isSpecializedType,
  getDefaultOptions,
  getDefaultScaleLabels,
  validateQuestion
} from '../../utils/questionUtils';
import { useQuestionParser } from '../../hooks/useQuestionParser';

// Import specialized editors
import {
  MatrixLikertEditor,
  ConstantSumEditor,
  GaborGrangerEditor,
  NumericGridEditor,
  NumericOpenEditor
} from '../editors';

interface QuestionEditorProps {
  question: Question;
  onSave: (updatedQuestion: Question) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  hideSaveButton?: boolean; // New prop to hide save button
}

export const QuestionEditor: React.FC<QuestionEditorProps> = ({
  question,
  onSave,
  onCancel,
  isLoading = false,
  hideSaveButton = false
}) => {
  const [editedQuestion, setEditedQuestion] = useState<Question>(question);
  const [errors, setErrors] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  
  const { parsedData, validateParsedData } = useQuestionParser(question);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Update edited question when question prop changes
  useEffect(() => {
    setEditedQuestion(question);
    setErrors([]);
    setSaveError(null);
  }, [question]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Validate question on changes
  useEffect(() => {
    const validationErrors = validateQuestion(editedQuestion);
    const parsedErrors = validateParsedData();
    setErrors([...validationErrors, ...parsedErrors]);
  }, [editedQuestion, validateParsedData]);

  // Debounced auto-save function
  const debouncedSave = useCallback(async (questionToSave: Question) => {
    if (hideSaveButton && onSave) {
      try {
        console.log('💾 [QuestionEditor] Auto-saving question:', questionToSave.id);
        await onSave(questionToSave);
        console.log('✅ [QuestionEditor] Auto-save successful');
      } catch (error) {
        console.error('❌ [QuestionEditor] Auto-save failed:', error);
      }
    }
  }, [hideSaveButton, onSave]);

  const updateQuestionField = (field: keyof Question, value: any) => {
    const updatedQuestion = { ...editedQuestion, [field]: value };
    setEditedQuestion(updatedQuestion);
    
    // Auto-save when in survey edit mode (hideSaveButton = true)
    if (hideSaveButton) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      
      // Set new timeout for debounced save
      saveTimeoutRef.current = setTimeout(() => {
        debouncedSave(updatedQuestion);
      }, 1000); // 1 second debounce
    }
  };

  const handleQuestionTypeChange = (newType: string) => {
    const updatedQuestion = { ...editedQuestion, type: newType as any };
    
    // Set default options if required
    if (requiresOptions(newType)) {
      updatedQuestion.options = getDefaultOptions(newType);
    } else {
      updatedQuestion.options = undefined;
    }
    
    // Set default scale labels if required
    if (requiresScaleLabels(newType)) {
      updatedQuestion.scale_labels = getDefaultScaleLabels();
    } else {
      updatedQuestion.scale_labels = undefined;
    }
    
    setEditedQuestion(updatedQuestion);
    
    // Auto-save when in survey edit mode
    if (hideSaveButton) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      
      // Set new timeout for debounced save
      saveTimeoutRef.current = setTimeout(() => {
        debouncedSave(updatedQuestion);
      }, 1000); // 1 second debounce
    }
  };

  // Wrapper function for specialized editors that also triggers auto-save
  const handleSpecializedUpdate = (updatedQuestion: Question) => {
    setEditedQuestion(updatedQuestion);
    
    // Auto-save when in survey edit mode
    if (hideSaveButton) {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      
      // Set new timeout for debounced save
      saveTimeoutRef.current = setTimeout(() => {
        debouncedSave(updatedQuestion);
      }, 1000); // 1 second debounce
    }
  };

  const handleSave = async () => {
    if (errors.length > 0) {
      setSaveError('Please fix validation errors before saving');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    
    try {
      await onSave(editedQuestion);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save question');
    } finally {
      setIsSaving(false);
    }
  };

  const renderSpecializedEditor = () => {
    switch (editedQuestion.type) {
      case 'matrix_likert':
        return (
          <MatrixLikertEditor
            question={editedQuestion}
            parsedData={parsedData}
            onUpdate={handleSpecializedUpdate}
            errors={errors}
          />
        );
      case 'constant_sum':
        return (
          <ConstantSumEditor
            question={editedQuestion}
            parsedData={parsedData}
            onUpdate={handleSpecializedUpdate}
            errors={errors}
          />
        );
      case 'gabor_granger':
        return (
          <GaborGrangerEditor
            question={editedQuestion}
            parsedData={parsedData}
            onUpdate={handleSpecializedUpdate}
            errors={errors}
          />
        );
      case 'numeric_grid':
        return (
          <NumericGridEditor
            question={editedQuestion}
            parsedData={parsedData}
            onUpdate={handleSpecializedUpdate}
            errors={errors}
          />
        );
      case 'numeric_open':
        return (
          <NumericOpenEditor
            question={editedQuestion}
            parsedData={parsedData}
            onUpdate={handleSpecializedUpdate}
            errors={errors}
          />
        );
      default:
        return null;
    }
  };

  const renderStandardEditor = () => (
    <div className="space-y-4">
      {/* Question Text */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Question Text *
        </label>
        <textarea
          value={editedQuestion.text || ''}
          onChange={(e) => updateQuestionField('text', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={3}
          placeholder="Enter your question text..."
        />
        {errors.some(e => e.includes('text')) && (
          <p className="mt-1 text-sm text-red-600">Question text is required</p>
        )}
      </div>

      {/* Question Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Question Type *
        </label>
        <select
          value={editedQuestion.type}
          onChange={(e) => handleQuestionTypeChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          {Object.entries(questionTypeLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Options for choice-based questions */}
      {requiresOptions(editedQuestion.type) && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Options *
          </label>
          <div className="space-y-2">
            {(editedQuestion.options || []).map((option, index) => (
              <div key={index} className="flex items-center space-x-2">
                <input
                  type="text"
                  value={option}
                  onChange={(e) => {
                    const newOptions = [...(editedQuestion.options || [])];
                    newOptions[index] = e.target.value;
                    updateQuestionField('options', newOptions);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={`Option ${index + 1}`}
                />
                <button
                  onClick={() => {
                    const newOptions = (editedQuestion.options || []).filter((_, i) => i !== index);
                    updateQuestionField('options', newOptions);
                  }}
                  className="px-2 py-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                  type="button"
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              onClick={() => {
                const newOptions = [...(editedQuestion.options || []), ''];
                updateQuestionField('options', newOptions);
              }}
              className="px-3 py-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded border border-blue-200"
              type="button"
            >
              + Add Option
            </button>
          </div>
          {errors.some(e => e.includes('options')) && (
            <p className="mt-1 text-sm text-red-600">Options are required for this question type</p>
          )}
        </div>
      )}

      {/* Scale Labels for scale questions */}
      {requiresScaleLabels(editedQuestion.type) && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Scale Labels *
          </label>
          <div className="space-y-2">
            {editedQuestion.scale_labels && Object.entries(editedQuestion.scale_labels).map(([key, label]) => (
              <div key={key} className="flex items-center space-x-2">
                <span className="w-16 text-sm text-gray-600">{key}:</span>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => {
                    const newScaleLabels = { ...editedQuestion.scale_labels };
                    newScaleLabels[key] = e.target.value;
                    updateQuestionField('scale_labels', newScaleLabels);
                  }}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            ))}
          </div>
          {errors.some(e => e.includes('scale')) && (
            <p className="mt-1 text-sm text-red-600">Scale labels are required for scale questions</p>
          )}
        </div>
      )}

      {/* Additional Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <input
            type="text"
            value={editedQuestion.category || ''}
            onChange={(e) => updateQuestionField('category', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., screening, pricing"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Methodology
          </label>
          <input
            type="text"
            value={editedQuestion.methodology || ''}
            onChange={(e) => updateQuestionField('methodology', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., van_westendorp"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={editedQuestion.description || ''}
          onChange={(e) => updateQuestionField('description', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={2}
          placeholder="Additional context or instructions..."
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="required"
          checked={Boolean(editedQuestion.required)}
          onChange={(e) => updateQuestionField('required', e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="required" className="ml-2 block text-sm text-gray-900">
          Required question
        </label>
      </div>
    </div>
  );

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading question editor..." />;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Edit Question
        </h3>
        <p className="text-sm text-gray-600">
          Type: {questionTypeLabels[editedQuestion.type] || editedQuestion.type}
        </p>
      </div>

      {/* Error Display */}
      {saveError && (
        <ErrorDisplay 
          error={saveError} 
          onRetry={() => setSaveError(null)}
          className="mb-4"
        />
      )}

      {/* Validation Errors */}
      {errors.length > 0 && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-red-800 mb-2">Please fix the following errors:</h4>
          <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Editor Content */}
      {isSpecializedType(editedQuestion.type) ? renderSpecializedEditor() : renderStandardEditor()}

      {/* Action Buttons */}
      <div className="mt-6 flex justify-end space-x-3">
        {!hideSaveButton && (
          <>
            <button
              onClick={onCancel}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || errors.length > 0}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? (
                <div className="flex items-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Saving...</span>
                </div>
              ) : (
                'Save Changes'
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default QuestionEditor;
