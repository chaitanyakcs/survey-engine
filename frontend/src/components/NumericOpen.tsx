import React, { useState } from 'react';

interface NumericOpenProps {
  question: {
    id: string;
    text: string;
    required?: boolean;
    methodology?: string;
    category?: string;
    labels?: string[];
    // New fields for better context
    numeric_type?: 'currency' | 'age' | 'quantity' | 'rating' | 'percentage' | 'measurement' | 'generic';
    unit?: string;
    min_value?: number;
    max_value?: number;
    decimal_places?: number;
  };
  isPreview?: boolean;
}

const NumericOpen: React.FC<NumericOpenProps> = ({ question, isPreview = true }) => {
  const [value, setValue] = useState<string>('');

  // Intelligent detection of numeric question type based on question text and metadata
  const detectNumericType = (): 'currency' | 'age' | 'quantity' | 'rating' | 'percentage' | 'measurement' | 'generic' => {
    const text = question.text.toLowerCase();
    const labels = question.labels || [];
    
    // Check explicit numeric_type first
    if (question.numeric_type) {
      return question.numeric_type;
    }
    
    // Age detection
    if (text.includes('age') || text.includes('years old') || text.includes('how old') || 
        labels.some(label => label.toLowerCase().includes('age'))) {
      return 'age';
    }
    
    // Currency detection
    if (text.match(/[£$€¥₹]/) || text.includes('price') || text.includes('cost') || text.includes('budget') ||
        text.includes('dollar') || text.includes('euro') || text.includes('pound') ||
        labels.some(label => label.toLowerCase().includes('price') || label.toLowerCase().includes('cost'))) {
      return 'currency';
    }
    
    // Quantity detection
    if (text.includes('how many') || text.includes('number of') || text.includes('count') ||
        text.includes('items') || text.includes('units') || text.includes('pieces') ||
        labels.some(label => label.toLowerCase().includes('quantity') || label.toLowerCase().includes('count'))) {
      return 'quantity';
    }
    
    // Rating detection
    if (text.includes('rate') || text.includes('score') || text.includes('out of') ||
        text.includes('1-10') || text.includes('1-5') || text.includes('1-100') ||
        labels.some(label => label.toLowerCase().includes('rating') || label.toLowerCase().includes('score'))) {
      return 'rating';
    }
    
    // Percentage detection
    if (text.includes('percentage') || text.includes('percent') || text.includes('%') ||
        labels.some(label => label.toLowerCase().includes('percentage'))) {
      return 'percentage';
    }
    
    // Measurement detection
    if (text.includes('height') || text.includes('weight') || text.includes('length') ||
        text.includes('width') || text.includes('distance') || text.includes('size') ||
        labels.some(label => label.toLowerCase().includes('measurement'))) {
      return 'measurement';
    }
    
    return 'generic';
  };

  const numericType = detectNumericType();
  const unit = question.unit || extractUnitFromText(question.text);
  
  // Extract unit information from question text
  function extractUnitFromText(text: string): string {
    // Look for common unit patterns
    const unitPatterns = [
      /per\s+([^,.?]+)/i,
      /in\s+([^,.?]+)/i,
      /measured\s+in\s+([^,.?]+)/i,
      /([a-z]+)\s*[?.,]/i
    ];
    
    for (const pattern of unitPatterns) {
      const match = text.match(pattern);
      if (match) {
        const unit = match[1].trim();
        // Filter out common non-unit words
        if (!['what', 'how', 'which', 'when', 'where', 'why'].includes(unit.toLowerCase())) {
          return unit;
        }
      }
    }
    
    return '';
  }

  // Get appropriate input configuration based on numeric type
  const getInputConfig = () => {
    switch (numericType) {
      case 'age':
        return {
          type: 'number',
          placeholder: '25',
          min: 0,
          max: 120,
          step: 1,
          format: (val: string) => val,
          unit: 'years old',
          label: 'Age'
        };
      
      case 'currency':
        return {
          type: 'text',
          placeholder: '0.00',
          min: 0,
          max: undefined,
          step: 0.01,
          format: (val: string) => {
            const num = parseFloat(val);
            return isNaN(num) ? val : num.toFixed(2);
          },
          unit: '$',
          label: 'Amount'
        };
      
      case 'quantity':
        return {
          type: 'number',
          placeholder: '1',
          min: 0,
          max: 10000,
          step: 1,
          format: (val: string) => val,
          unit: unit || 'items',
          label: 'Quantity'
        };
      
      case 'rating':
        return {
          type: 'number',
          placeholder: '5',
          min: 1,
          max: 10,
          step: 1,
          format: (val: string) => val,
          unit: 'out of 10',
          label: 'Rating'
        };
      
      case 'percentage':
        return {
          type: 'number',
          placeholder: '50',
          min: 0,
          max: 100,
          step: 1,
          format: (val: string) => val,
          unit: '%',
          label: 'Percentage'
        };
      
      case 'measurement':
        return {
          type: 'number',
          placeholder: '0',
          min: 0,
          max: undefined,
          step: 0.1,
          format: (val: string) => val,
          unit: unit || 'units',
          label: 'Measurement'
        };
      
      default: // generic
        return {
          type: 'number',
          placeholder: '0',
          min: question.min_value || 0,
          max: question.max_value,
          step: question.decimal_places ? 0.1 : 1,
          format: (val: string) => val,
          unit: unit || '',
          label: 'Value'
        };
    }
  };

  const inputConfig = getInputConfig();

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    
    if (numericType === 'currency') {
      // Allow only numbers and decimal point for currency
      const sanitizedValue = inputValue.replace(/[^0-9.]/g, '');
      setValue(sanitizedValue);
    } else {
      // For other types, use standard number input validation
      setValue(inputValue);
    }
  };

  const formatDisplayValue = () => {
    if (!value) return '';
    return inputConfig.format(value);
  };

  const isVanWestendorp = question.methodology?.includes('van_westendorp') || 
                         question.text.toLowerCase().includes('van westendorp');

  const getQuestionTypeLabel = () => {
    if (isVanWestendorp) return 'Van Westendorp Price Sensitivity';
    
    switch (numericType) {
      case 'age': return 'Age Question';
      case 'currency': return 'Currency Question';
      case 'quantity': return 'Quantity Question';
      case 'rating': return 'Rating Question';
      case 'percentage': return 'Percentage Question';
      case 'measurement': return 'Measurement Question';
      default: return 'Numeric Question';
    }
  };

  const getInstructionText = () => {
    if (isVanWestendorp) return 'Please enter a specific price value for this question:';
    
    switch (numericType) {
      case 'age': return 'Please enter your age:';
      case 'currency': return 'Please enter the amount:';
      case 'quantity': return 'Please enter the quantity:';
      case 'rating': return 'Please enter your rating (1-10):';
      case 'percentage': return 'Please enter the percentage (0-100):';
      case 'measurement': return 'Please enter the measurement:';
      default: return 'Please enter a numeric value:';
    }
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
      <div className="text-sm font-medium text-gray-800 mb-4">
        {getQuestionTypeLabel()}
      </div>
      
      <div className="text-sm text-gray-600 mb-6">
        {getInstructionText()}
      </div>

      <div className="space-y-4">
        {/* Input field */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">{inputConfig.label}:</label>
            <div className="flex items-center space-x-1">
              {numericType === 'currency' && (
                <span className="text-gray-600">{inputConfig.unit}</span>
              )}
              <input
                type={inputConfig.type}
                value={value}
                onChange={handleValueChange}
                disabled={isPreview}
                placeholder={inputConfig.placeholder}
                min={inputConfig.min}
                max={inputConfig.max}
                step={inputConfig.step}
                className="w-32 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              {numericType !== 'currency' && inputConfig.unit && (
                <span className="text-gray-600 text-sm">{inputConfig.unit}</span>
              )}
            </div>
          </div>
        </div>

        {/* Display formatted value */}
        {value && (
          <div className="p-3 bg-white rounded border border-gray-200">
            <div className="text-sm text-gray-600">Your response:</div>
            <div className="text-lg font-semibold text-gray-900">
              {numericType === 'currency' ? `${inputConfig.unit}${formatDisplayValue()}` : `${formatDisplayValue()} ${inputConfig.unit}`.trim()}
            </div>
          </div>
        )}

        {/* Type-specific guidance */}
        {numericType === 'age' && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-blue-600 text-lg">ℹ️</div>
              <div>
                <h4 className="text-sm font-medium text-blue-900 mb-1">Age Information</h4>
                <p className="text-sm text-blue-800">
                  Please enter your age in years. This information helps us understand our audience demographics.
                </p>
              </div>
            </div>
          </div>
        )}

        {numericType === 'rating' && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-green-600 text-lg">⭐</div>
              <div>
                <h4 className="text-sm font-medium text-green-900 mb-1">Rating Scale</h4>
                <p className="text-sm text-green-800">
                  Please rate on a scale of 1-10, where 1 is the lowest and 10 is the highest.
                </p>
              </div>
            </div>
          </div>
        )}

        {numericType === 'percentage' && (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="text-yellow-600 text-lg">📊</div>
              <div>
                <h4 className="text-sm font-medium text-yellow-900 mb-1">Percentage Input</h4>
                <p className="text-sm text-yellow-800">
                  Please enter a percentage value between 0 and 100.
                </p>
              </div>
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

        {/* Validation messages */}
        {value && parseFloat(value) < (inputConfig.min || 0) && (
          <div className="text-sm text-red-600">
            ⚠️ Please enter a value of at least {inputConfig.min}
          </div>
        )}
        
        {value && inputConfig.max && parseFloat(value) > inputConfig.max && (
          <div className="text-sm text-red-600">
            ⚠️ Please enter a value no more than {inputConfig.max}
          </div>
        )}
      </div>
    </div>
  );
};

export default NumericOpen;
