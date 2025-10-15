import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { XMarkIcon, PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { QNR_LABELS, LABEL_CATEGORIES, QNRLabel } from '../data/qnrLabels';

interface EnhancedLabelsInputProps {
  labels: string[];
  onLabelsChange: (labels: string[]) => void;
  placeholder?: string;
  maxLabels?: number;
  showMasterList?: boolean;
}

const EnhancedLabelsInput: React.FC<EnhancedLabelsInputProps> = ({
  labels = [],
  onLabelsChange,
  placeholder = "Add a label...",
  maxLabels = 10,
  showMasterList = true
}) => {
  const [inputValue, setInputValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<QNRLabel['category'] | 'all'>('all');
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter labels based on search and category
  const filteredLabels = QNR_LABELS.filter(label => {
    const matchesSearch = searchQuery === '' || 
      label.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      label.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || label.category === selectedCategory;
    const notAlreadySelected = !labels.includes(label.name);
    return matchesSearch && matchesCategory && notAlreadySelected;
  });

  // Group filtered labels by category
  const groupedLabels = filteredLabels.reduce((acc, label) => {
    if (!acc[label.category]) {
      acc[label.category] = [];
    }
    acc[label.category].push(label);
    return acc;
  }, {} as Record<string, QNRLabel[]>);

  const handleAddLabel = (labelName?: string) => {
    const labelToAdd = labelName || inputValue.trim();
    if (labelToAdd && !labels.includes(labelToAdd) && labels.length < maxLabels) {
      onLabelsChange([...labels, labelToAdd]);
      setInputValue('');
      setShowDropdown(false);
      setSearchQuery('');
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
    if (e.key === 'Escape') {
      setShowDropdown(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value.replace(/,/g, ''));
    setSearchQuery(value.replace(/,/g, ''));
    setShowDropdown(true);
  };

  const handleFocus = () => {
    if (showMasterList) {
      setShowDropdown(true);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="space-y-3">
      {/* Input Field */}
      <div className="flex items-center space-x-2">
        <div className="flex-1 relative">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            onFocus={handleFocus}
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
          onClick={() => handleAddLabel()}
          disabled={!inputValue.trim() || labels.includes(inputValue.trim()) || labels.length >= maxLabels}
          className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Master List Dropdown */}
      {showMasterList && showDropdown && (
        <div 
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto"
        >
          {/* Search and Filter Header */}
          <div className="p-3 border-b border-gray-200">
            <div className="flex items-center space-x-2 mb-2">
              <MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search labels..."
                className="flex-1 text-sm border-none outline-none"
              />
            </div>
            
            {/* Category Filter */}
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-2 py-1 text-xs rounded ${
                  selectedCategory === 'all' 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              {Object.entries(LABEL_CATEGORIES).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key as QNRLabel['category'])}
                  className={`px-2 py-1 text-xs rounded ${
                    selectedCategory === key 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Labels List */}
          <div className="p-2">
            {Object.keys(groupedLabels).length === 0 ? (
              <div className="text-sm text-gray-500 py-2 text-center">
                No labels found
              </div>
            ) : (
              Object.entries(groupedLabels).map(([category, categoryLabels]) => (
                <div key={category} className="mb-4">
                  <div className="text-xs font-semibold text-gray-600 mb-2 px-2">
                    {LABEL_CATEGORIES[category as keyof typeof LABEL_CATEGORIES]}
                  </div>
                  <div className="space-y-1">
                    {categoryLabels.map((label) => (
                      <button
                        key={label.name}
                        onClick={() => handleAddLabel(label.name)}
                        className="w-full text-left p-2 hover:bg-gray-50 rounded text-sm"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900">{label.name}</div>
                            <div className="text-xs text-gray-600 mt-1">{label.description}</div>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className={`px-1.5 py-0.5 text-xs rounded ${
                                label.mandatory 
                                  ? 'bg-red-100 text-red-700' 
                                  : 'bg-gray-100 text-gray-600'
                              }`}>
                                {label.mandatory ? 'Required' : 'Optional'}
                              </span>
                              <span className="px-1.5 py-0.5 text-xs rounded bg-blue-100 text-blue-700">
                                {label.type}
                              </span>
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

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
        Press Enter or comma to add labels. Click x to remove. 
        {showMasterList && " Use the dropdown to select from predefined QNR labels."}
      </div>
    </div>
  );
};

export default EnhancedLabelsInput;
