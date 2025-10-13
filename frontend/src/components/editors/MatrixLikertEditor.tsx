import React, { useState, useEffect } from 'react';
import { Question } from '../../types';
import { 
  reconstructQuestionText,
  validateAttributes 
} from '../../utils/textParsers';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface MatrixLikertEditorProps {
  question: Question;
  parsedData: {
    attributes: string[];
    options: string[];
  };
  onUpdate: (question: Question) => void;
  errors: string[];
}

export const MatrixLikertEditor: React.FC<MatrixLikertEditorProps> = ({
  question,
  parsedData,
  onUpdate,
  errors
}) => {
  const [attributes, setAttributes] = useState<string[]>(parsedData.attributes);
  const [options, setOptions] = useState<string[]>(parsedData.options);

  // Update question when attributes or options change
  useEffect(() => {
    const newText = reconstructQuestionText(question.text || '', attributes);
    onUpdate({
      ...question,
      text: newText,
      options: options
    });
  }, [attributes, options, question, onUpdate]);

  const addAttribute = () => {
    setAttributes(prev => [...prev, '']);
  };

  const updateAttribute = (index: number, value: string) => {
    setAttributes(prev => prev.map((attr, i) => i === index ? value : attr));
  };

  const removeAttribute = (index: number) => {
    setAttributes(prev => prev.filter((_, i) => i !== index));
  };

  const addOption = () => {
    setOptions(prev => [...prev, '']);
  };

  const updateOption = (index: number, value: string) => {
    setOptions(prev => prev.map((opt, i) => i === index ? value : opt));
  };

  const removeOption = (index: number) => {
    setOptions(prev => prev.filter((_, i) => i !== index));
  };

  const moveAttribute = (index: number, direction: 'up' | 'down') => {
    const newAttributes = [...attributes];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newAttributes.length) {
      [newAttributes[index], newAttributes[newIndex]] = [newAttributes[newIndex], newAttributes[index]];
      setAttributes(newAttributes);
    }
  };

  const moveOption = (index: number, direction: 'up' | 'down') => {
    const newOptions = [...options];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newOptions.length) {
      [newOptions[index], newOptions[newIndex]] = [newOptions[newIndex], newOptions[index]];
      setOptions(newOptions);
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

      {/* Attributes Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Attributes to Rate *
          </label>
          <button
            onClick={addAttribute}
            className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
            type="button"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Attribute
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
                placeholder={`Attribute ${index + 1}`}
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

      {/* Scale Options Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Scale Options *
          </label>
          <button
            onClick={addOption}
            className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
            type="button"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Option
          </button>
        </div>
        
        <div className="space-y-2">
          {options.map((option, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="w-8 text-sm text-gray-600">{index + 1}.</span>
              <input
                type="text"
                value={option}
                onChange={(e) => updateOption(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={`Scale option ${index + 1}`}
              />
              <button
                onClick={() => moveOption(index, 'up')}
                disabled={index === 0}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↑
              </button>
              <button
                onClick={() => moveOption(index, 'down')}
                disabled={index === options.length - 1}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↓
              </button>
              <button
                onClick={() => removeOption(index)}
                className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                type="button"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        
        {options.length < 2 && (
          <p className="mt-2 text-sm text-red-600">At least 2 scale options are required</p>
        )}
      </div>

      {/* Matrix Preview */}
      {attributes.length > 0 && options.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-3">Matrix Preview:</h4>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-blue-300">
                  <th className="text-left py-2 px-3 font-medium text-blue-700 bg-blue-100">
                    Attributes
                  </th>
                  {options.map((option, index) => (
                    <th key={index} className="text-center py-2 px-2 font-medium text-blue-700 bg-blue-100 min-w-[100px]">
                      {index + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {attributes.map((attribute, attrIndex) => (
                  <tr key={attrIndex} className="border-b border-blue-200">
                    <td className="py-2 px-3 text-blue-700 font-medium">
                      {attribute || `Attribute ${attrIndex + 1}`}
                    </td>
                    {options.map((option, optionIndex) => (
                      <td key={optionIndex} className="text-center py-2 px-2">
                        <div className="w-4 h-4 border border-blue-300 rounded mx-auto"></div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default MatrixLikertEditor;
