"""
Text Requirements Validator
Validates that generated surveys include all mandatory text introduction requirements
"""

from typing import Dict, List, Any, Set
import logging

logger = logging.getLogger(__name__)

class TextRequirementsValidator:
    """Validates that surveys include required text blocks based on methodology"""
    
    # Required text blocks by methodology (from enhanced_rfq_converter.py)
    METHODOLOGY_TEXT_REQUIREMENTS = {
        "concept_test": ["Study_Intro", "Concept_Intro"],
        "product_test": ["Study_Intro", "Product_Usage"],
        "ad_test": ["Study_Intro", "Concept_Intro"],
        "package_test": ["Study_Intro", "Product_Usage"],
        "brand_tracker": ["Study_Intro", "Product_Usage"],
        "u_and_a": ["Study_Intro", "Product_Usage"],
        "segmentation": ["Study_Intro", "Confidentiality_Agreement"],
        "pricing": ["Study_Intro", "Product_Usage"],
        "van_westendorp": ["Study_Intro", "Product_Usage"],
        "gabor_granger": ["Study_Intro", "Product_Usage"],
        "conjoint": ["Study_Intro", "Confidentiality_Agreement"],
        "max_diff": ["Study_Intro"],
        "monadic": ["Study_Intro", "Concept_Intro"],
        "sequential": ["Study_Intro", "Concept_Intro"],
        "competitive": ["Study_Intro", "Product_Usage"],
        "basic_survey": ["Study_Intro"],
    }
    
    def validate_text_requirements(
        self, 
        survey: Dict[str, Any], 
        methodology_tags: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that survey includes all required text blocks for given methodologies
        """
        results = {
            "text_requirements_valid": True,
            "missing_text_blocks": [],
            "incorrectly_placed_blocks": [],
            "validation_errors": [],
            "found_text_blocks": []
        }
        
        try:
            # Get required text blocks for methodologies
            required_blocks = self._get_required_text_blocks(methodology_tags)
            if not required_blocks:
                results["text_requirements_valid"] = True
                return results
            
            # Extract text blocks from survey
            found_blocks = self._extract_text_blocks(survey)
            results["found_text_blocks"] = found_blocks
            
            # Check for missing blocks
            missing_blocks = required_blocks - set(found_blocks.keys())
            if missing_blocks:
                results["missing_text_blocks"] = list(missing_blocks)
                results["text_requirements_valid"] = False
                results["validation_errors"].append(
                    f"Missing required text blocks: {list(missing_blocks)}"
                )
            
            # Validate placement of found blocks
            placement_errors = self._validate_text_block_placement(survey, found_blocks)
            if placement_errors:
                results["incorrectly_placed_blocks"] = placement_errors
                results["text_requirements_valid"] = False
                results["validation_errors"].extend(placement_errors)
            
            logger.info(f"Text requirements validation: {results['text_requirements_valid']}")
            return results
            
        except Exception as e:
            logger.error(f"Text requirements validation failed: {str(e)}")
            results["validation_errors"].append(f"Validation failed: {str(e)}")
            results["text_requirements_valid"] = False
            return results
    
    def _get_required_text_blocks(self, methodology_tags: List[str]) -> Set[str]:
        """Get all required text blocks for given methodologies"""
        required_blocks = set()
        
        for tag in methodology_tags:
            tag_lower = tag.lower()
            requirements = self.METHODOLOGY_TEXT_REQUIREMENTS.get(tag_lower, [])
            required_blocks.update(requirements)
        
        # Always require Study_Intro
        required_blocks.add("Study_Intro")
        
        return required_blocks
    
    def _extract_text_blocks(self, survey: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract all text blocks from survey sections"""
        text_blocks = {}
        
        sections = survey.get("sections", [])
        for section in sections:
            section_id = section.get("id")
            
            # Check introText
            intro_text = section.get("introText")
            if intro_text and isinstance(intro_text, dict):
                label = intro_text.get("label", "")
                if label:
                    text_blocks[label] = {
                        "type": "introText",
                        "section_id": section_id,
                        "content": intro_text.get("content", ""),
                        "mandatory": intro_text.get("mandatory", False)
                    }
            
            # Check textBlocks
            section_text_blocks = section.get("textBlocks", [])
            if isinstance(section_text_blocks, list):
                for block in section_text_blocks:
                    if isinstance(block, dict):
                        label = block.get("label", "")
                        if label:
                            text_blocks[label] = {
                                "type": "textBlock",
                                "section_id": section_id,
                                "content": block.get("content", ""),
                                "mandatory": block.get("mandatory", False)
                            }
            
            # Check closingText
            closing_text = section.get("closingText")
            if closing_text and isinstance(closing_text, dict):
                label = closing_text.get("label", "")
                if label:
                    text_blocks[label] = {
                        "type": "closingText",
                        "section_id": section_id,
                        "content": closing_text.get("content", ""),
                        "mandatory": closing_text.get("mandatory", False)
                    }
        
        return text_blocks
    
    def _validate_text_block_placement(
        self, 
        survey: Dict[str, Any], 
        found_blocks: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Validate that text blocks are placed in correct sections"""
        errors = []
        
        # Expected placement rules
        placement_rules = {
            "Study_Intro": [1],  # Sample Plan
            "Confidentiality_Agreement": [1],  # Sample Plan
            "Product_Usage": [3],  # Brand/Product Awareness
            "Concept_Intro": [4],  # Concept Exposure
        }
        
        for block_label, block_info in found_blocks.items():
            expected_sections = placement_rules.get(block_label, [])
            actual_section = block_info.get("section_id")
            
            if expected_sections and actual_section not in expected_sections:
                errors.append(
                    f"Text block '{block_label}' should be in section {expected_sections} "
                    f"but found in section {actual_section}"
                )
        
        return errors
