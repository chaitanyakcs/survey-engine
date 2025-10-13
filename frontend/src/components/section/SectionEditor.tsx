import React, { useState, useEffect } from 'react';
import { SurveySection } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorDisplay } from '../common/ErrorDisplay';

interface SectionEditorProps {
  section: SurveySection;
  onSave: (updatedSection: SurveySection) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  hideSaveButton?: boolean; // New prop to hide save button
}

export const SectionEditor: React.FC<SectionEditorProps> = ({
  section,
  onSave,
  onCancel,
  isLoading = false,
  hideSaveButton = false
}) => {
  const [editedSection, setEditedSection] = useState<SurveySection>(section);
  const [errors, setErrors] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Update edited section when section prop changes
  useEffect(() => {
    setEditedSection(section);
    setErrors([]);
    setSaveError(null);
  }, [section]);

  // Validate section on changes
  useEffect(() => {
    const validationErrors: string[] = [];
    
    if (!editedSection.title || editedSection.title.trim().length === 0) {
      validationErrors.push('Section title is required');
    }
    
    if (editedSection.title && editedSection.title.length > 200) {
      validationErrors.push('Section title must be less than 200 characters');
    }
    
    if (editedSection.description && editedSection.description.length > 1000) {
      validationErrors.push('Section description must be less than 1000 characters');
    }
    
    setErrors(validationErrors);
  }, [editedSection]);

  const updateSectionField = (field: keyof SurveySection, value: any) => {
    setEditedSection(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (errors.length > 0) {
      setSaveError('Please fix validation errors before saving');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    
    try {
      await onSave(editedSection);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save section');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner size="lg" text="Loading section editor..." />;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Edit Section
        </h3>
        <p className="text-sm text-gray-600">
          Section ID: {editedSection.id}
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
      <div className="space-y-4">
        {/* Section Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Section Title *
          </label>
          <input
            type="text"
            value={editedSection.title || ''}
            onChange={(e) => updateSectionField('title', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter section title..."
          />
          {errors.some(e => e.includes('title')) && (
            <p className="mt-1 text-sm text-red-600">Section title is required</p>
          )}
        </div>

        {/* Section Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Section Description
          </label>
          <textarea
            value={editedSection.description || ''}
            onChange={(e) => updateSectionField('description', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            placeholder="Enter section description..."
          />
          {errors.some(e => e.includes('description')) && (
            <p className="mt-1 text-sm text-red-600">Description must be less than 1000 characters</p>
          )}
        </div>

        {/* Section Order */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Section Order
          </label>
          <input
            type="number"
            value={editedSection.order || 0}
            onChange={(e) => updateSectionField('order', parseInt(e.target.value) || 0)}
            className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            min="0"
          />
          <p className="mt-1 text-xs text-gray-500">
            Lower numbers appear first in the survey
          </p>
        </div>

        {/* Questions Count */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Questions in this section:</h4>
          <p className="text-sm text-gray-600">
            {editedSection.questions?.length || 0} questions
          </p>
          {editedSection.questions && editedSection.questions.length > 0 && (
            <div className="mt-2 space-y-1">
              {editedSection.questions.map((question, index) => (
                <div key={question.id} className="text-xs text-gray-500">
                  {index + 1}. {question.text.substring(0, 50)}
                  {question.text.length > 50 && '...'}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex justify-end space-x-3">
        <button
          onClick={onCancel}
          disabled={isSaving}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
        >
          Cancel
        </button>
        {!hideSaveButton && (
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
        )}
      </div>
    </div>
  );
};

export default SectionEditor;
