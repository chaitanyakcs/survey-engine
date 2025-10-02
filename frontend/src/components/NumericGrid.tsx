import React from 'react';

interface NumericGridProps {
  question: {
    id: string;
    text: string;
    options?: string[];
    required?: boolean;
  };
  isPreview?: boolean;
}

const NumericGrid: React.FC<NumericGridProps> = ({ question, isPreview = true }) => {
  // Parse the question text to extract attributes (comma-separated after question mark or colon)
  const extractAttributes = (text: string): string[] => {
    // Look for comma-separated attributes after question mark or colon
    let searchText = text;
    
    // Try question mark first
    const questionMarkIndex = text.indexOf('?');
    if (questionMarkIndex !== -1) {
      searchText = text.substring(questionMarkIndex + 1).trim();
    } else {
      // Try colon as fallback
      const colonIndex = text.indexOf(':');
      if (colonIndex !== -1) {
        searchText = text.substring(colonIndex + 1).trim();
      }
    }
    
    // Remove trailing period if present
    const cleanText = searchText.replace(/\.$/, '');
    
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
          Numeric Grid Question
        </div>
        
        <div className="text-sm text-gray-600 mb-4">
          Please provide numeric values for each item:
        </div>

        <div className="min-w-full">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-300">
                <th className="text-left py-3 px-4 font-medium text-gray-700 bg-gray-100">
                  Items
                </th>
                {options.map((option, index) => (
                  <th key={index} className="text-center py-3 px-2 font-medium text-gray-700 bg-gray-100 min-w-[120px]">
                    <div className="text-xs">
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
                      <input
                        type="number"
                        name={`${question.id}_${attrIndex}_${optionIndex}`}
                        disabled={isPreview}
                        placeholder="0"
                        className="w-16 px-2 py-1 text-sm border border-gray-300 rounded text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
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

export default NumericGrid;
