import React, { useState, useEffect } from 'react';
import { GoldenSection, GoldenQuestion } from '../types';
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';

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

  const handleMethodologyTagsChange = (value: string) => {
    const tags = value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setFormData(prev => ({ ...prev, methodology_tags: tags }));
  };

  const handleIndustryKeywordsChange = (value: string) => {
    const keywords = value.split(',').map(keyword => keyword.trim()).filter(keyword => keyword);
    setFormData(prev => ({ ...prev, industry_keywords: keywords }));
  };

  const handleQuestionPatternsChange = (value: string) => {
    const patterns = value.split(',').map(pattern => pattern.trim()).filter(pattern => pattern);
    setFormData(prev => ({ ...prev, question_patterns: patterns }));
  };

  if (!isOpen || !content) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Question Type
                </label>
                <select
                  value={(formData as GoldenQuestion).question_type || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, question_type: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                >
                  <option value="">Select type</option>
                  <option value="multiple_choice">Multiple Choice</option>
                  <option value="rating_scale">Rating Scale</option>
                  <option value="open_text">Open Text</option>
                  <option value="yes_no">Yes/No</option>
                  <option value="single_choice">Single Choice</option>
                  <option value="matrix">Matrix</option>
                  <option value="ranking">Ranking</option>
                  <option value="slider">Slider</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Question Subtype
                </label>
                <select
                  value={(formData as GoldenQuestion).question_subtype || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, question_subtype: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                >
                  <option value="">Select subtype</option>
                  <option value="likert_5">Likert 5-Point</option>
                  <option value="likert_7">Likert 7-Point</option>
                  <option value="binary">Binary</option>
                  <option value="text_input">Text Input</option>
                  <option value="dropdown">Dropdown</option>
                  <option value="radio">Radio</option>
                  <option value="checkbox">Checkbox</option>
                  <option value="nps">NPS Scale</option>
                </select>
              </div>
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Methodology Tags
            </label>
            <input
              type="text"
              value={formData.methodology_tags?.join(', ') || ''}
              onChange={(e) => handleMethodologyTagsChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              placeholder="Enter methodology tags separated by commas"
            />
          </div>

          {/* Industry Keywords */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry Keywords
            </label>
            <input
              type="text"
              value={formData.industry_keywords?.join(', ') || ''}
              onChange={(e) => handleIndustryKeywordsChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              placeholder="Enter industry keywords separated by commas"
            />
          </div>

          {/* Question Patterns (for questions) */}
          {type === 'question' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question Patterns
              </label>
              <input
                type="text"
                value={formData.question_patterns?.join(', ') || ''}
                onChange={(e) => handleQuestionPatternsChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                placeholder="Enter question patterns separated by commas"
              />
            </div>
          )}

          {/* Quality Score */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quality Score (0.0 - 1.0)
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
