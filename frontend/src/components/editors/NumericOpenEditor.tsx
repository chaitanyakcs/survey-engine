import React, { useState, useEffect } from 'react';
import { Question } from '../../types';
import { 
  reconstructQuestionText,
  validateAttributes 
} from '../../utils/textParsers';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface NumericOpenEditorProps {
  question: Question;
  parsedData: {
    attributes: string[];
  };
  onUpdate: (question: Question) => void;
  errors: string[];
}

export const NumericOpenEditor: React.FC<NumericOpenEditorProps> = ({
  question,
  parsedData,
  onUpdate,
  errors
}) => {
  const [attributes, setAttributes] = useState<string[]>(parsedData.attributes);
  const [minValue, setMinValue] = useState<number>(0);
  const [maxValue, setMaxValue] = useState<number>(100);
  const [allowDecimals, setAllowDecimals] = useState<boolean>(false);

  // Update question when attributes change
  useEffect(() => {
    const newText = reconstructQuestionText(question.text || '', attributes);
    onUpdate({
      ...question,
      text: newText
    });
  }, [attributes, question, onUpdate]);

  const addAttribute = () => {
    setAttributes(prev => [...prev, '']);
  };

  const updateAttribute = (index: number, value: string) => {
    setAttributes(prev => prev.map((attr, i) => i === index ? value : attr));
  };

  const removeAttribute = (index: number) => {
    setAttributes(prev => prev.filter((_, i) => i !== index));
  };

  const moveAttribute = (index: number, direction: 'up' | 'down') => {
    const newAttributes = [...attributes];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newAttributes.length) {
      [newAttributes[index], newAttributes[newIndex]] = [newAttributes[newIndex], newAttributes[index]];
      setAttributes(newAttributes);
    }
  };

  const validationErrors = validateAttributes(attributes);

  return (
    <div className="space-y-6">
      {/* Question Text Preview */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Question Preview:</h4>
        <p className="text-sm text-gray-600 italic">
          {question.text || 'Question text will appear here...'}
        </p>
      </div>

      {/* Items Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Items to Rate *
          </label>
          <button
            onClick={addAttribute}
            className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
            type="button"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Item
          </button>
        </div>
        
        <div className="space-y-2">
          {attributes.map((attribute, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={attribute}
                onChange={(e) => updateAttribute(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={`Item ${index + 1}`}
              />
              <button
                onClick={() => moveAttribute(index, 'up')}
                disabled={index === 0}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↑
              </button>
              <button
                onClick={() => moveAttribute(index, 'down')}
                disabled={index === attributes.length - 1}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↓
              </button>
              <button
                onClick={() => removeAttribute(index)}
                className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                type="button"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        
        {validationErrors.length > 0 && (
          <div className="mt-2 text-sm text-red-600">
            {validationErrors.map((error, index) => (
              <div key={index}>{error}</div>
            ))}
          </div>
        )}
      </div>

      {/* Numeric Constraints */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-3">Numeric Constraints:</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-blue-700 mb-1">
              Minimum Value
            </label>
            <input
              type="number"
              value={minValue}
              onChange={(e) => setMinValue(parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-blue-700 mb-1">
              Maximum Value
            </label>
            <input
              type="number"
              value={maxValue}
              onChange={(e) => setMaxValue(parseFloat(e.target.value) || 100)}
              className="w-full px-3 py-2 border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="allowDecimals"
              checked={allowDecimals}
              onChange={(e) => setAllowDecimals(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-blue-300 rounded"
            />
            <label htmlFor="allowDecimals" className="ml-2 block text-sm text-blue-700">
              Allow decimals
            </label>
          </div>
        </div>
        
        {(minValue >= maxValue) && (
          <p className="mt-2 text-sm text-red-600">Maximum value must be greater than minimum value</p>
        )}
      </div>

      {/* Input Preview */}
      {attributes.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-green-800 mb-3">Input Preview:</h4>
          <div className="space-y-3">
            {attributes.map((attribute, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-white rounded border border-green-200">
                <div className="flex-1">
                  <label className="text-sm font-medium text-green-700">
                    {attribute || `Item ${index + 1}`}
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    min={minValue}
                    max={maxValue}
                    step={allowDecimals ? 0.01 : 1}
                    disabled
                    className="w-24 px-2 py-1 text-sm border border-gray-300 rounded text-center bg-gray-100"
                    placeholder="0"
                  />
                  <span className="text-xs text-green-600">
                    {allowDecimals ? 'decimal' : 'integer'}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 p-3 bg-white rounded border border-green-200">
            <div className="text-sm text-green-700">
              <strong>Range:</strong> {minValue} to {maxValue} 
              {allowDecimals ? ' (decimals allowed)' : ' (integers only)'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NumericOpenEditor;
