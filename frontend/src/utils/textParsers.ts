/**
 * Extract comma-separated attributes from question text
 * Used by MatrixLikert, NumericGrid, ConstantSum editors
 */
export const extractAttributesFromText = (text: string): string[] => {
  if (!text || typeof text !== 'string') {
    return [];
  }

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

/**
 * Extract price points from Gabor Granger question text
 */
export const extractPricePoints = (text: string): number[] => {
  if (!text || typeof text !== 'string') {
    return [];
  }

  // Look for price patterns like "$30, $35, $40" or "30, 35, 40"
  const pricePattern = /\$?(\d+(?:\.\d{2})?)/g;
  const matches = text.match(pricePattern);
  
  if (matches) {
    return matches.map(match => {
      // Remove $ sign and convert to number
      const cleanMatch = match.replace('$', '');
      return parseFloat(cleanMatch);
    }).filter(price => !isNaN(price));
  }
  
  return [];
};

/**
 * Extract total points from Constant Sum question text
 */
export const extractTotalPoints = (text: string): number => {
  if (!text || typeof text !== 'string') {
    return 100; // Default
  }

  // Look for patterns like "allocate 100 points across the following features"
  const pointsMatch = text.match(/(\d+)\s+points?/i);
  return pointsMatch ? parseInt(pointsMatch[1]) : 100;
};

/**
 * Reconstruct question text from structured data
 */
export const reconstructQuestionText = (
  baseText: string,
  attributes: string[],
  options?: string[],
  totalPoints?: number
): string => {
  if (!baseText || typeof baseText !== 'string') {
    return '';
  }

  // For matrix_likert and numeric_grid, replace the attributes part
  if (attributes && attributes.length > 0) {
    // Find where to insert the attributes
    const colonIndex = baseText.indexOf(':');
    const questionMarkIndex = baseText.indexOf('?');
    const periodIndex = baseText.indexOf('.');
    
    let insertIndex = -1;
    if (colonIndex !== -1) {
      insertIndex = colonIndex + 1;
    } else if (questionMarkIndex !== -1) {
      insertIndex = questionMarkIndex + 1;
    } else if (periodIndex !== -1) {
      insertIndex = periodIndex + 1;
    }
    
    if (insertIndex !== -1) {
      const beforeText = baseText.substring(0, insertIndex).trim();
      const afterText = baseText.substring(insertIndex).trim();
      
      // Remove existing attributes from afterText
      const cleanAfterText = afterText.replace(/[^,]*,[^,]*,[^,]*.*/, '').trim();
      
      return `${beforeText} ${attributes.join(', ')}${cleanAfterText ? ' ' + cleanAfterText : ''}`;
    }
  }
  
  // For constant_sum, replace total points
  if (totalPoints !== undefined) {
    return baseText.replace(/\d+\s+points?/i, `${totalPoints} points`);
  }
  
  return baseText;
};

/**
 * Extract product name from Gabor Granger question text
 */
export const extractProductName = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  // Look for patterns like "How much would you pay for [Product Name]?"
  const patterns = [
    /for\s+([^?]+)\?/i,
    /pay\s+for\s+([^?]+)\?/i,
    /buy\s+([^?]+)\?/i,
    /purchase\s+([^?]+)\?/i
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  return '';
};

/**
 * Clean and normalize text input
 */
export const cleanText = (text: string): string => {
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  return text.trim().replace(/\s+/g, ' ');
};

/**
 * Validate attribute list
 */
export const validateAttributes = (attributes: string[]): string[] => {
  const errors: string[] = [];
  
  if (!attributes || attributes.length === 0) {
    errors.push('At least one attribute is required');
    return errors;
  }
  
  // Check for empty attributes
  const emptyAttributes = attributes.filter(attr => !attr.trim());
  if (emptyAttributes.length > 0) {
    errors.push('All attributes must have text');
  }
  
  // Check for duplicate attributes
  const uniqueAttributes = new Set(attributes.map(attr => attr.trim().toLowerCase()));
  if (uniqueAttributes.size !== attributes.length) {
    errors.push('Attributes must be unique');
  }
  
  // Check attribute length
  const longAttributes = attributes.filter(attr => attr.length > 100);
  if (longAttributes.length > 0) {
    errors.push('Attributes should be less than 100 characters');
  }
  
  return errors;
};

/**
 * Validate price points
 */
export const validatePricePoints = (pricePoints: number[]): string[] => {
  const errors: string[] = [];
  
  if (!pricePoints || pricePoints.length === 0) {
    errors.push('At least one price point is required');
    return errors;
  }
  
  // Check for valid numbers
  const invalidPrices = pricePoints.filter(price => isNaN(price) || price < 0);
  if (invalidPrices.length > 0) {
    errors.push('All price points must be valid positive numbers');
  }
  
  // Check for reasonable range
  const maxPrice = Math.max(...pricePoints);
  const minPrice = Math.min(...pricePoints);
  if (maxPrice > 10000) {
    errors.push('Price points should be reasonable (less than $10,000)');
  }
  
  if (minPrice < 0) {
    errors.push('Price points cannot be negative');
  }
  
  return errors;
};
