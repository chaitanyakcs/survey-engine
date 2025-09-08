"""Document parsing service for converting DOCX files to JSON using LLM."""

import json
import logging
from typing import Dict, Any, Optional
from io import BytesIO
from docx import Document
import replicate
from pydantic import ValidationError

from ..models.survey import SurveyCreate, Question, QuestionType
from ..core.config import settings

logger = logging.getLogger(__name__)

class DocumentParsingError(Exception):
    """Exception raised when document parsing fails."""
    pass

class DocumentParser:
    """Service for parsing DOCX documents and converting to survey JSON."""
    
    def __init__(self):
        replicate.api_token = settings.replicate_api_token  # type: ignore
        self.model = "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
    
    def extract_text_from_docx(self, docx_content: bytes) -> str:
        """Extract text content from DOCX file."""
        try:
            doc = Document(BytesIO(docx_content))
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {str(e)}")
            raise DocumentParsingError(f"Failed to extract text from document: {str(e)}")
    
    def create_conversion_prompt(self, document_text: str) -> str:
        """Create the system prompt for LLM conversion."""
        
        # Define the expected JSON schema
        json_schema = {
            "title": "string (required)",
            "description": "string (required)", 
            "product_category": "string (electronics|appliances|healthcare_technology|enterprise_software|automotive|financial_services|hospitality)",
            "target_segment": "string (B2B decision makers|General consumers|Healthcare professionals|IT professionals|C-suite executives)",
            "research_goal": "string (pricing_research|feature_research|satisfaction_research|brand_research|market_sizing)",
            "methodologies": "array of strings (van_westendorp|gabor_granger|conjoint|maxdiff|brand_tracking|nps)",
            "estimated_time": "number (minutes)",
            "confidence_score": "number (0.0-1.0)",
            "questions": [
                {
                    "id": "string (required)",
                    "text": "string (required)",
                    "type": "string (multiple_choice|single_choice|scale|text|ranking|matrix|van_westendorp|gabor_granger)",
                    "options": "array of strings (for choice questions)",
                    "scale_min": "number (for scale questions)",
                    "scale_max": "number (for scale questions)",
                    "scale_labels": "array of strings (for scale questions)",
                    "required": "boolean",
                    "logic": "object (optional)"
                }
            ]
        }
        
        prompt = f"""You are an expert survey methodologist. Convert the following survey document to JSON format.

DOCUMENT TEXT:
{document_text}

INSTRUCTIONS:
1. Extract the survey structure and convert to the exact JSON schema provided below
2. Identify question types: multiple_choice, single_choice, scale, text, ranking, matrix, van_westendorp, gabor_granger
3. Detect methodologies: van_westendorp, gabor_granger, conjoint, maxdiff, brand_tracking, nps
4. Preserve question order and logic flow
5. If unsure about any field, use null rather than guessing
6. Generate a confidence_score (0.0-1.0) based on how well you could parse the document

REQUIRED JSON SCHEMA:
{json.dumps(json_schema, indent=2)}

METHODOLOGY DETECTION HINTS:
- Van Westendorp PSM: Questions about "too cheap", "too expensive", "cheap", "expensive" price points
- Gabor-Granger: Sequential price acceptance questions
- Conjoint Analysis: Choice scenarios with multiple attributes
- MaxDiff: "Most important" and "Least important" selection tasks
- Brand Tracking: Brand awareness, consideration, preference questions
- NPS: "How likely are you to recommend" questions

IMPORTANT: Return ONLY valid JSON that matches the schema exactly. No explanations or additional text.
"""
        return prompt
    
    async def convert_to_json(self, document_text: str) -> Dict[str, Any]:
        """Convert document text to JSON using LLM."""
        try:
            prompt = self.create_conversion_prompt(document_text)
            
            output = await replicate.async_run(
                self.model,
                input={
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "system_prompt": "You are an expert survey methodologist that converts survey documents to structured JSON format. Return only valid JSON with no explanations."
                }
            )
            
            # Replicate returns a generator, join the output
            json_content = "".join(output).strip()
            
            # Try to parse the JSON
            try:
                survey_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON: {str(e)}")
                # Try to extract JSON from the response if it contains explanations
                try:
                    # Look for JSON between { and }
                    start = json_content.find('{')
                    end = json_content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_content = json_content[start:end]
                        survey_data = json.loads(json_content)
                    else:
                        raise DocumentParsingError(f"No valid JSON found in response")
                except json.JSONDecodeError:
                    raise DocumentParsingError(f"LLM returned invalid JSON: {str(e)}")
            
            return survey_data
            
        except Exception as e:
            logger.error(f"Failed to convert document to JSON: {str(e)}")
            raise DocumentParsingError(f"Failed to convert document: {str(e)}")
    
    def validate_survey_json(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated JSON against our survey schema."""
        try:
            # Create a SurveyCreate object to validate the structure
            survey = SurveyCreate(**survey_data)
            return survey.model_dump()
        except ValidationError as e:
            logger.error(f"Survey validation failed: {str(e)}")
            raise DocumentParsingError(f"Generated JSON validation failed: {str(e)}")
    
    async def parse_document(self, docx_content: bytes) -> Dict[str, Any]:
        """Main method to parse DOCX document and return validated JSON."""
        try:
            # Extract text from DOCX
            document_text = self.extract_text_from_docx(docx_content)
            
            if not document_text.strip():
                raise DocumentParsingError("No text content found in document")
            
            # Convert to JSON using LLM
            survey_json = await self.convert_to_json(document_text)
            
            # Validate the JSON
            validated_survey = self.validate_survey_json(survey_json)
            
            return validated_survey
            
        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during document parsing: {str(e)}")
            raise DocumentParsingError(f"Unexpected error: {str(e)}")

# Global instance
document_parser = DocumentParser()