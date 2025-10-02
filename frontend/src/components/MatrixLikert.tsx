import React from 'react';

interface MatrixLikertProps {
  question: {
    id: string;
    text: string;
    options?: string[];
    required?: boolean;
  };
  isPreview?: boolean;
}

const MatrixLikert: React.FC<MatrixLikertProps> = ({ question, isPreview = true }) => {
  // Parse the question text to extract attributes (comma-separated after question mark)
  const extractAttributes = (text: string): string[] => {
    // Look for comma-separated attributes after the question mark
    // Pattern: "...? Attribute1, Attribute2, Attribute3."
    const questionMarkIndex = text.indexOf('?');
    if (questionMarkIndex === -1) return [];
    
    // Get everything after the question mark
    const afterQuestionMark = text.substring(questionMarkIndex + 1).trim();
    
    // Remove trailing period if present
    const cleanText = afterQuestionMark.replace(/\.$/, '');
    
    // Split by comma and clean up
    return cleanText
      .split(',')
      .map(attr => attr.trim())
      .filter(attr => attr.length > 0);
  };

  const attributes = extractAttributes(question.text);
  const options = question.options || [];

  if (attributes.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-yellow-800 text-sm">
            Unable to parse attributes from question text. Please ensure attributes are comma-separated.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-sm font-medium text-gray-800 mb-4">
          Matrix Likert Scale Question
        </div>
        
        <div className="text-sm text-gray-600 mb-4">
          Please rate each attribute using the scale provided:
        </div>

        <div className="min-w-full">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-300">
                <th className="text-left py-3 px-4 font-medium text-gray-700 bg-gray-100">
                  Attributes
                </th>
                {options.map((option, index) => (
                  <th key={index} className="text-center py-3 px-2 font-medium text-gray-700 bg-gray-100 min-w-[120px]">
                    <div className="text-xs">
                      {index + 1}
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {option}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {attributes.map((attribute, attrIndex) => (
                <tr key={attrIndex} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-700 font-medium">
                    {attribute}
                  </td>
                  {options.map((option, optionIndex) => (
                    <td key={optionIndex} className="text-center py-3 px-2">
                      <label className="flex items-center justify-center">
                        <input
                          type="radio"
                          name={`${question.id}_${attrIndex}`}
                          value={optionIndex}
                          disabled={isPreview}
                          className="h-4 w-4 text-amber-600 border-gray-300 focus:ring-amber-500"
                        />
                      </label>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MatrixLikert;
