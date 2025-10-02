from sqlalchemy.orm import Session
from typing import Dict, List, Any
from src.config import settings
from src.services.embedding_service import EmbeddingService
from src.utils.survey_utils import extract_all_questions
import json
import numpy as np


class ValidationService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def validate_survey(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        rfq_text: str
    ) -> Dict[str, Any]:
        """
        Validate survey against schema, methodology rules, and golden similarity
        """
        results = {
            "schema_valid": False,
            "methodology_compliant": False,
            "validation_errors": [],
            "methodology_errors": []
        }
        
        try:
            # Schema validation
            schema_validation = self._validate_schema(survey)
            results.update(schema_validation)
            
            # Methodology validation
            methodology_validation = await self._validate_methodology(survey)
            results.update(methodology_validation)
            
            return results
            
        except Exception as e:
            results["validation_errors"].append(f"Validation failed: {str(e)}")  # type: ignore
            return results
    
    async def calculate_golden_similarity(
        self,
        survey: Dict[str, Any],
        golden_examples: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate similarity score between generated survey and golden examples
        """
        try:
            if not golden_examples:
                return 0.0
            
            # Generate embedding for the generated survey
            survey_text = self._survey_to_text(survey)
            survey_embedding = await self.embedding_service.get_embedding(survey_text)
            
            # Calculate similarity with each golden example
            similarities = []
            for example in golden_examples:
                golden_text = self._survey_to_text(example["survey_json"])
                golden_embedding = await self.embedding_service.get_embedding(golden_text)
                
                # Cosine similarity
                similarity = self._cosine_similarity(survey_embedding, golden_embedding)
                similarities.append(similarity)
            
            # Return average similarity
            return sum(similarities) / len(similarities)
            
        except Exception as e:
            raise Exception(f"Similarity calculation failed: {str(e)}")
    
    def _validate_schema(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate survey JSON schema with sections support
        """
        errors = []
        
        # Required top-level fields - now supporting both old and new format
        required_fields = ["title"]
        for field in required_fields:
            if field not in survey:
                errors.append(f"Missing required field: {field}")
        
        # Check if using new sections format or old questions format
        has_sections = "sections" in survey
        has_questions = "questions" in survey
        
        if has_sections and has_questions:
            errors.append("Survey cannot have both 'sections' and 'questions' fields. Use sections format.")
        elif not has_sections and not has_questions:
            errors.append("Survey must have either 'sections' or 'questions' field")
        
        # Validate sections structure (new format)
        if has_sections:
            if not isinstance(survey["sections"], list):
                errors.append("Sections must be a list")
            else:
                # Flexible section validation - allow any number of sections with any IDs
                found_section_ids = []
                for i, section in enumerate(survey["sections"]):
                    if not isinstance(section, dict):
                        errors.append(f"Section {i} must be an object")
                        continue
                    
                    # Required section fields
                    required_section_fields = ["id", "title", "questions"]
                    for field in required_section_fields:
                        if field not in section:
                            errors.append(f"Section {i} missing required field: {field}")
                    
                    # Validate section ID (must be positive integer)
                    if "id" in section:
                        if not isinstance(section["id"], int) or section["id"] <= 0:
                            errors.append(f"Section {i} has invalid ID {section['id']}. Must be positive integer")
                        else:
                            found_section_ids.append(section["id"])
                    
                    # Validate questions within section
                    if "questions" in section:
                        if not isinstance(section["questions"], list):
                            errors.append(f"Section {i} questions must be a list")
                        else:
                            self._validate_questions_array(section["questions"], errors, f"Section {i}")
                
                # Check for duplicate section IDs
                if len(found_section_ids) != len(set(found_section_ids)):
                    errors.append("Duplicate section IDs found")
        
        # Validate questions structure (legacy format)
        elif has_questions:
            if not isinstance(survey["questions"], list):
                errors.append("Questions must be a list")
            else:
                self._validate_questions_array(survey["questions"], errors, "Survey")
        
        return {
            "schema_valid": len(errors) == 0,
            "validation_errors": errors
        }
    
    def _validate_questions_array(self, questions: List[Dict], errors: List[str], context: str):
        """
        Validate an array of questions
        """
        for i, question in enumerate(questions):
            if not isinstance(question, dict):
                errors.append(f"{context} question {i} must be an object")
                continue
            
            # Required question fields
            required_q_fields = ["text", "type"]
            for field in required_q_fields:
                if field not in question:
                    errors.append(f"{context} question {i} missing required field: {field}")
            
            # Validate question type
            if "type" in question:
                valid_types = [
                    # Basic question types
                    "multiple_choice", "single_choice", "multiple_select", "text", "open_text", 
                    "scale", "ranking", "yes_no",
                    # Advanced question types
                    "numeric_open", "matrix_likert", "constant_sum", "numeric_grid",
                    # Methodology-specific types
                    "van_westendorp", "gabor_granger", "conjoint", "maxdiff",
                    # Special types
                    "instruction", "matrix", "grid"
                ]
                if question["type"] not in valid_types:
                    errors.append(f"{context} question {i} has invalid type: {question['type']}")
                
                # Validate options for choice-based questions
                choice_types = ["multiple_choice", "single_choice", "multiple_select"]
                if question.get("type") in choice_types:
                    if "options" not in question or not isinstance(question["options"], list):
                        errors.append(f"{context} question {i} {question['type']} must have options list")
                    elif len(question.get("options", [])) == 0:
                        errors.append(f"{context} question {i} {question['type']} must have at least one option")
    
    def _extract_all_questions(self, survey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all questions from survey, supporting both sections and legacy formats
        """
        return extract_all_questions(survey)
    
    async def _validate_methodology(self, survey: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate methodology compliance based on spec requirements
        """
        errors = []
        
        # Extract methodology tags from survey
        methodology_tags = survey.get("metadata", {}).get("methodology_tags", [])
        
        for tag in methodology_tags:
            tag_lower = tag.lower()
            
            # Van Westendorp (VW) validation
            if tag_lower == "vw":
                vw_errors = self._validate_vw_methodology(survey)
                errors.extend(vw_errors)
            
            # Gabor Granger (GG) validation
            elif tag_lower == "gg":
                gg_errors = self._validate_gg_methodology(survey)
                errors.extend(gg_errors)
            
            # Conjoint validation
            elif tag_lower == "conjoint":
                conjoint_errors = self._validate_conjoint_methodology(survey)
                errors.extend(conjoint_errors)
        
        return {
            "methodology_compliant": len(errors) == 0,
            "methodology_errors": errors
        }
    
    def _validate_vw_methodology(self, survey: Dict[str, Any]) -> List[str]:
        """
        Validate Van Westendorp methodology: exactly 4 pricing questions
        """
        errors = []
        
        # Count pricing questions
        pricing_questions = []
        required_pricing_types = ["too_expensive", "too_cheap", "getting_expensive", "good_deal"]
        
        for question in self._extract_all_questions(survey):
            if question.get("methodology") == "pricing" or "price" in question.get("text", "").lower():
                pricing_questions.append(question)
        
        if len(pricing_questions) != 4:
            errors.append(f"VW methodology requires exactly 4 pricing questions, found {len(pricing_questions)}")
        
        return errors
    
    def _validate_gg_methodology(self, survey: Dict[str, Any]) -> List[str]:
        """
        Validate Gabor Granger methodology: price ladder with 5-8 incremental points
        """
        errors = []
        
        # Find price ladder questions
        price_ladder_questions = []
        for question in self._extract_all_questions(survey):
            if question.get("type") == "scale" and "price" in question.get("text", "").lower():
                if "options" in question and isinstance(question["options"], list):
                    price_ladder_questions.append(question)
        
        if not price_ladder_questions:
            errors.append("GG methodology requires at least one price ladder question")
        else:
            for question in price_ladder_questions:
                option_count = len(question.get("options", []))
                if option_count < 5 or option_count > 8:
                    errors.append(f"GG price ladder should have 5-8 price points, found {option_count}")
        
        return errors
    
    def _validate_conjoint_methodology(self, survey: Dict[str, Any]) -> List[str]:
        """
        Validate Conjoint methodology: max 15 attributes, balanced design
        """
        errors = []
        
        # Count conjoint attributes
        conjoint_attributes = []
        for question in self._extract_all_questions(survey):
            if question.get("methodology") == "conjoint" or "conjoint" in question.get("text", "").lower():
                conjoint_attributes.append(question)
        
        if len(conjoint_attributes) > 15:
            errors.append(f"Conjoint methodology should have max 15 attributes, found {len(conjoint_attributes)}")
        
        return errors
    
    def _survey_to_text(self, survey: Dict[str, Any]) -> str:
        """
        Convert survey JSON to text for embedding generation
        """
        text_parts = []
        
        if "title" in survey:
            text_parts.append(f"Title: {survey['title']}")
        
        if "description" in survey:
            text_parts.append(f"Description: {survey['description']}")
        
        # Handle both sections and legacy format
        if "sections" in survey:
            text_parts.append("Sections:")
            for section in survey["sections"]:
                text_parts.append(f"Section {section.get('id', '')}: {section.get('title', '')}")
                if "questions" in section:
                    for i, question in enumerate(section["questions"], 1):
                        text_parts.append(f"  {i}. {question.get('text', '')}")
                        if question.get("options"):
                            text_parts.append(f"  Options: {', '.join(question['options'])}")
        elif "questions" in survey:
            text_parts.append("Questions:")
            for i, question in enumerate(survey["questions"], 1):
                text_parts.append(f"{i}. {question.get('text', '')}")
                if question.get("options"):
                    text_parts.append(f"Options: {', '.join(question['options'])}")
        
        return " ".join(text_parts)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))  # type: ignore