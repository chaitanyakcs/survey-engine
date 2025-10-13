import { useMemo } from 'react';
import { Question } from '../types';
import { 
  extractAttributesFromText, 
  extractPricePoints, 
  extractTotalPoints,
  extractProductName,
  reconstructQuestionText 
} from '../utils/textParsers';

interface ParsedQuestionData {
  attributes: string[];
  pricePoints: number[];
  totalPoints: number;
  productName: string;
  options: string[];
  scaleLabels: Record<string, string>;
}

export const useQuestionParser = (question: Question) => {
  const parsedData = useMemo((): ParsedQuestionData => {
    const text = question.text || '';
    
    return {
      attributes: extractAttributesFromText(text),
      pricePoints: extractPricePoints(text),
      totalPoints: extractTotalPoints(text),
      productName: extractProductName(text),
      options: question.options || [],
      scaleLabels: question.scale_labels || {}
    };
  }, [question.text, question.options, question.scale_labels]);

  const reconstructText = (
    baseText: string,
    attributes?: string[],
    options?: string[],
    totalPoints?: number
  ) => {
    return reconstructQuestionText(baseText, attributes || [], options, totalPoints);
  };

  const updateQuestionWithParsedData = (
    updates: Partial<Question>,
    parsedUpdates?: Partial<ParsedQuestionData>
  ): Partial<Question> => {
    const result = { ...updates };

    // Update text if attributes or other parsed data changed
    if (parsedUpdates) {
      let newText = result.text || question.text || '';
      
      if (parsedUpdates.attributes) {
        newText = reconstructText(newText, parsedUpdates.attributes);
      }
      
      if (parsedUpdates.totalPoints !== undefined) {
        newText = reconstructText(newText, undefined, undefined, parsedUpdates.totalPoints);
      }
      
      result.text = newText;
    }

    // Update options if provided
    if (parsedUpdates?.options) {
      result.options = parsedUpdates.options;
    }

    // Update scale labels if provided
    if (parsedUpdates?.scaleLabels) {
      result.scale_labels = parsedUpdates.scaleLabels;
    }

    return result;
  };

  const validateParsedData = (): string[] => {
    const errors: string[] = [];

    // Validate attributes for matrix types
    if (['matrix_likert', 'numeric_grid', 'constant_sum'].includes(question.type)) {
      if (parsedData.attributes.length === 0) {
        errors.push('Unable to parse attributes from question text. Please ensure attributes are comma-separated.');
      }
    }

    // Validate price points for Gabor Granger
    if (question.type === 'gabor_granger') {
      if (parsedData.pricePoints.length === 0) {
        errors.push('Unable to parse price points from question text.');
      }
    }

    // Validate total points for Constant Sum
    if (question.type === 'constant_sum') {
      if (parsedData.totalPoints < 10 || parsedData.totalPoints > 1000) {
        errors.push('Total points should be between 10 and 1000.');
      }
    }

    return errors;
  };

  const getDefaultDataForType = (type: string): Partial<ParsedQuestionData> => {
    switch (type) {
      case 'matrix_likert':
        return {
          attributes: ['Quality', 'Price', 'Service'],
          options: ['Very Unsatisfied', 'Unsatisfied', 'Neutral', 'Satisfied', 'Very Satisfied']
        };
      case 'constant_sum':
        return {
          attributes: ['Feature 1', 'Feature 2', 'Feature 3'],
          totalPoints: 100
        };
      case 'gabor_granger':
        return {
          pricePoints: [10, 20, 30, 40, 50],
          productName: 'this product'
        };
      case 'numeric_grid':
        return {
          attributes: ['Item 1', 'Item 2', 'Item 3'],
          options: ['Column 1', 'Column 2', 'Column 3']
        };
      case 'numeric_open':
        return {
          attributes: ['Item 1', 'Item 2', 'Item 3']
        };
      case 'scale':
        return {
          scaleLabels: {
            '1': 'Very Poor',
            '2': 'Poor',
            '3': 'Fair',
            '4': 'Good',
            '5': 'Excellent'
          }
        };
      default:
        return {};
    }
  };

  return {
    parsedData,
    reconstructText,
    updateQuestionWithParsedData,
    validateParsedData,
    getDefaultDataForType
  };
};
