import React, { useState, useEffect } from 'react';
import { Question } from '../../types';
import { 
  validatePricePoints 
} from '../../utils/textParsers';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface GaborGrangerEditorProps {
  question: Question;
  parsedData: {
    pricePoints: number[];
    productName: string;
  };
  onUpdate: (question: Question) => void;
  errors: string[];
}

export const GaborGrangerEditor: React.FC<GaborGrangerEditorProps> = ({
  question,
  parsedData,
  onUpdate,
  errors
}) => {
  const [pricePoints, setPricePoints] = useState<number[]>(parsedData.pricePoints);
  const [productName, setProductName] = useState<string>(parsedData.productName);

  // Update question when pricePoints or productName change
  useEffect(() => {
    const priceText = pricePoints.map(price => `$${price}`).join(', ');
    const newText = `How much would you pay for ${productName || 'this product'}? Please select from: ${priceText}`;
    
    onUpdate({
      ...question,
      text: newText,
      options: pricePoints.map(price => `$${price}`)
    });
  }, [pricePoints, productName, question, onUpdate]);

  const addPricePoint = () => {
    const lastPrice = pricePoints.length > 0 ? pricePoints[pricePoints.length - 1] : 0;
    setPricePoints(prev => [...prev, lastPrice + 10]);
  };

  const updatePricePoint = (index: number, value: string) => {
    const numValue = Math.max(0, parseFloat(value) || 0);
    setPricePoints(prev => prev.map((price, i) => i === index ? numValue : price));
  };

  const removePricePoint = (index: number) => {
    setPricePoints(prev => prev.filter((_, i) => i !== index));
  };

  const movePricePoint = (index: number, direction: 'up' | 'down') => {
    const newPricePoints = [...pricePoints];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex >= 0 && newIndex < newPricePoints.length) {
      [newPricePoints[index], newPricePoints[newIndex]] = [newPricePoints[newIndex], newPricePoints[index]];
      setPricePoints(newPricePoints);
    }
  };

  const sortPricePoints = () => {
    setPricePoints(prev => [...prev].sort((a, b) => a - b));
  };

  const validationErrors = validatePricePoints(pricePoints);

  return (
    <div className="space-y-6">
      {/* Question Text Preview */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Question Preview:</h4>
        <p className="text-sm text-gray-600 italic">
          {question.text || 'Question text will appear here...'}
        </p>
      </div>

      {/* Product Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Product Name *
        </label>
        <input
          type="text"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="e.g., this smartphone, the new laptop"
        />
        <p className="mt-1 text-xs text-gray-500">
          The product that respondents will price
        </p>
        {!productName.trim() && (
          <p className="mt-1 text-sm text-red-600">Product name is required</p>
        )}
      </div>

      {/* Price Points Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Price Points *
          </label>
          <div className="flex space-x-2">
            <button
              onClick={sortPricePoints}
              className="inline-flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded"
              type="button"
            >
              Sort
            </button>
            <button
              onClick={addPricePoint}
              className="inline-flex items-center px-2 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
              type="button"
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              Add Price
            </button>
          </div>
        </div>
        
        <div className="space-y-2">
          {pricePoints.map((price, index) => (
            <div key={index} className="flex items-center space-x-2">
              <span className="w-8 text-sm text-gray-600">${index + 1}</span>
              <div className="flex items-center space-x-1">
                <span className="text-sm text-gray-600">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={price}
                  onChange={(e) => updatePricePoint(index, e.target.value)}
                  className="w-24 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <button
                onClick={() => movePricePoint(index, 'up')}
                disabled={index === 0}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↑
              </button>
              <button
                onClick={() => movePricePoint(index, 'down')}
                disabled={index === pricePoints.length - 1}
                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
                type="button"
              >
                ↓
              </button>
              <button
                onClick={() => removePricePoint(index)}
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
        
        {pricePoints.length < 2 && (
          <p className="mt-2 text-sm text-red-600">At least 2 price points are required</p>
        )}
      </div>

      {/* Price Range Preview */}
      {pricePoints.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-800 mb-3">Price Range Preview:</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-700">Lowest Price:</span>
              <span className="font-medium text-blue-800">${Math.min(...pricePoints).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-700">Highest Price:</span>
              <span className="font-medium text-blue-800">${Math.max(...pricePoints).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-700">Price Range:</span>
              <span className="font-medium text-blue-800">${(Math.max(...pricePoints) - Math.min(...pricePoints)).toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-700">Number of Options:</span>
              <span className="font-medium text-blue-800">{pricePoints.length}</span>
            </div>
          </div>
        </div>
      )}

      {/* Options Preview */}
      {pricePoints.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Generated Options:</h4>
          <div className="space-y-1">
            {pricePoints.map((price, index) => (
              <div key={index} className="flex items-center p-2 bg-white border border-gray-200 rounded">
                <div className="flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 rounded-full text-sm font-medium mr-3">
                  {index + 1}
                </div>
                <span className="text-sm text-gray-700">${price.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default GaborGrangerEditor;
