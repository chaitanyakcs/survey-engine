from typing import List, Dict
from difflib import SequenceMatcher
import re
import logging

logger = logging.getLogger(__name__)


class LabelNormalizer:
    """Normalize label variations for consistent RAG matching"""
    
    def __init__(self):
        # Known abbreviations and variations
        self.mappings = {
            'addl': 'additional',
            'adnl': 'additional',
            'demog': 'demographics',
            'coi': 'conflict_of_interest',
            'gg': 'gabor_granger',
            'vw': 'van_westendorp',
            'nps': 'net_promoter_score',
            'csat': 'customer_satisfaction',
            # Add more mappings as needed
        }
        
        # Separator variations
        self.separators = ['_', '-', ' ', '.']
    
    def normalize(self, label: str) -> str:
        """Normalize a single label"""
        # Convert to lowercase
        normalized = label.lower().strip()
        
        # Apply known mappings - handle underscores properly
        for abbrev, full in self.mappings.items():
            # Match whole word with word boundaries or underscore boundaries
            pattern = rf'(?<![a-zA-Z]){re.escape(abbrev)}(?![a-zA-Z])'
            normalized = re.sub(pattern, full, normalized)
        
        # Standardize separators to underscore
        for sep in self.separators:
            if sep != '_':
                normalized = normalized.replace(sep, '_')
        
        # Remove multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Capitalize properly: each_word_capitalized
        parts = normalized.split('_')
        normalized = '_'.join(p.capitalize() for p in parts)
        
        return normalized
    
    def normalize_batch(self, labels: List[str]) -> List[str]:
        """Normalize a list of labels"""
        return [self.normalize(label) for label in labels]
    
    def fuzzy_match(self, label: str, candidates: List[str], 
                    threshold: float = 0.85) -> str:
        """Find best matching label from candidates using fuzzy matching"""
        normalized_label = self.normalize(label)
        
        best_match = normalized_label
        best_score = 0.0
        
        for candidate in candidates:
            normalized_candidate = self.normalize(candidate)
            score = SequenceMatcher(None, normalized_label, normalized_candidate).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = normalized_candidate
        
        return best_match
