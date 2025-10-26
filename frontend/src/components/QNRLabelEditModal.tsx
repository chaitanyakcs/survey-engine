import React, { useState, useEffect } from 'react';
import { XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';

interface QNRLabelEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (label: QNRLabelInput) => Promise<void>;
  label?: Partial<QNRLabelInput>;
  mode: 'create' | 'edit';
}

interface QNRLabelInput {
  name: string;
  description: string;
  category: 'screener' | 'brand' | 'concept' | 'methodology' | 'additional';
  mandatory: boolean;
  label_type: 'Text' | 'QNR' | 'Rules';
  applicable_labels: string[];
  detection_patterns: string[];
  section_id: number;
  display_order: number;
  active: boolean;
}

export const QNRLabelEditModal: React.FC<QNRLabelEditModalProps> = ({
  isOpen,
  onClose,
  onSave,
  label,
  mode
}) => {
  const [formData, setFormData] = useState<QNRLabelInput>({
    name: '',
    description: '',
    category: 'screener',
    mandatory: false,
    label_type: 'QNR',
    applicable_labels: [],
    detection_patterns: [],
    section_id: 2,
    display_order: 0,
    active: true
  });

  const [applicableInput, setApplicableInput] = useState('');
  const [patternInput, setPatternInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen && label && mode === 'edit') {
      setFormData({
        name: label.name || '',
        description: label.description || '',
        category: label.category || 'screener',
        mandatory: label.mandatory || false,
        label_type: label.label_type || 'QNR',
        applicable_labels: label.applicable_labels || [],
        detection_patterns: label.detection_patterns || [],
        section_id: label.section_id || 2,
        display_order: label.display_order || 0,
        active: label.active !== undefined ? label.active : true
      });
      setApplicableInput('');
      setPatternInput('');
    } else if (isOpen && mode === 'create') {
      setFormData({
        name: '',
        description: '',
        category: 'screener',
        mandatory: false,
        label_type: 'QNR',
        applicable_labels: [],
        detection_patterns: [],
        section_id: 2,
        display_order: 0,
        active: true
      });
    }
    setErrors({});
  }, [isOpen, label, mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validate
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }
    if (!formData.category) {
      newErrors.category = 'Category is required';
    }
    if (formData.section_id < 1 || formData.section_id > 7) {
      newErrors.section_id = 'Section ID must be between 1 and 7';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      setErrors({ submit: err instanceof Error ? err.message : 'Failed to save label' });
    } finally {
      setSaving(false);
    }
  };

  const addApplicableLabel = () => {
    if (applicableInput.trim() && !formData.applicable_labels.includes(applicableInput.trim())) {
      setFormData({
        ...formData,
        applicable_labels: [...formData.applicable_labels, applicableInput.trim()]
      });
      setApplicableInput('');
    }
  };

  const removeApplicableLabel = (label: string) => {
    setFormData({
      ...formData,
      applicable_labels: formData.applicable_labels.filter(l => l !== label)
    });
  };

  const addPattern = () => {
    if (patternInput.trim() && !formData.detection_patterns.includes(patternInput.trim())) {
      setFormData({
        ...formData,
        detection_patterns: [...formData.detection_patterns, patternInput.trim()]
      });
      setPatternInput('');
    }
  };

  const removePattern = (pattern: string) => {
    setFormData({
      ...formData,
      detection_patterns: formData.detection_patterns.filter(p => p !== pattern)
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900">
            {mode === 'create' ? 'Add QNR Label' : 'Edit QNR Label'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Label Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="e.g., Study_Intro"
              disabled={mode === 'edit'}
            />
            {errors.name && <p className="text-red-600 text-sm mt-1">{errors.name}</p>}
            {mode === 'edit' && (
              <p className="text-xs text-gray-500 mt-1">Name cannot be changed after creation</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 ${
                errors.description ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Description of what this label represents"
            />
            {errors.description && <p className="text-red-600 text-sm mt-1">{errors.description}</p>}
          </div>

          {/* Category and Section */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 ${
                  errors.category ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="screener">Screener</option>
                <option value="brand">Brand</option>
                <option value="concept">Concept</option>
                <option value="methodology">Methodology</option>
                <option value="additional">Additional</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Section <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.section_id}
                onChange={(e) => setFormData({ ...formData, section_id: Number(e.target.value) })}
                className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 ${
                  errors.section_id ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value={1}>1 - Sample Plan</option>
                <option value={2}>2 - Screener</option>
                <option value={3}>3 - Brand/Product Awareness</option>
                <option value={4}>4 - Concept Exposure</option>
                <option value={5}>5 - Methodology</option>
                <option value={6}>6 - Additional Questions</option>
                <option value={7}>7 - Programmer Instructions</option>
              </select>
              {errors.section_id && <p className="text-red-600 text-sm mt-1">{errors.section_id}</p>}
            </div>
          </div>

          {/* Type and Mandatory */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Label Type</label>
              <select
                value={formData.label_type}
                onChange={(e) => setFormData({ ...formData, label_type: e.target.value as any })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
              >
                <option value="Text">Text</option>
                <option value="QNR">QNR</option>
                <option value="Rules">Rules</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <div className="space-y-3">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.mandatory}
                    onChange={(e) => setFormData({ ...formData, mandatory: e.target.checked })}
                    className="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
                  />
                  <span className="text-sm text-gray-700">Mandatory</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.active}
                    onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                    className="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
                  />
                  <span className="text-sm text-gray-700">Active</span>
                </label>
              </div>
            </div>
          </div>

          {/* Applicable Labels */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Applicable To (Industries/Methodologies)
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={applicableInput}
                onChange={(e) => setApplicableInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addApplicableLabel())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                placeholder="e.g., Healthcare, Consumer Health"
              />
              <button
                type="button"
                onClick={addApplicableLabel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Add
              </button>
            </div>
            {formData.applicable_labels.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.applicable_labels.map((label) => (
                  <span
                    key={label}
                    className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                  >
                    {label}
                    <button
                      type="button"
                      onClick={() => removeApplicableLabel(label)}
                      className="ml-2 hover:text-blue-600"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to apply to all contexts
            </p>
          </div>

          {/* Detection Patterns */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Detection Patterns (Keywords for Auto-Detection)
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={patternInput}
                onChange={(e) => setPatternInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addPattern())}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                placeholder="e.g., ai model, machine learning"
              />
              <button
                type="button"
                onClick={addPattern}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Add
              </button>
            </div>
            {formData.detection_patterns.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.detection_patterns.map((pattern) => (
                  <span
                    key={pattern}
                    className="inline-flex items-center px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                  >
                    {pattern}
                    <button
                      type="button"
                      onClick={() => removePattern(pattern)}
                      className="ml-2 hover:text-green-600"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Display Order */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Display Order</label>
            <input
              type="number"
              value={formData.display_order}
              onChange={(e) => setFormData({ ...formData, display_order: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
              min="0"
            />
            <p className="text-xs text-gray-500 mt-1">
              Lower numbers appear first in lists
            </p>
          </div>

          {/* Error Messages */}
          {errors.submit && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{errors.submit}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              disabled={saving}
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
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
        </form>
      </div>
    </div>
  );
};

