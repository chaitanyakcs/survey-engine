import React, { useState, KeyboardEvent } from 'react';
import { XMarkIcon, PlusIcon } from '@heroicons/react/24/outline';

interface LabelsInputProps {
  labels: string[];
  onLabelsChange: (labels: string[]) => void;
  placeholder?: string;
  maxLabels?: number;
}

const LabelsInput: React.FC<LabelsInputProps> = ({
  labels = [],
  onLabelsChange,
  placeholder = "Add a label...",
  maxLabels = 10
}) => {
  const [inputValue, setInputValue] = useState('');

  const handleAddLabel = () => {
    const trimmedValue = inputValue.trim();
    if (trimmedValue && !labels.includes(trimmedValue) && labels.length < maxLabels) {
      onLabelsChange([...labels, trimmedValue]);
      setInputValue('');
    }
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    onLabelsChange(labels.filter(label => label !== labelToRemove));
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddLabel();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Remove commas as they're used as separators
    setInputValue(value.replace(/,/g, ''));
  };

  return (
    <div className="space-y-3">
      {/* Input Field */}
      <div className="flex items-center space-x-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={labels.length >= maxLabels}
          />
          {labels.length >= maxLabels && (
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-gray-500">
              Max {maxLabels} labels
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={handleAddLabel}
          disabled={!inputValue.trim() || labels.includes(inputValue.trim()) || labels.length >= maxLabels}
          className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Labels Display */}
      {labels.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {labels.map((label, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full border border-blue-200"
            >
              <span>{label}</span>
              <button
                type="button"
                onClick={() => handleRemoveLabel(label)}
                className="ml-1 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Helper Text */}
      <div className="text-xs text-gray-500">
        Press Enter or comma to add labels. Click × to remove.
        {labels.length > 0 && (
          <span className="ml-2">
            ({labels.length}/{maxLabels} labels)
          </span>
        )}
      </div>
    </div>
  );
};

export default LabelsInput;
