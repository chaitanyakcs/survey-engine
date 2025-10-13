import React, { useState, useEffect } from 'react';
import { Question } from '../../types';
import { 
  reconstructQuestionText,
  validateAttributes 
} from '../../utils/textParsers';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface NumericGridEditorProps {
  question: Question;
  parsedData: {
    attributes: string[];
    options: string[];
  };
  onUpdate: (question: Question) => void;
  errors: string[];
}

export const NumericGridEditor: React.FC<NumericGridEditorProps> = ({
  question,
  parsedData,
  onUpdate,
  errors
}) => {
  const [attributes, setAttributes] = useState<string[]>(parsedData.attributes);
  const [columns, setColumns] = useState<string[]>(parsedData.options);

  // Update question when attributes or columns change
  useEffect(() => {
    const newText = reconstructQuestionText(question.text || '', attributes);
    onUpdate({
      ...question,
      text: newText,
      options: columns
    });
  }, [attributes, columns, question, onUpdate]);

  const addAttribute = () => {
    setAttributes(prev => [...prev, '']);
  };

  const updateAttribute = (index: number, value: string) => {
    setAttributes(prev => prev.map((attr, i) => i === index ? value : attr));
  };

  const removeAttribute = (index: number) => {
    setAttributes(prev => prev.filter((_, i) => i !== index));
  };

  const addColumn = () => {
    setColumns(prev => [...prev, '']);
  };

  const updateColumn = (index: number, value: string) => {
    setColumns(prev => prev.map((col, i) => i === index ? value : col));
  };

  const removeColumn = (index: number) => {
    setColumns(prev => prev.filter((_, i) => i !== index));
  };

  const moveAttribute = (index: number, direction: 'up' | 'down') => {
    const newAttributes = [...attributes];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newAttributes.length) {
      [newAttributes[index], newAttributes[newIndex]] = [newAttributes[newIndex], newAttributes[index]];
      setAttributes(newAttributes);
    }
  };

  const moveColumn = (index: number, direction: 'up' | 'down') => {
    const newColumns = [...columns];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newColumns.length) {
      [newColumns[index], newColumns[newIndex]] = [newColumns[newIndex], newColumns[index]];
      setColumns(newColumns);
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

      {/* Items/Rows Section */}
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

      {/* Columns Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Columns/Categories *
          </label>
          <button
            onClick={addColumn}
            className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
            type="button"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Column
          </button>
        </div>
        
        <div className="space-y-2">
          {columns.map((column, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="w-8 text-sm text-gray-600">{index + 1}.</span>
              <input
                type="text"
                value={column}
                onChange={(e) => updateColumn(index, e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={`Column ${index + 1}`}
              />
              <button
                onClick={() => moveColumn(index, 'up')}
                disabled={index === 0}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↑
              </button>
              <button
                onClick={() => moveColumn(index, 'down')}
                disabled={index === columns.length - 1}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↓
              </button>
              <button
                onClick={() => removeColumn(index)}
                className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                type="button"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        
        {columns.length < 2 && (
          <p className="mt-2 text-sm text-red-600">At least 2 columns are required</p>
        )}
      </div>

      {/* Grid Preview */}
      {attributes.length > 0 && columns.length > 0 && (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-purple-800 mb-3">Numeric Grid Preview:</h4>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-purple-300">
                  <th className="text-left py-2 px-3 font-medium text-purple-700 bg-purple-100">
                    Items
                  </th>
                  {columns.map((column, index) => (
                    <th key={index} className="text-center py-2 px-2 font-medium text-purple-700 bg-purple-100 min-w-[100px]">
                      {column || `Column ${index + 1}`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {attributes.map((attribute, attrIndex) => (
                  <tr key={attrIndex} className="border-b border-purple-200">
                    <td className="py-2 px-3 text-purple-700 font-medium">
                      {attribute || `Item ${attrIndex + 1}`}
                    </td>
                    {columns.map((column, columnIndex) => (
                      <td key={columnIndex} className="text-center py-2 px-2">
                        <input
                          type="number"
                          disabled
                          placeholder="0"
                          className="w-16 px-2 py-1 text-sm border border-gray-300 rounded text-center bg-gray-100"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-purple-600">
            Respondents will enter numeric values for each item-column combination
          </p>
        </div>
      )}
    </div>
  );
};

export default NumericGridEditor;
