import React, { useState, useEffect } from 'react';
import { GoldenSection, GoldenQuestion } from '../types';
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';
import { EditableCombobox } from './common/EditableCombobox';
import { getGoldenMetadataOptions } from '../services/api';

interface GoldenContentEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  content: GoldenSection | GoldenQuestion | null;
  type: 'section' | 'question';
  onSave: (id: string, updates: Partial<GoldenSection | GoldenQuestion>) => Promise<void>;
}

export const GoldenContentEditModal: React.FC<GoldenContentEditModalProps> = ({
  isOpen,
  onClose,
  content,
  type,
  onSave
}) => {
  const [formData, setFormData] = useState<Partial<GoldenSection | GoldenQuestion>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [metadataOptions, setMetadataOptions] = useState<{
    questionTypes: string[];
    questionSubtypes: string[];
    methodologyTags: string[];
    industryKeywords: string[];
    questionPatterns: string[];
  }>({
    questionTypes: [],
    questionSubtypes: [],
    methodologyTags: [],
    industryKeywords: [],
    questionPatterns: []
  });

  useEffect(() => {
    if (content) {
      setFormData({
        ...content,
        methodology_tags: content.methodology_tags || [],
        industry_keywords: content.industry_keywords || [],
        question_patterns: content.question_patterns || [],
        labels: content.labels || {}
      });
    }
  }, [content]);

  // Fetch metadata options on mount
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const options = await getGoldenMetadataOptions();
        setMetadataOptions({
          questionTypes: options.question_types || [],
          questionSubtypes: options.question_subtypes || [],
          methodologyTags: options.methodology_tags || [],
          industryKeywords: options.industry_keywords || [],
          questionPatterns: options.question_patterns || []
        });
      } catch (error) {
        console.error('Failed to fetch metadata options:', error);
      }
    };
    
    if (isOpen) {
      fetchMetadata();
    }
  }, [isOpen]);

  const handleSave = async () => {
    if (!content) return;
    
    setIsSaving(true);
    try {
      await onSave(content.id, formData);
      onClose();
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen || !content) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9998]">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">
            Edit Golden {type === 'section' ? 'Section' : 'Question'}
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Title (for sections) */}
          {type === 'section' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Section Title
              </label>
              <input
                type="text"
                value={(formData as GoldenSection).section_title || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, section_title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                placeholder="Enter section title"
              />
            </div>
          )}

          {/* Question Type (for questions) */}
          {type === 'question' && (
            <div className="grid grid-cols-2 gap-4">
              <EditableCombobox
                label="Question Type"
                value={(formData as GoldenQuestion).question_type || ''}
                options={metadataOptions.questionTypes}
                onChange={(value) => setFormData(prev => ({ ...prev, question_type: value as string }))}
                placeholder="Select or type question type"
                multiSelect={false}
                allowCustom={true}
              />
              <EditableCombobox
                label="Question Subtype"
                value={(formData as GoldenQuestion).question_subtype || ''}
                options={metadataOptions.questionSubtypes}
                onChange={(value) => setFormData(prev => ({ ...prev, question_subtype: value as string }))}
                placeholder="Select or type question subtype"
                multiSelect={false}
                allowCustom={true}
              />
            </div>
          )}

          {/* Section Type (for sections) */}
          {type === 'section' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Section Type
              </label>
              <select
                value={(formData as GoldenSection).section_type || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, section_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              >
                <option value="">Select type</option>
                <option value="demographics">Demographics</option>
                <option value="pricing">Pricing</option>
                <option value="satisfaction">Satisfaction</option>
                <option value="behavioral">Behavioral</option>
                <option value="preferences">Preferences</option>
                <option value="intent">Intent</option>
                <option value="awareness">Awareness</option>
                <option value="loyalty">Loyalty</option>
              </select>
            </div>
          )}

          {/* Content Text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {type === 'section' ? 'Section Text' : 'Question Text'}
            </label>
            <textarea
              value={type === 'section' ? (formData as GoldenSection).section_text || '' : (formData as GoldenQuestion).question_text || ''}
              onChange={(e) => setFormData(prev => ({ 
                ...prev, 
                [type === 'section' ? 'section_text' : 'question_text']: e.target.value 
              }))}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              placeholder={`Enter ${type} text`}
            />
          </div>

          {/* Methodology Tags */}
          <EditableCombobox
            label="Methodology Tags"
            value={formData.methodology_tags || []}
            options={metadataOptions.methodologyTags}
            onChange={(value) => setFormData(prev => ({ ...prev, methodology_tags: value as string[] }))}
            placeholder="Select or add methodology tags"
            multiSelect={true}
            allowCustom={true}
          />

          {/* Industry Keywords */}
          <EditableCombobox
            label="Industry Keywords"
            value={formData.industry_keywords || []}
            options={metadataOptions.industryKeywords}
            onChange={(value) => setFormData(prev => ({ ...prev, industry_keywords: value as string[] }))}
            placeholder="Select or add industry keywords"
            multiSelect={true}
            allowCustom={true}
          />

          {/* Question Patterns (for questions) */}
          {type === 'question' && (
            <EditableCombobox
              label="Question Patterns"
              value={formData.question_patterns || []}
              options={metadataOptions.questionPatterns}
              onChange={(value) => setFormData(prev => ({ ...prev, question_patterns: value as string[] }))}
              placeholder="Select or add question patterns"
              multiSelect={true}
              allowCustom={true}
            />
          )}

          {/* Suitability Score */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suitability Score (0.0 - 1.0)
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={formData.quality_score || 0}
                onChange={(e) => setFormData(prev => ({ ...prev, quality_score: parseFloat(e.target.value) }))}
                className="flex-1"
              />
              <span className="text-sm font-medium text-gray-700 min-w-[3rem]">
                {Math.round((formData.quality_score || 0) * 100)}%
              </span>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Combines quality rating and relevance assessment
            </div>
          </div>

          {/* Human Verified */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="human_verified"
              checked={formData.human_verified || false}
              onChange={(e) => setFormData(prev => ({ ...prev, human_verified: e.target.checked }))}
              className="h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded"
            />
            <label htmlFor="human_verified" className="ml-2 block text-sm text-gray-700">
              Human Verified
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <CheckIcon className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
