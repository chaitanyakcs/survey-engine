import { Question } from '../types';

/**
 * Question type labels for display
 */
export const questionTypeLabels: Record<string, string> = {
  'multiple_choice': 'Multiple Choice',
  'multiple_select': 'Multiple Select',
  'single_choice': 'Single Choice',
  'text': 'Text Input',
  'scale': 'Scale',
  'ranking': 'Ranking',
  'instruction': 'Instruction',
  'matrix': 'Matrix',
  'numeric': 'Numeric',
  'date': 'Date',
  'boolean': 'Boolean',
  'open_text': 'Open Text',
  'matrix_likert': 'Matrix Likert Scale',
  'constant_sum': 'Constant Sum',
  'gabor_granger': 'Gabor Granger',
  'numeric_grid': 'Numeric Grid',
  'numeric_open': 'Numeric Open',
  'likert': 'Likert Scale',
  'open_end': 'Open Ended',
  'display_only': 'Display Only',
  'single_open': 'Single Open',
  'multiple_open': 'Multiple Open',
  'open_ended': 'Open Ended',
  'van_westendorp': 'Van Westendorp',
  'conjoint': 'Conjoint',
  'maxdiff': 'MaxDiff'
};

/**
 * Get icon for question type
 */
export const getQuestionIcon = (type: string): string => {
  const iconMap: Record<string, string> = {
    'multiple_choice': '📋',
    'multiple_select': '☑️',
    'single_choice': '🔘',
    'text': '📝',
    'scale': '📊',
    'ranking': '🔢',
    'instruction': 'ℹ️',
    'matrix': '📋',
    'numeric': '🔢',
    'date': '📅',
    'boolean': '✅',
    'open_text': '📝',
    'matrix_likert': '📊',
    'constant_sum': '⚖️',
    'gabor_granger': '💰',
    'numeric_grid': '🔢',
    'numeric_open': '🔢',
    'likert': '📊',
    'open_end': '📝',
    'display_only': '👁️',
    'single_open': '📝',
    'multiple_open': '📝',
    'open_ended': '📝',
    'van_westendorp': '💰',
    'conjoint': '🔗',
    'maxdiff': '📊'
  };
  
  return iconMap[type] || '❓';
};

/**
 * Validate question data
 */
export const validateQuestion = (question: Partial<Question>): string[] => {
  const errors: string[] = [];
  
  if (!question.text || question.text.trim().length === 0) {
    errors.push('Question text is required');
  }
  
  if (!question.type) {
    errors.push('Question type is required');
  }
  
  // Validate options for choice-based questions
  const choiceTypes = ['multiple_choice', 'multiple_select', 'single_choice', 'ranking'];
  if (choiceTypes.includes(question.type || '') && (!question.options || question.options.length === 0)) {
    errors.push('Options are required for choice-based questions');
  }
  
  // Validate scale labels for scale questions
  if (question.type === 'scale' && (!question.scale_labels || Object.keys(question.scale_labels).length === 0)) {
    errors.push('Scale labels are required for scale questions');
  }
  
  return errors;
};

/**
 * Check if question type requires options
 */
export const requiresOptions = (type: string): boolean => {
  const typesWithOptions = [
    'multiple_choice', 'multiple_select', 'single_choice', 'ranking',
    'matrix_likert', 'constant_sum', 'gabor_granger', 'likert'
  ];
  return typesWithOptions.includes(type);
};

/**
 * Check if question type requires scale labels
 */
export const requiresScaleLabels = (type: string): boolean => {
  return type === 'scale';
};

/**
 * Check if question type is specialized (requires custom editor)
 */
export const isSpecializedType = (type: string): boolean => {
  const specializedTypes = [
    'matrix_likert', 'constant_sum', 'gabor_granger', 
    'numeric_grid', 'numeric_open', 'van_westendorp', 
    'conjoint', 'maxdiff'
  ];
  return specializedTypes.includes(type);
};

/**
 * Get default options for question type
 */
export const getDefaultOptions = (type: string): string[] => {
  const defaults: Record<string, string[]> = {
    'multiple_choice': ['Option 1', 'Option 2', 'Option 3'],
    'multiple_select': ['Option 1', 'Option 2', 'Option 3'],
    'single_choice': ['Option 1', 'Option 2', 'Option 3'],
    'ranking': ['Item 1', 'Item 2', 'Item 3'],
    'likert': ['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree'],
    'matrix_likert': ['Very Unsatisfied', 'Unsatisfied', 'Neutral', 'Satisfied', 'Very Satisfied'],
    'constant_sum': ['Feature 1', 'Feature 2', 'Feature 3'],
    'gabor_granger': ['$10', '$20', '$30', '$40', '$50'],
    'numeric_grid': ['Column 1', 'Column 2', 'Column 3'],
    'numeric_open': ['Item 1', 'Item 2', 'Item 3']
  };
  
  return defaults[type] || [];
};

/**
 * Get default scale labels for scale questions
 */
export const getDefaultScaleLabels = (): Record<string, string> => {
  return {
    '1': 'Very Poor',
    '2': 'Poor',
    '3': 'Fair',
    '4': 'Good',
    '5': 'Excellent'
  };
};

/**
 * Generate a unique question ID
 */
export const generateQuestionId = (): string => {
  return `q_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Generate a unique section ID
 */
export const generateSectionId = (): number => {
  return Date.now();
};

/**
 * Check if question is editable (not display-only)
 */
export const isEditableQuestion = (question: Question): boolean => {
  return question.type !== 'display_only' && question.type !== 'instruction';
};

/**
 * Get question category color
 */
export const getCategoryColor = (category: string): string => {
  const colorMap: Record<string, string> = {
    'screening': 'bg-yellow-100 text-yellow-800',
    'pricing': 'bg-green-100 text-green-800',
    'features': 'bg-blue-100 text-blue-800',
    'demographics': 'bg-purple-100 text-purple-800',
    'satisfaction': 'bg-orange-100 text-orange-800',
    'behavior': 'bg-indigo-100 text-indigo-800',
    'preference': 'bg-pink-100 text-pink-800',
    'default': 'bg-gray-100 text-gray-800'
  };
  
  return colorMap[category] || colorMap['default'];
};
