import React, { useState, useEffect } from 'react';
import { Question } from '../../types';
import { 
  reconstructQuestionText,
  validateAttributes 
} from '../../utils/textParsers';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface ConstantSumEditorProps {
  question: Question;
  parsedData: {
    attributes: string[];
    totalPoints: number;
  };
  onUpdate: (question: Question) => void;
  errors: string[];
}

export const ConstantSumEditor: React.FC<ConstantSumEditorProps> = ({
  question,
  parsedData,
  onUpdate,
  errors
}) => {
  const [attributes, setAttributes] = useState<string[]>(parsedData.attributes);
  const [totalPoints, setTotalPoints] = useState<number>(parsedData.totalPoints);

  // Update question when attributes or totalPoints change
  useEffect(() => {
    const newText = reconstructQuestionText(question.text || '', attributes, undefined, totalPoints);
    onUpdate({
      ...question,
      text: newText
    });
  }, [attributes, totalPoints, question, onUpdate]);

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

      {/* Total Points */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Total Points to Allocate *
        </label>
        <input
          type="number"
          min="10"
          max="1000"
          value={totalPoints}
          onChange={(e) => setTotalPoints(Math.max(10, parseInt(e.target.value) || 10))}
          className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="mt-1 text-xs text-gray-500">
          Respondents will allocate these points across the attributes below
        </p>
        {(totalPoints < 10 || totalPoints > 1000) && (
          <p className="mt-1 text-sm text-red-600">Total points must be between 10 and 1000</p>
        )}
      </div>

      {/* Attributes Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Attributes to Allocate Points *
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

      {/* Allocation Preview */}
      {attributes.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-green-800 mb-3">Allocation Preview:</h4>
          <div className="space-y-3">
            {attributes.map((attribute, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-white rounded border border-green-200">
                <div className="flex-1">
                  <label className="text-sm font-medium text-green-700">
                    {attribute || `Attribute ${index + 1}`}
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    min="0"
                    max={totalPoints}
                    disabled
                    className="w-20 px-2 py-1 text-sm border border-gray-300 rounded text-center bg-gray-100"
                    placeholder="0"
                  />
                  <span className="text-xs text-green-600">points</span>
                </div>
              </div>
            ))}
            <div className="mt-4 p-3 bg-white rounded border border-green-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-700">Total Allocated:</span>
                <span className="text-sm font-bold text-green-600">0 / {totalPoints}</span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-sm text-green-600">Remaining:</span>
                <span className="text-sm font-medium text-green-600">{totalPoints} points</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConstantSumEditor;
