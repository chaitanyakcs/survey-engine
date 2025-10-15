"""
QNR Label Taxonomy Service
Manages QNR label definitions and requirements for survey structure validation
"""

from typing import Dict, List, Optional, Set
import csv
import os
import logging
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LabelDefinition:
    """Single QNR label definition"""
    name: str
    category: str
    description: str
    mandatory: bool
    applicable_labels: List[str]
    label_type: str
    detection_patterns: List[str]
    
    def __post_init__(self):
        """Build detection patterns from label name and description"""
        if not self.detection_patterns:
            self.detection_patterns = self._build_patterns()
    
    def _build_patterns(self) -> List[str]:
        """Build detection keywords from label name and description"""
        patterns = []
        
        # Convert label name to keywords
        name_words = self.name.lower().replace('_', ' ').split()
        patterns.extend(name_words)
        
        # Add description keywords
        desc_words = self.description.lower().split()
        # Filter out common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        desc_keywords = [w for w in desc_words if w not in common_words and len(w) > 2]
        patterns.extend(desc_keywords)
        
        # Add specific patterns based on label type
        if 'participation' in self.name.lower():
            patterns.extend(['participated', 'market research', 'recent study', 'past 6 months'])
        elif 'conflict' in self.name.lower() or 'coi' in self.name.lower():
            patterns.extend(['work for', 'employed by', 'conflict of interest', 'employee of'])
        elif 'demographics' in self.name.lower():
            patterns.extend(['age', 'gender', 'male', 'female', 'age range'])
        elif 'brand' in self.name.lower() and 'recall' in self.name.lower():
            patterns.extend(['brands', 'think of', 'top of mind', 'come to mind'])
        elif 'awareness' in self.name.lower() and 'funnel' in self.name.lower():
            patterns.extend(['aware', 'considered', 'purchased', 'continue', 'prefer'])
        elif 'vw_price' in self.name.lower():
            if 'too_cheap' in self.name.lower():
                patterns.extend(['too cheap', 'too inexpensive', 'suspiciously cheap'])
            elif 'bargain' in self.name.lower():
                patterns.extend(['bargain', 'good value', 'great deal', 'good price'])
            elif 'getting_expensive' in self.name.lower():
                patterns.extend(['getting expensive', 'starting to expensive', 'bit expensive'])
            elif 'too_expensive' in self.name.lower():
                patterns.extend(['too expensive', 'prohibitively expensive', 'cannot afford'])
        
        return list(set(patterns))  # Remove duplicates


class QNRLabelTaxonomy:
    """Manages QNR label definitions and requirements"""
    
    def __init__(self, csv_directory: str = "QNR_Labeling"):
        self.labels: Dict[str, LabelDefinition] = {}
        self.categories = {
            'screener': [],
            'brand': [],
            'concept': [],
            'methodology': [],
            'additional': []
        }
        self._load_from_csvs(csv_directory)
    
    def _load_from_csvs(self, directory: str):
        """Load label definitions from CSV files"""
        try:
            base_path = Path(directory)
            
            # Map CSV files to categories
            csv_files = {
                'screener': 'Screener*.csv',
                'brand': 'Brand*.csv', 
                'concept': 'Concept*.csv',
                'methodology': 'Methodology*.csv',
                'additional': 'Additional*.csv'
            }
            
            for category, pattern in csv_files.items():
                files = list(base_path.glob(pattern))
                if files:
                    self._load_category_csv(files[0], category)
                    logger.info(f"Loaded {len(self.categories[category])} {category} labels")
                else:
                    logger.warning(f"No CSV file found for category: {category}")
            
            logger.info(f"QNR Label Taxonomy loaded: {len(self.labels)} total labels")
            
        except Exception as e:
            logger.error(f"Failed to load QNR label taxonomy: {e}")
            # Initialize with empty categories to prevent crashes
            for category in self.categories:
                self.categories[category] = []
    
    def _load_category_csv(self, csv_file: Path, category: str):
        """Load labels from a specific CSV file"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    label_name = row.get('Label', '').strip()
                    if not label_name:
                        continue
                    
                    # Apply standardized naming
                    standardized_name = self._standardize_label_name(label_name)
                    
                    # Parse mandatory flag
                    mandatory = row.get('Mandatory', '').strip().lower() == 'yes'
                    
                    # Parse applicable labels
                    applicable_labels = []
                    if row.get('Applicable_Labels'):
                        applicable_labels = [l.strip() for l in row['Applicable_Labels'].split(',') if l.strip()]
                    
                    label_def = LabelDefinition(
                        name=standardized_name,
                        category=category,
                        description=row.get('Descr', '').strip(),
                        mandatory=mandatory,
                        applicable_labels=applicable_labels,
                        label_type=row.get('Type', 'QNR').strip(),
                        detection_patterns=[]  # Will be built in __post_init__
                    )
                    
                    self.labels[standardized_name] = label_def
                    self.categories[category].append(label_def)
                    
        except Exception as e:
            logger.error(f"Failed to load CSV {csv_file}: {e}")
    
    def _standardize_label_name(self, original_name: str) -> str:
        """Apply standardized naming conventions"""
        # Apply Option B standardization
        name_mappings = {
            # Screener section
            'CoI_Check': 'Conflict_Of_Interest_Check',
            'Demog_Basic': 'Demographics_Basic',
            'Category_Usage_Adnl': 'Category_Usage_Additional',
            'Category_Usage_Consider': 'Category_Usage_Consideration',
            'User_Categorization_Logic': 'User_Category_Rules',
            
            # Brand section
            'Brand_awareness_funnel': 'Brand_Awareness_Funnel',
            'Brand_Product_Satisfaction': 'Product_Satisfaction',
            'Purchase_Decision': 'Purchase_Decision_Influence',
            'Brand_Recall': 'Brand_Recall_Unaided',
            
            # Concept section
            'Message_reaction': 'Message_Reaction',
            'Concept_impression': 'Concept_Impression',
            'Concept_eval_funnel': 'Concept_Evaluation_Funnel',
            
            # Methodology section
            'VW_pricing': 'VW_Price_Generic',  # Will be replaced with 4 specific labels
            'VW_Likelihood': 'VW_Purchase_Likelihood',
            'GG_Likelihood': 'GG_Price_Acceptance',
        }
        
        # Apply mapping if exists
        if original_name in name_mappings:
            return name_mappings[original_name]
        
        # Fix casing issues
        parts = original_name.split('_')
        standardized_parts = []
        for part in parts:
            if part.lower() in ['coi', 'adnl', 'demog']:
                # These should be handled by mappings above
                standardized_parts.append(part)
            else:
                # Capitalize first letter of each part
                standardized_parts.append(part.capitalize())
        
        return '_'.join(standardized_parts)
    
    def get_required_labels(self, section_id: int, methodology: Optional[List[str]] = None,
                          industry: Optional[str] = None) -> List[LabelDefinition]:
        """Get required labels for a section based on context"""
        section_map = {
            1: [],  # Sample Plan - no question labels, just text blocks
            2: 'screener',
            3: 'brand',
            4: 'concept',
            5: 'methodology',
            6: 'additional',
            7: []  # Programmer Instructions
        }
        
        category = section_map.get(section_id)
        if not category:
            return []
        
        labels = self.categories.get(category, [])
        
        # Filter by methodology
        if methodology and category == 'methodology':
            labels = [l for l in labels if self._matches_methodology(l, methodology)]
        
        # Filter by industry
        if industry:
            labels = [l for l in labels if self._matches_industry(l, industry)]
        
        return [l for l in labels if l.mandatory]
    
    def _matches_methodology(self, label: LabelDefinition, methodologies: List[str]) -> bool:
        """Check if label applies to given methodologies"""
        if not label.applicable_labels:
            return True
        
        methodology_lower = [m.lower() for m in methodologies]
        applicable_lower = [a.lower() for a in label.applicable_labels]
        
        return any(m in applicable_lower for m in methodology_lower)
    
    def _matches_industry(self, label: LabelDefinition, industry: str) -> bool:
        """Check if label applies to given industry"""
        if not label.applicable_labels:
            return True
        
        industry_lower = industry.lower()
        applicable_lower = [a.lower() for a in label.applicable_labels]
        
        return any(industry_lower in a for a in applicable_lower)
    
    def get_label_definition(self, label_name: str) -> Optional[LabelDefinition]:
        """Get definition for a specific label"""
        return self.labels.get(label_name)
    
    def get_all_labels(self) -> Dict[str, LabelDefinition]:
        """Get all label definitions"""
        return self.labels.copy()
    
    def get_labels_by_category(self, category: str) -> List[LabelDefinition]:
        """Get all labels in a specific category"""
        return self.categories.get(category, []).copy()
    
    def get_van_westendorp_labels(self) -> List[str]:
        """Get the 4 required Van Westendorp labels"""
        return [
            'VW_Price_Too_Cheap',
            'VW_Price_Bargain', 
            'VW_Price_Getting_Expensive',
            'VW_Price_Too_Expensive'
        ]
    
    def is_van_westendorp_label(self, label_name: str) -> bool:
        """Check if a label is one of the Van Westendorp 4"""
        return label_name in self.get_van_westendorp_labels()
    
    def get_critical_screener_labels(self) -> List[str]:
        """Get critical screener labels that should never be missing"""
        return [
            'Recent_Participation',
            'Conflict_Of_Interest_Check',
            'Demographics_Basic'
        ]
    
    def is_critical_screener_label(self, label_name: str) -> bool:
        """Check if a label is critical for screener section"""
        return label_name in self.get_critical_screener_labels()


