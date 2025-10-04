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
  // Parse the question text to extract attributes (comma-separated after question mark, colon, or period)
  const extractAttributes = (text: string): string[] => {
    // Look for comma-separated attributes after question mark, colon, or period
    let searchText = text;

    // Check for question mark first
    const questionMarkIndex = text.indexOf('?');
    if (questionMarkIndex !== -1) {
      searchText = text.substring(questionMarkIndex + 1).trim();
    } else {
      // Check for colon
      const colonIndex = text.indexOf(':');
      if (colonIndex !== -1) {
        searchText = text.substring(colonIndex + 1).trim();
      } else {
        // Check for period (for statements like "Rate the following items. Item1, Item2, Item3")
        const periodIndex = text.indexOf('.');
        if (periodIndex !== -1) {
          searchText = text.substring(periodIndex + 1).trim();
        } else {
          // Fallback: if no punctuation found, try to find patterns like "at the following" or "priced at"
          // This handles cases like "priced at the following per box of 6 monthly lenses. $30, $35, $40"
          const followingPatterns = [
            "at the following",
            "priced at",
            "the following",
            "as follows"
          ];
          for (const pattern of followingPatterns) {
            const patternIndex = text.toLowerCase().indexOf(pattern);
            if (patternIndex !== -1) {
              // Look for the next period or end of string
              const nextPeriod = text.indexOf('.', patternIndex);
              if (nextPeriod !== -1) {
                searchText = text.substring(nextPeriod + 1).trim();
                break;
              } else {
                // If no period after pattern, take everything after the pattern
                searchText = text.substring(patternIndex + pattern.length).trim();
                break;
              }
            }
          }
        }
      }
    }

    // Remove trailing period if present
    const cleanText = searchText.replace(/\.$/, '');
    
    // Split by comma and clean up
    let attributes = cleanText
      .split(',')
      .map(attr => attr.trim())
      .filter(attr => attr.length > 0);

    // If no attributes found with the above methods, try a more aggressive approach
    // Look for any comma-separated list in the text
    if (attributes.length === 0) {
      // Look for patterns like "$30, $35, $40" or "Item1, Item2, Item3"
      const pricePattern = /\$[\d,]+(?:\.\d{2})?(?:\s*,\s*\$?\d+(?:\.\d{2})?)+/g;
      const wordPattern = /[A-Za-z][A-Za-z0-9\s]*(?:\s*,\s*[A-Za-z][A-Za-z0-9\s]*)+/g;
      const generalPattern = /[\w\s]+(?:\s*,\s*[\w\s]+)+/g;
      
      const patterns = [pricePattern, wordPattern, generalPattern];
      
      for (const pattern of patterns) {
        const matches = text.match(pattern);
        if (matches && matches.length > 0) {
          // Take the longest match (most likely to be the attribute list)
          const longestMatch = matches.reduce((a, b) => a.length > b.length ? a : b);
          attributes = longestMatch
            .split(',')
            .map(attr => attr.trim())
            .filter(attr => attr.length > 0);
          if (attributes.length > 1) {
            break;
          }
        }
      }
      
      // If still no attributes, try the simple approach: find the last comma-separated list
      if (attributes.length === 0) {
        const lastComma = text.lastIndexOf(',');
        if (lastComma !== -1) {
          // Look backwards to find the start of the list
          let start = text.lastIndexOf('.', lastComma);
          if (start === -1) {
            start = text.lastIndexOf(':', lastComma);
          }
          if (start === -1) {
            start = text.lastIndexOf('?', lastComma);
          }
          
          if (start !== -1) {
            const listText = text.substring(start + 1).trim();
            attributes = listText
              .split(',')
              .map(attr => attr.trim())
              .filter(attr => attr.length > 0);
            // Clean up any trailing periods
            if (attributes.length > 0 && attributes[attributes.length - 1].endsWith('.')) {
              attributes[attributes.length - 1] = attributes[attributes.length - 1].replace(/\.$/, '');
            }
          }
        }
      }
    }

    return attributes;
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


