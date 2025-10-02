import React, { useState, useEffect } from 'react';

interface ConstantSumProps {
  question: {
    id: string;
    text: string;
    options?: string[];
    required?: boolean;
  };
  isPreview?: boolean;
}

const ConstantSum: React.FC<ConstantSumProps> = ({ question, isPreview = true }) => {
  // Parse the question text to extract attributes and total points
  const parseConstantSumQuestion = (text: string) => {
    // Look for patterns like "allocate 100 points across the following features"
    const pointsMatch = text.match(/(\d+)\s+points?/i);
    const totalPoints = pointsMatch ? parseInt(pointsMatch[1]) : 100;
    
    // Find attributes after the colon or specific keywords
    const colonIndex = text.indexOf(':');
    if (colonIndex === -1) return { totalPoints, attributes: [] };
    
    // Get everything after the last colon
    const afterColon = text.substring(colonIndex + 1).trim();
    
    // Look for attributes after keywords like "features", "items", "options"
    const keywords = ['features', 'items', 'options', 'attributes', 'factors'];
    let attributesText = afterColon;
    
    for (const keyword of keywords) {
      const keywordMatch = afterColon.match(new RegExp(`${keyword}[\\s:]*([^.]+)`, 'i'));
      if (keywordMatch) {
        attributesText = keywordMatch[1].trim();
        break;
      }
    }
    
    // Split by comma and clean up
    const attributes = attributesText
      .split(',')
      .map(attr => attr.trim())
      .filter(attr => attr.length > 0);
    
    return { totalPoints, attributes };
  };

  const { totalPoints, attributes } = parseConstantSumQuestion(question.text);
  const [allocations, setAllocations] = useState<Record<string, number>>({});
  const [remainingPoints, setRemainingPoints] = useState(totalPoints);

  // Initialize allocations
  useEffect(() => {
    const initialAllocations: Record<string, number> = {};
    attributes.forEach(attr => {
      initialAllocations[attr] = 0;
    });
    setAllocations(initialAllocations);
  }, [attributes]);

  // Update remaining points when allocations change
  useEffect(() => {
    const usedPoints = Object.values(allocations).reduce((sum, points) => sum + points, 0);
    setRemainingPoints(totalPoints - usedPoints);
  }, [allocations, totalPoints]);

  const handleAllocationChange = (attribute: string, value: string) => {
    const numValue = Math.max(0, parseInt(value) || 0);
    setAllocations(prev => ({
      ...prev,
      [attribute]: numValue
    }));
  };

  const distributeEvenly = () => {
    const pointsPerAttribute = Math.floor(totalPoints / attributes.length);
    const remainder = totalPoints % attributes.length;
    
    const newAllocations: Record<string, number> = {};
    attributes.forEach((attr, index) => {
      newAllocations[attr] = pointsPerAttribute + (index < remainder ? 1 : 0);
    });
    setAllocations(newAllocations);
  };

  const clearAll = () => {
    const newAllocations: Record<string, number> = {};
    attributes.forEach(attr => {
      newAllocations[attr] = 0;
    });
    setAllocations(newAllocations);
  };

  if (attributes.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-yellow-800 text-sm">
            Unable to parse attributes from question text. Please ensure attributes are comma-separated after a colon.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <div className="text-sm font-medium text-gray-800 mb-4">
        Constant Sum Question
      </div>
      
      <div className="text-sm text-gray-600 mb-6">
        Please allocate <strong>{totalPoints} points</strong> across the following items to reflect their importance:
      </div>

      {/* Control buttons */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={distributeEvenly}
          disabled={isPreview}
          className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Distribute Evenly
        </button>
        <button
          onClick={clearAll}
          disabled={isPreview}
          className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Clear All
        </button>
      </div>

      {/* Allocation inputs */}
      <div className="space-y-4">
        {attributes.map((attribute, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-white rounded border border-gray-200">
            <div className="flex-1">
              <label className="text-sm font-medium text-gray-700">
                {attribute}
              </label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="number"
                min="0"
                max={totalPoints}
                value={allocations[attribute] || 0}
                onChange={(e) => handleAllocationChange(attribute, e.target.value)}
                disabled={isPreview}
                className="w-20 px-2 py-1 text-sm border border-gray-300 rounded text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <span className="text-xs text-gray-500">points</span>
            </div>
          </div>
        ))}
      </div>

      {/* Points summary */}
      <div className="mt-6 p-4 bg-white rounded border border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Total Allocated:</span>
          <span className={`text-sm font-bold ${remainingPoints === 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalPoints - remainingPoints} / {totalPoints}
          </span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-sm text-gray-600">Remaining:</span>
          <span className={`text-sm font-medium ${remainingPoints === 0 ? 'text-green-600' : 'text-red-600'}`}>
            {remainingPoints} points
          </span>
        </div>
        {remainingPoints !== 0 && (
          <div className="mt-2 text-xs text-red-600">
            ⚠️ Please allocate all {totalPoints} points to continue
          </div>
        )}
      </div>
    </div>
  );
};

export default ConstantSum;
