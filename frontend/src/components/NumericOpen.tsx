import React, { useState } from 'react';

interface NumericOpenProps {
  question: {
    id: string;
    text: string;
    required?: boolean;
    methodology?: string;
  };
  isPreview?: boolean;
}

const NumericOpen: React.FC<NumericOpenProps> = ({ question, isPreview = true }) => {
  const [value, setValue] = useState<string>('');
  const [currency, setCurrency] = useState<string>('$');

  // Extract currency and unit information from question text
  const extractCurrencyInfo = (text: string) => {
    // Look for currency symbols or currency mentions
    const currencyMatch = text.match(/[£$€¥₹]/);
    if (currencyMatch) {
      return currencyMatch[0];
    }
    
    // Look for currency mentions
    const currencyTextMatch = text.match(/(?:in|using|with)\s+([A-Z]{3})/i);
    if (currencyTextMatch) {
      return currencyTextMatch[1];
    }
    
    // Look for "local currency" mentions
    if (text.toLowerCase().includes('local currency')) {
      return '$'; // Default to dollar sign
    }
    
    return '$'; // Default fallback
  };

  // Extract unit information (per box, per unit, etc.)
  const extractUnitInfo = (text: string) => {
    const unitMatch = text.match(/per\s+([^,.?]+)/i);
    if (unitMatch) {
      return unitMatch[1].trim();
    }
    return '';
  };

  const detectedCurrency = extractCurrencyInfo(question.text);
  const unit = extractUnitInfo(question.text);
  
  // Initialize currency from detected value
  React.useEffect(() => {
    setCurrency(detectedCurrency);
  }, [detectedCurrency]);

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    // Allow only numbers, decimal point, and currency symbol
    const sanitizedValue = inputValue.replace(/[^0-9.]/g, '');
    setValue(sanitizedValue);
  };

  const handleCurrencyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrency(e.target.value);
  };

  const formatDisplayValue = () => {
    if (!value) return '';
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return value;
    return numValue.toFixed(2);
  };

  const isVanWestendorp = question.methodology?.includes('van_westendorp') || 
                         question.text.toLowerCase().includes('van westendorp');

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <div className="text-sm font-medium text-gray-800 mb-4">
        {isVanWestendorp ? 'Van Westendorp Price Sensitivity' : 'Numeric Open Question'}
      </div>
      
      <div className="text-sm text-gray-600 mb-6">
        {isVanWestendorp 
          ? 'Please enter a specific price value for this question:'
          : 'Please enter a numeric value:'
        }
      </div>

      <div className="space-y-4">
        {/* Currency and value input */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Currency:</label>
            <select
              value={currency}
              onChange={handleCurrencyChange}
              disabled={isPreview}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="$">$ (USD)</option>
              <option value="€">€ (EUR)</option>
              <option value="£">£ (GBP)</option>
              <option value="¥">¥ (JPY)</option>
              <option value="₹">₹ (INR)</option>
              <option value="CAD">CAD</option>
              <option value="AUD">AUD</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Amount:</label>
            <div className="flex items-center space-x-1">
              <span className="text-gray-600">{currency}</span>
              <input
                type="text"
                value={value}
                onChange={handleValueChange}
                disabled={isPreview}
                placeholder="0.00"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Unit information */}
        {unit && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Unit:</span> {unit}
          </div>
        )}

        {/* Display formatted value */}
        {value && (
          <div className="p-3 bg-white rounded border border-gray-200">
            <div className="text-sm text-gray-600">Your response:</div>
            <div className="text-lg font-semibold text-gray-900">
              {currency}{formatDisplayValue()}
              {unit && <span className="text-sm text-gray-600 ml-1">per {unit}</span>}
            </div>
          </div>
        )}

        {/* Van Westendorp specific guidance */}
        {isVanWestendorp && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-blue-600 text-lg">ℹ️</div>
              <div>
                <h4 className="text-sm font-medium text-blue-900 mb-1">Price Sensitivity Guidance</h4>
                <p className="text-sm text-blue-800">
                  Please think about the price point where you would have the described reaction to the product. 
                  Consider your local market conditions and personal budget when entering your response.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Validation message */}
        {value && parseFloat(value) < 0 && (
          <div className="text-sm text-red-600">
            ⚠️ Please enter a positive value
          </div>
        )}
      </div>
    </div>
  );
};

export default NumericOpen;
