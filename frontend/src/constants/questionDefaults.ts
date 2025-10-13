/**
 * Default options for different question types
 */
export const DEFAULT_QUESTION_OPTIONS: Record<string, string[]> = {
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

/**
 * Default scale labels for scale questions
 */
export const DEFAULT_SCALE_LABELS: Record<string, string> = {
  '1': 'Very Poor',
  '2': 'Poor',
  '3': 'Fair',
  '4': 'Good',
  '5': 'Excellent'
};

/**
 * Default categories for questions
 */
export const DEFAULT_CATEGORIES = [
  'screening',
  'pricing',
  'features',
  'demographics',
  'satisfaction',
  'behavior',
  'preference',
  'other'
];

/**
 * Default methodologies
 */
export const DEFAULT_METHODOLOGIES = [
  'van_westendorp',
  'gabor_granger',
  'conjoint',
  'maxdiff',
  'basic_survey',
  'brand_tracking',
  'concept_testing',
  'usage_attitudes'
];

/**
 * Question type groups for organization
 */
export const QUESTION_TYPE_GROUPS = {
  'Choice Questions': [
    'multiple_choice',
    'multiple_select',
    'single_choice',
    'ranking'
  ],
  'Scale Questions': [
    'scale',
    'likert',
    'matrix_likert'
  ],
  'Text Questions': [
    'text',
    'open_text',
    'open_end',
    'single_open',
    'multiple_open',
    'open_ended'
  ],
  'Specialized Questions': [
    'matrix_likert',
    'constant_sum',
    'gabor_granger',
    'numeric_grid',
    'numeric_open',
    'van_westendorp',
    'conjoint',
    'maxdiff'
  ],
  'Other': [
    'instruction',
    'display_only',
    'numeric',
    'date',
    'boolean'
  ]
};

/**
 * Default section titles
 */
export const DEFAULT_SECTION_TITLES = [
  'Introduction',
  'Screening Questions',
  'Main Questions',
  'Demographics',
  'Additional Questions',
  'Closing'
];

/**
 * Validation rules for different question types
 */
export const VALIDATION_RULES = {
  'text': {
    minLength: 1,
    maxLength: 1000,
    required: true
  },
  'options': {
    minCount: 2,
    maxCount: 20,
    maxLength: 200
  },
  'attributes': {
    minCount: 1,
    maxCount: 15,
    maxLength: 100
  },
  'pricePoints': {
    minCount: 2,
    maxCount: 10,
    minValue: 0,
    maxValue: 10000
  },
  'totalPoints': {
    minValue: 10,
    maxValue: 1000
  }
};

/**
 * Error messages for validation
 */
export const VALIDATION_MESSAGES = {
  REQUIRED_FIELD: 'This field is required',
  INVALID_TEXT_LENGTH: 'Text must be between 1 and 1000 characters',
  INVALID_OPTIONS_COUNT: 'Must have between 2 and 20 options',
  INVALID_ATTRIBUTES_COUNT: 'Must have between 1 and 15 attributes',
  INVALID_PRICE_POINTS: 'Must have between 2 and 10 price points',
  INVALID_PRICE_VALUE: 'Price must be between $0 and $10,000',
  INVALID_TOTAL_POINTS: 'Total points must be between 10 and 1000',
  DUPLICATE_VALUES: 'Values must be unique',
  INVALID_NUMBER: 'Must be a valid number'
};
