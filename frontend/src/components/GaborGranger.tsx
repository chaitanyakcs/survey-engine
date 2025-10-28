import React from 'react';

interface GaborGrangerProps {
  question: {
    id: string;
    text: string;
    options?: string[];
    scale_labels?: Record<string, string>;
    required?: boolean;
  };
  isPreview?: boolean;
  showQuestionText?: boolean;
}

const GaborGranger: React.FC<GaborGrangerProps> = ({ question, isPreview = true, showQuestionText = true }) => {
  // Extract metadata
  const extractMetadata = () => {
    const text = question.text;
    
    // Product name from question or text
    const productMatch = text.match(/purchase\s+(Product_[A-Z]|GoPro[^\s?]+)/i);
    const product = productMatch ? productMatch[1] : 'this product';
    
    // Clean question text
    let cleanText = text
      .replace(/\[.*?\]/g, '')
      .replace(/On a scale of.*?purchase[',]/gi, '')
      .replace(/\$[\d,]+(?:\.\d{2})?/g, '')
      .trim();
    
    // If text is messy, create simple version
    if (cleanText.length > 150 || cleanText.includes('CQ0')) {
      cleanText = `How likely would you be to purchase ${product}?`;
    }
    
    return { product, cleanText };
  };
  
  const { cleanText } = extractMetadata();
  
  // Price points from options
  const pricePoints = question.options || [];
  
  // Scale labels
  const scaleLabels = question.scale_labels || {
    '1': 'Definitely will not purchase',
    '2': 'Probably will not purchase',
    '3': 'May or may not purchase',
    '4': 'Probably will purchase',
    '5': 'Definitely will purchase'
  };
  
  if (pricePoints.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-800">
          No price points specified for this Gabor-Granger question.
        </p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Clean question text - only if showQuestionText is true */}
      {showQuestionText && (
        <div className="text-base font-medium text-gray-900">
          {cleanText}
        </div>
      )}
      
      {/* Scale legend */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="text-sm font-medium text-blue-900 mb-2">Purchase Likelihood Scale:</div>
        <div className="grid grid-cols-5 gap-2 text-xs text-blue-800">
          {Object.entries(scaleLabels).map(([num, label]) => (
            <div key={num} className="text-center">
              <span className="font-semibold">{num}</span> = {label}
            </div>
          ))}
        </div>
      </div>
      
      {/* Price point grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse bg-white rounded-lg overflow-hidden shadow-sm">
          <thead>
            <tr className="bg-gray-100 border-b border-gray-300">
              <th className="text-left py-3 px-4 font-semibold text-gray-700">
                Price Point
              </th>
              <th className="text-center py-3 px-4 font-semibold text-gray-700">
                Purchase Likelihood (1-5)
              </th>
            </tr>
          </thead>
          <tbody>
            {pricePoints.map((price, idx) => (
              <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                <td className="py-3 px-4 font-medium text-gray-900">
                  {price}
                </td>
                <td className="py-3 px-4">
                  <div className="flex justify-center gap-4">
                    {['1', '2', '3', '4', '5'].map((value) => (
                      <label key={value} className="flex flex-col items-center cursor-pointer">
                        <input
                          type="radio"
                          name={`${question.id}_${idx}`}
                          value={value}
                          disabled={isPreview}
                          className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-xs text-gray-600 mt-1">{value}</span>
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
  );
};

export default GaborGranger;
