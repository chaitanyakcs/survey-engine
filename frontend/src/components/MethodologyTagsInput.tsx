import React, { useState, useRef, useEffect } from 'react';
import { PlusIcon, XMarkIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface MethodologyTag {
  name: string;
  description: string;
  category: 'pricing' | 'choice' | 'brand' | 'satisfaction' | 'concept' | 'usage' | 'other';
}

interface MethodologyTagsInputProps {
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  placeholder?: string;
  maxTags?: number;
  showDropdownMenu?: boolean;
  extractedTags?: string[];
  disabled?: boolean;
}

// Standard methodology tags with categories
const STANDARD_METHODOLOGY_TAGS: MethodologyTag[] = [
  // Pricing Research
  { name: 'Van Westendorp', description: 'Price sensitivity measurement', category: 'pricing' },
  { name: 'Gabor-Granger', description: 'Direct price testing', category: 'pricing' },
  { name: 'Brand-Price Trade-off', description: 'Price vs brand preference', category: 'pricing' },
  { name: 'Price Sensitivity', description: 'General price sensitivity analysis', category: 'pricing' },
  
  // Choice Research
  { name: 'Conjoint', description: 'Conjoint analysis for preferences', category: 'choice' },
  { name: 'MaxDiff', description: 'Maximum difference scaling', category: 'choice' },
  { name: 'Choice Modeling', description: 'Discrete choice experiments', category: 'choice' },
  { name: 'DCE', description: 'Discrete choice experiments', category: 'choice' },
  { name: 'TURF', description: 'Total unduplicated reach and frequency', category: 'choice' },
  
  // Brand Research
  { name: 'Brand Tracking', description: 'Brand awareness and perception tracking', category: 'brand' },
  { name: 'Brand Mapping', description: 'Brand positioning analysis', category: 'brand' },
  { name: 'Brand Associations', description: 'Brand attribute associations', category: 'brand' },
  { name: 'Perceptual Mapping', description: 'Brand positioning visualization', category: 'brand' },
  { name: 'Message Testing', description: 'Advertising message effectiveness', category: 'brand' },
  
  // Satisfaction Research
  { name: 'CSAT', description: 'Customer satisfaction measurement', category: 'satisfaction' },
  { name: 'NPS', description: 'Net Promoter Score', category: 'satisfaction' },
  { name: 'CES', description: 'Customer effort score', category: 'satisfaction' },
  { name: 'Driver Analysis', description: 'Satisfaction driver identification', category: 'satisfaction' },
  
  // Concept Testing
  { name: 'Concept Testing', description: 'New product concept evaluation', category: 'concept' },
  { name: 'Monadic Testing', description: 'Single concept evaluation', category: 'concept' },
  { name: 'Sequential Monadic', description: 'Multiple concept evaluation', category: 'concept' },
  { name: 'Kano Model', description: 'Feature satisfaction analysis', category: 'concept' },
  
  // Usage & Attitudes
  { name: 'Usage & Attitudes', description: 'Product usage and attitude study', category: 'usage' },
  { name: 'Purchase Intent', description: 'Likelihood to purchase measurement', category: 'usage' },
  { name: 'Market Sizing', description: 'Market size estimation', category: 'usage' },
  { name: 'Segmentation', description: 'Market segmentation analysis', category: 'usage' },
  
  // Other
  { name: 'Quantitative', description: 'Quantitative research methods', category: 'other' },
  { name: 'Qualitative', description: 'Qualitative research methods', category: 'other' },
  { name: 'Mixed Methods', description: 'Combined quantitative and qualitative', category: 'other' },
  { name: 'Demographic', description: 'Demographic profiling', category: 'other' },
  { name: 'Behavioral', description: 'Behavioral analysis', category: 'other' },
  { name: 'Attitudinal', description: 'Attitude measurement', category: 'other' }
];

const CATEGORY_LABELS = {
  pricing: 'Pricing Research',
  choice: 'Choice Research',
  brand: 'Brand Research',
  satisfaction: 'Satisfaction Research',
  concept: 'Concept Testing',
  usage: 'Usage & Attitudes',
  other: 'Other'
};

const MethodologyTagsInput: React.FC<MethodologyTagsInputProps> = ({
  tags = [],
  onTagsChange,
  placeholder = "Add methodology tags...",
  maxTags = 20,
  showDropdownMenu = true,
  extractedTags = [],
  disabled = false
}) => {
  const [inputValue, setInputValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<MethodologyTag['category'] | 'all'>('all');
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter tags based on search and category
  const filteredTags = STANDARD_METHODOLOGY_TAGS.filter(tag => {
    const matchesSearch = searchQuery === '' || 
      tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tag.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tag.category === selectedCategory;
    const notAlreadySelected = !tags.includes(tag.name);
    return matchesSearch && matchesCategory && notAlreadySelected;
  });

  // Group filtered tags by category
  const groupedTags = filteredTags.reduce((acc, tag) => {
    if (!acc[tag.category]) {
      acc[tag.category] = [];
    }
    acc[tag.category].push(tag);
    return acc;
  }, {} as Record<string, MethodologyTag[]>);

  const handleAddTag = (tagName?: string) => {
    const tagToAdd = tagName || inputValue.trim();
    if (tagToAdd && !tags.includes(tagToAdd) && tags.length < maxTags) {
      onTagsChange([...tags, tagToAdd]);
      setInputValue('');
      setShowDropdown(false);
      setSearchQuery('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onTagsChange(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value.replace(/,/g, ''));
    setSearchQuery(value.replace(/,/g, ''));
    if (value && showDropdown) {
      setShowDropdown(true);
    }
  };

  const handleInputFocus = () => {
    if (showDropdownMenu) {
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
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
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
            onFocus={handleInputFocus}
            placeholder={placeholder}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-50"
            disabled={disabled || tags.length >= maxTags}
          />
          {tags.length >= maxTags && (
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-gray-500">
              Max {maxTags} tags
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            handleAddTag();
          }}
          disabled={disabled || !inputValue.trim() || tags.includes(inputValue.trim()) || tags.length >= maxTags}
          className="flex items-center justify-center w-8 h-8 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
        {showDropdownMenu && (
          <button
            type="button"
            onClick={() => setShowDropdown(!showDropdown)}
            disabled={disabled}
            className="flex items-center justify-center w-8 h-8 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronDownIcon className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div ref={dropdownRef} className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {/* Search and Category Filter */}
          <div className="p-3 border-b border-gray-200">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search methodology tags..."
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
            <div className="mt-2">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as MethodologyTag['category'] | 'all')}
                className="w-full px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              >
                <option value="all">All Categories</option>
                {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Tags List */}
          <div className="p-3">
            {Object.keys(groupedTags).length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-4">
                No methodology tags found
              </div>
            ) : (
              Object.entries(groupedTags).map(([category, categoryTags]) => (
                <div key={category} className="mb-4">
                  <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                    {CATEGORY_LABELS[category as MethodologyTag['category']]}
                  </h4>
                  <div className="space-y-1">
                    {categoryTags.map((tag) => (
                      <button
                        key={tag.name}
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          handleAddTag(tag.name);
                        }}
                        disabled={disabled}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-yellow-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="font-medium text-gray-900">{tag.name}</div>
                        <div className="text-xs text-gray-500">{tag.description}</div>
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Extracted Tags Section */}
      {extractedTags.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-green-600 font-medium">
            Tags extracted from uploaded document (click to add):
          </p>
          <div className="flex flex-wrap gap-2">
            {extractedTags
              .filter(tag => !tags.includes(tag))
              .map((tag) => (
                <button
                  key={`extracted-${tag}`}
                  type="button"
                  onClick={() => handleAddTag(tag)}
                  disabled={disabled}
                  className="px-3 py-1 text-sm rounded-full bg-green-100 text-green-700 hover:bg-green-200 border border-green-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {tag} +
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Selected Tags Display */}
      {tags.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-600 font-medium">
            Selected methodology tags ({tags.length}/{maxTags}):
          </p>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full border border-yellow-200"
              >
                <span>{tag}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  disabled={disabled}
                  className="ml-1 hover:bg-yellow-200 rounded-full p-0.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Helper Text */}
      <div className="text-xs text-gray-500">
        Press Enter or comma to add tags. Click × to remove. 
        {showDropdownMenu && " Use the dropdown to select from predefined methodology tags."}
        {extractedTags.length > 0 && " Upload a document to automatically extract methodology tags."}
      </div>
    </div>
  );
};

export default MethodologyTagsInput;
