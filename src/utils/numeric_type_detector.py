"""
Utility functions for intelligent numeric question type detection and validation.

This module provides functions to automatically detect the appropriate numeric
question type based on question text, labels, and context, ensuring proper
rendering and validation for different numeric input scenarios.
"""

import re
from typing import Dict, Any, Optional, Literal
from enum import Enum


class NumericType(Enum):
    """Enumeration of supported numeric question types."""
    CURRENCY = "currency"
    AGE = "age"
    QUANTITY = "quantity"
    RATING = "rating"
    PERCENTAGE = "percentage"
    MEASUREMENT = "measurement"
    GENERIC = "generic"


class NumericTypeDetector:
    """Intelligent detector for numeric question types based on content analysis."""
    
    # Age-related patterns
    AGE_PATTERNS = [
        r'\bage\b',
        r'years?\s+old',
        r'how\s+old',
        r'age\s+group',
        r'age\s+range',
        r'age\s+bracket'
    ]
    
    # Currency-related patterns
    CURRENCY_PATTERNS = [
        r'[£$€¥₹]',  # Currency symbols
        r'\bprice\b',
        r'\bcost\b',
        r'\bbudget\b',
        r'\bdollar\b',
        r'\beuro\b',
        r'\bpound\b',
        r'\byen\b',
        r'\brupee\b',
        r'local\s+currency',
        r'amount\s+in',
        r'value\s+in'
    ]
    
    # Quantity-related patterns
    QUANTITY_PATTERNS = [
        r'how\s+many',
        r'number\s+of',
        r'\bcount\b',
        r'\bitems?\b',
        r'\bunits?\b',
        r'\bpieces?\b',
        r'\binstances?\b',
        r'\boccurrences?\b',
        r'total\s+number',
        r'quantity\s+of'
    ]
    
    # Rating-related patterns
    RATING_PATTERNS = [
        r'\brate\b',
        r'\bscore\b',
        r'out\s+of',
        r'1-10',
        r'1-5',
        r'1-100',
        r'scale\s+of',
        r'level\s+of',
        r'degree\s+of',
        r'extent\s+of'
    ]
    
    # Percentage-related patterns
    PERCENTAGE_PATTERNS = [
        r'percentage',
        r'percent',
        r'%',
        r'proportion',
        r'share\s+of',
        r'portion\s+of',
        r'fraction\s+of'
    ]
    
    # Measurement-related patterns
    MEASUREMENT_PATTERNS = [
        r'\bheight\b',
        r'\bweight\b',
        r'\blength\b',
        r'\bwidth\b',
        r'\bdistance\b',
        r'\bsize\b',
        r'\barea\b',
        r'\bvolume\b',
        r'\btemperature\b',
        r'\bspeed\b',
        r'\bpressure\b',
        r'measured\s+in',
        r'units?\s+of'
    ]
    
    @classmethod
    def detect_numeric_type(
        cls, 
        question_text: str, 
        labels: Optional[list] = None,
        explicit_type: Optional[str] = None,
        methodology: Optional[str] = None
    ) -> NumericType:
        """
        Detect the most appropriate numeric type for a question.
        
        Args:
            question_text: The question text to analyze
            labels: Optional list of labels/tags associated with the question
            explicit_type: Explicitly specified numeric type (takes precedence)
            methodology: Survey methodology (e.g., 'van_westendorp')
        
        Returns:
            NumericType enum value
        """
        if explicit_type:
            try:
                return NumericType(explicit_type)
            except ValueError:
                pass  # Fall back to detection
        
        # Check methodology-specific types
        if methodology and 'van_westendorp' in methodology.lower():
            return NumericType.CURRENCY
        
        text = question_text.lower()
        labels = labels or []
        label_text = ' '.join(labels).lower()
        combined_text = f"{text} {label_text}"
        
        # Check each type in order of specificity
        if cls._matches_patterns(combined_text, cls.AGE_PATTERNS):
            return NumericType.AGE
        
        if cls._matches_patterns(combined_text, cls.CURRENCY_PATTERNS):
            return NumericType.CURRENCY
        
        if cls._matches_patterns(combined_text, cls.QUANTITY_PATTERNS):
            return NumericType.QUANTITY
        
        if cls._matches_patterns(combined_text, cls.RATING_PATTERNS):
            return NumericType.RATING
        
        if cls._matches_patterns(combined_text, cls.PERCENTAGE_PATTERNS):
            return NumericType.PERCENTAGE
        
        if cls._matches_patterns(combined_text, cls.MEASUREMENT_PATTERNS):
            return NumericType.MEASUREMENT
        
        return NumericType.GENERIC
    
    @classmethod
    def _matches_patterns(cls, text: str, patterns: list) -> bool:
        """Check if text matches any of the given patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def get_input_config(cls, numeric_type: NumericType) -> Dict[str, Any]:
        """
        Get input configuration for a specific numeric type.
        
        Args:
            numeric_type: The detected numeric type
            
        Returns:
            Dictionary with input configuration
        """
        configs = {
            NumericType.AGE: {
                'type': 'number',
                'placeholder': '25',
                'min': 0,
                'max': 120,
                'step': 1,
                'unit': 'years old',
                'label': 'Age',
                'validation': 'integer'
            },
            NumericType.CURRENCY: {
                'type': 'text',
                'placeholder': '0.00',
                'min': 0,
                'max': None,
                'step': 0.01,
                'unit': '$',
                'label': 'Amount',
                'validation': 'decimal'
            },
            NumericType.QUANTITY: {
                'type': 'number',
                'placeholder': '1',
                'min': 0,
                'max': 10000,
                'step': 1,
                'unit': 'items',
                'label': 'Quantity',
                'validation': 'integer'
            },
            NumericType.RATING: {
                'type': 'number',
                'placeholder': '5',
                'min': 1,
                'max': 10,
                'step': 1,
                'unit': 'out of 10',
                'label': 'Rating',
                'validation': 'integer'
            },
            NumericType.PERCENTAGE: {
                'type': 'number',
                'placeholder': '50',
                'min': 0,
                'max': 100,
                'step': 1,
                'unit': '%',
                'label': 'Percentage',
                'validation': 'integer'
            },
            NumericType.MEASUREMENT: {
                'type': 'number',
                'placeholder': '0',
                'min': 0,
                'max': None,
                'step': 0.1,
                'unit': 'units',
                'label': 'Measurement',
                'validation': 'decimal'
            },
            NumericType.GENERIC: {
                'type': 'number',
                'placeholder': '0',
                'min': 0,
                'max': None,
                'step': 1,
                'unit': '',
                'label': 'Value',
                'validation': 'decimal'
            }
        }
        
        return configs.get(numeric_type, configs[NumericType.GENERIC])
    
    @classmethod
    def extract_unit_from_text(cls, text: str) -> Optional[str]:
        """
        Extract unit information from question text.
        
        Args:
            text: Question text to analyze
            
        Returns:
            Extracted unit string or None
        """
        unit_patterns = [
            r'per\s+([^,.?]+)',
            r'in\s+([^,.?]+)',
            r'measured\s+in\s+([^,.?]+)',
            r'units?\s+of\s+([^,.?]+)',
            r'([a-z]+)\s*[?.,]'
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                unit = match[1].strip()
                # Filter out common non-unit words
                non_units = ['what', 'how', 'which', 'when', 'where', 'why', 'the', 'a', 'an']
                if unit.lower() not in non_units and len(unit) > 1:
                    return unit
        
        return None
    
    @classmethod
    def enhance_question_with_numeric_type(cls, question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance a question object with detected numeric type information.
        
        Args:
            question: Question dictionary to enhance
            
        Returns:
            Enhanced question dictionary
        """
        if question.get('type') not in ['numeric', 'numeric_open', 'numeric_grid']:
            return question
        
        # Detect numeric type
        numeric_type = cls.detect_numeric_type(
            question_text=question.get('text', ''),
            labels=question.get('labels', []),
            explicit_type=question.get('numeric_type'),
            methodology=question.get('methodology')
        )
        
        # Get input configuration
        config = cls.get_input_config(numeric_type)
        
        # Extract unit from text if not already specified
        unit = question.get('unit') or cls.extract_unit_from_text(question.get('text', ''))
        
        # Enhance question with detected information
        enhanced_question = question.copy()
        enhanced_question.update({
            'numeric_type': numeric_type.value,
            'unit': unit or config.get('unit'),
            'min_value': question.get('min_value', config.get('min')),
            'max_value': question.get('max_value', config.get('max')),
            'decimal_places': 2 if config.get('validation') == 'decimal' else 0
        })
        
        return enhanced_question


def detect_and_enhance_numeric_questions(survey_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a survey and enhance all numeric questions with proper type detection.
    
    Args:
        survey_data: Survey data dictionary
        
    Returns:
        Enhanced survey data with numeric type information
    """
    enhanced_data = survey_data.copy()
    
    # Process questions in sections
    if 'sections' in enhanced_data:
        for section in enhanced_data['sections']:
            if 'questions' in section:
                section['questions'] = [
                    NumericTypeDetector.enhance_question_with_numeric_type(q)
                    for q in section['questions']
                ]
    
    # Process standalone questions
    if 'questions' in enhanced_data:
        enhanced_data['questions'] = [
            NumericTypeDetector.enhance_question_with_numeric_type(q)
            for q in enhanced_data['questions']
        ]
    
    return enhanced_data
