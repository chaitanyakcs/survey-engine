import React from 'react';

interface GaborGrangerProps {
  question: {
    id: string;
    text: string;
    options?: string[];
    required?: boolean;
  };
  isPreview?: boolean;
}

const GaborGranger: React.FC<GaborGrangerProps> = ({ question, isPreview = true }) => {
  // Extract price points from question text or use provided options
  const extractPricePoints = (text: string): string[] => {
    // Look for price patterns like $249, $299, etc.
    const pricePattern = /\$[\d,]+(?:\.\d{2})?/g;
    const prices = text.match(pricePattern);
    
    if (prices && prices.length > 0) {
      return prices;
    }
    
    // Fallback: look for comma-separated values that might be prices
    const commaPattern = /[\w\s]+(?:\s*,\s*[\w\s]+)+/g;
    const matches = text.match(commaPattern);
    
    if (matches && matches.length > 0) {
      // Take the longest match (most likely to be the price list)
      const longestMatch = matches.reduce((a, b) => a.length > b.length ? a : b);
      return longestMatch
        .split(',')
        .map(price => price.trim())
        .filter(price => price.length > 0);
    }
    
    return [];
  };

  const pricePoints = question.options && question.options.length > 0 
    ? question.options 
    : extractPricePoints(question.text);

  // Default price points if none found
  const defaultPricePoints = ["$249", "$299", "$349", "$399", "$449", "$499", "$549", "$599"];
  const finalPricePoints = pricePoints.length > 0 ? pricePoints : defaultPricePoints;

  const likelihoodScale = [
    "Definitely Not",
    "Probably Not", 
    "Maybe",
    "Probably Yes",
    "Definitely Yes"
  ];

  if (finalPricePoints.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <span className="text-yellow-800 text-sm">
            Unable to parse price points from question text. Please ensure price points are clearly specified.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-sm font-medium text-gray-800 mb-4">
          Gabor-Granger Price Sensitivity Question
        </div>
        
        <div className="text-sm text-gray-600 mb-4">
          Please indicate your purchase likelihood at each price point:
        </div>

        <div className="min-w-full">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-300">
                <th className="text-left py-3 px-4 font-medium text-gray-700 bg-gray-100">
                  Price Point
                </th>
                <th className="text-center py-3 px-2 font-medium text-gray-700 bg-gray-100">
                  Purchase Likelihood
                </th>
              </tr>
            </thead>
            <tbody>
              {finalPricePoints.map((price, priceIndex) => (
                <tr key={priceIndex} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-700 font-medium">
                    {price}
                  </td>
                  <td className="py-3 px-2">
                    <div className="flex flex-wrap gap-2 justify-center">
                      {likelihoodScale.map((option, optionIndex) => (
                        <label key={optionIndex} className="flex items-center text-xs">
                          <input
                            type="radio"
                            name={`${question.id}_${priceIndex}`}
                            value={optionIndex}
                            disabled={isPreview}
                            className="h-3 w-3 text-amber-600 border-gray-300 focus:ring-amber-500 mr-1"
                          />
                          <span className="text-gray-600">{option}</span>
                        </label>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GaborGranger;
