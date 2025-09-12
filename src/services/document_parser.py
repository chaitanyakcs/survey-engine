"""Document parsing service for converting DOCX files to JSON using LLM."""

import json
import logging
from typing import Dict, Any, Optional
from io import BytesIO
from docx import Document
import replicate
from pydantic import ValidationError

from ..models.survey import SurveyCreate, Question, QuestionType
from ..config.settings import settings

logger = logging.getLogger(__name__)

class DocumentParsingError(Exception):
    """Exception raised when document parsing fails."""
    pass

class DocumentParser:
    """Service for parsing DOCX documents and converting to survey JSON."""
    
    def __init__(self):
        if not settings.replicate_api_token:
            raise ValueError("REPLICATE_API_TOKEN is required but not set. Please set it in your environment variables or .env file.")
        replicate.api_token = settings.replicate_api_token  # type: ignore
        self.model = settings.generation_model  # Use GPT-5 from settings
    
    def extract_text_from_docx(self, docx_content: bytes) -> str:
        """Extract text content from DOCX file."""
        logger.info(f"📄 [Document Parser] Starting text extraction from DOCX, size: {len(docx_content)} bytes")
        try:
            doc = Document(BytesIO(docx_content))
            text_content = []
            
            logger.info(f"📝 [Document Parser] Processing {len(doc.paragraphs)} paragraphs")
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
                    if i < 5:  # Log first 5 paragraphs for debugging
                        logger.debug(f"📝 [Document Parser] Paragraph {i}: {paragraph.text.strip()[:100]}...")
            
            logger.info(f"📊 [Document Parser] Processing {len(doc.tables)} tables")
            # Also extract text from tables
            for table_idx, table in enumerate(doc.tables):
                logger.debug(f"📊 [Document Parser] Processing table {table_idx} with {len(table.rows)} rows")
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_content.append(" | ".join(row_text))
            
            extracted_text = "\n".join(text_content)
            logger.info(f"✅ [Document Parser] Text extraction completed, total length: {len(extracted_text)} chars")
            return extracted_text
            
        except Exception as e:
            logger.error(f"❌ [Document Parser] Failed to extract text from DOCX: {str(e)}", exc_info=True)
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
        logger.info(f"🤖 [Document Parser] Starting LLM conversion with model: {self.model}")
        try:
            logger.info(f"📝 [Document Parser] Creating conversion prompt")
            prompt = self.create_conversion_prompt(document_text)
            logger.info(f"✅ [Document Parser] Conversion prompt created, length: {len(prompt)} chars")
            
            logger.info(f"🚀 [Document Parser] Calling Replicate API")
            output = await replicate.async_run(
                self.model,
                input={
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "system_prompt": "You are a document parser. Parse the provided document into the exact JSON structure below. Be literal and strict: your output MUST be valid JSON, no prose, no backticks, no explanations, nothing else.\n\nCRITICAL: Your response must be valid JSON that can be parsed by json.loads().\n\nTop-level JSON shape required:\n{\n  \"raw_output\": { ...full extracted content and minimal normalization... },\n  \"final_output\": { ...cleaned, normalized, validated survey schema... }\n}\n\nMANDATORY STRUCTURE:\n1. \"raw_output\" must contain:\n   - \"document_text\": the full original text (unchanged)\n   - \"extraction_timestamp\": ISO 8601 timestamp\n   - \"source_file\": filename if provided, null otherwise\n   - \"error\": null (unless there was a blocking issue)\n\n2. \"final_output\" must contain:\n   - \"title\": string (required, cannot be null)\n   - \"description\": string or null\n   - \"metadata\": object with quality_score, estimated_time, methodology_tags, target_responses, source_file\n   - \"questions\": array (required, cannot be null, can be empty)\n   - \"parsing_issues\": array of strings\n\n3. Each question in \"questions\" must have:\n   - \"id\": string (q1, q2, q3...)\n   - \"text\": string (required)\n   - \"type\": string (one of: multiple_choice, scale, text, ranking, matrix, date, numeric, file_upload, boolean, unknown)\n   - \"options\": array of strings (empty for free text)\n   - \"required\": boolean\n   - \"validation\": string or null\n   - \"methodology\": string or null\n   - \"routing\": object or null\n\nRULES:\n1. ALWAYS return valid JSON - if you cannot parse something, include it as \"unknown\" type question\n2. Assign sequential IDs: q1, q2, q3...\n3. For multiple choice: put options in \"options\" array\n4. For scales: use \"type\":\"scale\" and put scale labels in \"options\"\n5. For matrices: use \"type\":\"matrix\" with validation \"matrix_per_brand:BrandA|BrandB\"\n6. For Van Westendorp: use \"methodology\":\"van_westendorp\"\n7. For MaxDiff: use \"type\":\"ranking\" with \"methodology\":\"maxdiff\"\n8. For Conjoint: use \"methodology\":\"conjoint\"\n9. Set \"required\": true for most questions, false for optional\n10. Use validation tokens: single_select, multi_select_min_1_max_3, currency_usd_min_1_max_1000, etc.\n\nEXAMPLE OUTPUT:\n{\n  \"raw_output\": {\n    \"document_text\": \"[full document text here]\",\n    \"extraction_timestamp\": \"2024-01-01T00:00:00Z\",\n    \"source_file\": null,\n    \"error\": null\n  },\n  \"final_output\": {\n    \"title\": \"Customer Satisfaction Survey\",\n    \"description\": \"Survey to measure customer satisfaction\",\n    \"metadata\": {\n      \"quality_score\": 0.9,\n      \"estimated_time\": 10,\n      \"methodology_tags\": [\"satisfaction\", \"nps\"],\n      \"target_responses\": 100,\n      \"source_file\": null\n    },\n    \"questions\": [\n      {\n        \"id\": \"q1\",\n        \"text\": \"How satisfied are you with our service?\",\n        \"type\": \"scale\",\n        \"options\": [\"Very Dissatisfied\", \"Dissatisfied\", \"Neutral\", \"Satisfied\", \"Very Satisfied\"],\n        \"required\": true,\n        \"validation\": \"single_select\",\n        \"methodology\": \"satisfaction\",\n        \"routing\": null\n      }\n    ],\n    \"parsing_issues\": []\n  }\n}\n\nNow parse the document and return ONLY the JSON structure above."
                }
            )
            
            # Replicate returns a generator, join the output
            logger.info(f"📥 [Document Parser] Processing LLM response")
            logger.debug(f"📥 [Document Parser] Output type: {type(output)}")
            logger.debug(f"📥 [Document Parser] Output value: {output}")
            
            # Handle different output types from Replicate
            if hasattr(output, '__iter__') and not isinstance(output, str):
                json_content = "".join(str(chunk) for chunk in output).strip()
            else:
                json_content = str(output).strip()
                
            logger.info(f"✅ [Document Parser] LLM response received, length: {len(json_content)} chars")
            logger.debug(f"📄 [Document Parser] LLM response preview: {json_content[:200]}...")
            
            # Try to parse the JSON
            logger.info(f"🔍 [Document Parser] Parsing JSON response")
            try:
                survey_data = json.loads(json_content)
                logger.info(f"✅ [Document Parser] JSON parsing successful")
                
                # Validate the expected structure
                if not isinstance(survey_data, dict):
                    raise ValueError("Response is not a JSON object")
                
                if "raw_output" not in survey_data or "final_output" not in survey_data:
                    logger.warning(f"⚠️ [Document Parser] Missing expected structure (raw_output/final_output)")
                    # Try to use the response as-is if it has the old structure
                    if "title" in survey_data and "questions" in survey_data:
                        logger.info(f"🔧 [Document Parser] Using legacy structure")
                        survey_data = {
                            "raw_output": {"document_text": document_text, "extraction_timestamp": "2024-01-01T00:00:00Z"},
                            "final_output": survey_data
                        }
                    else:
                        raise ValueError("Response missing required raw_output and final_output structure")
                
                logger.info(f"✅ [Document Parser] JSON structure validation successful")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [Document Parser] LLM returned invalid JSON: {str(e)}")
                logger.info(f"🔧 [Document Parser] Attempting to extract JSON from response")
                logger.debug(f"🔧 [Document Parser] Full LLM response: {json_content}")
                
                # Try multiple extraction methods
                import re
                
                # Method 1: Look for JSON between { and }
                start = json_content.find('{')
                end = json_content.rfind('}') + 1
                if start != -1 and end != 0:
                    extracted_json = json_content[start:end]
                    logger.info(f"🔧 [Document Parser] Extracted JSON substring, length: {len(extracted_json)} chars")
                    try:
                        survey_data = json.loads(extracted_json)
                        logger.info(f"✅ [Document Parser] JSON extraction and parsing successful")
                        return survey_data
                    except json.JSONDecodeError as e2:
                        logger.warning(f"⚠️ [Document Parser] Method 1 failed: {str(e2)}")
                
                # Method 2: Look for JSON in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', json_content, re.DOTALL)
                if json_match:
                    logger.info(f"🔧 [Document Parser] Found JSON in markdown code block")
                    try:
                        survey_data = json.loads(json_match.group(1))
                        logger.info(f"✅ [Document Parser] Markdown JSON extraction successful")
                        return survey_data
                    except json.JSONDecodeError as e3:
                        logger.warning(f"⚠️ [Document Parser] Method 2 failed: {str(e3)}")
                
                # Method 3: Look for any JSON object pattern
                json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', json_content, re.DOTALL)
                if json_match:
                    logger.info(f"🔧 [Document Parser] Found JSON object pattern")
                    try:
                        survey_data = json.loads(json_match.group(1))
                        logger.info(f"✅ [Document Parser] JSON object pattern extraction successful")
                        return survey_data
                    except json.JSONDecodeError as e4:
                        logger.warning(f"⚠️ [Document Parser] Method 3 failed: {str(e4)}")
                
                logger.error(f"❌ [Document Parser] All JSON extraction methods failed")
                logger.error(f"❌ [Document Parser] Raw response (first 1000 chars): {json_content[:1000]}")
                raise DocumentParsingError(f"No valid JSON found in response")
            
            logger.info(f"🎉 [Document Parser] LLM conversion completed successfully")
            return survey_data
            
        except Exception as e:
            logger.error(f"❌ [Document Parser] Failed to convert document to JSON: {str(e)}", exc_info=True)
            
            # Create a fallback response with error details
            fallback_response = {
                "raw_output": {
                    "document_text": document_text,
                    "extraction_timestamp": "2024-01-01T00:00:00Z",
                    "source_file": None,
                    "error": f"LLM conversion failed: {str(e)}"
                },
                "final_output": {
                    "title": "Document Parse Error",
                    "description": f"Failed to parse document: {str(e)}",
                    "metadata": {
                        "quality_score": 0.0,
                        "estimated_time": 0,
                        "methodology_tags": [],
                        "target_responses": None,
                        "source_file": None
                    },
                    "questions": [],
                    "parsing_issues": [f"LLM conversion failed: {str(e)}"]
                }
            }
            
            logger.warning(f"⚠️ [Document Parser] Returning fallback response due to error")
            return fallback_response
    
    def validate_survey_json(self, survey_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated JSON against our survey schema."""
        try:
            # Extract the final_output for validation
            if "final_output" in survey_data:
                final_output = survey_data["final_output"]
                logger.info(f"🔍 [Document Parser] Validating final_output structure")
                
                # Add order field to questions if missing
                if "questions" in final_output and isinstance(final_output["questions"], list):
                    for i, question in enumerate(final_output["questions"]):
                        if isinstance(question, dict) and "order" not in question:
                            question["order"] = i + 1
                
                # Create a SurveyCreate object to validate the structure
                survey = SurveyCreate(**final_output)
                validated_data = survey.model_dump()
                
                # Return the full structure with validated final_output
                return {
                    "raw_output": survey_data.get("raw_output", {}),
                    "final_output": validated_data
                }
            else:
                # Fallback for legacy format
                logger.warning(f"⚠️ [Document Parser] Using legacy format validation")
                survey = SurveyCreate(**survey_data)
                return survey.model_dump()
                
        except ValidationError as e:
            logger.error(f"Survey validation failed: {str(e)}")
            logger.error(f"Raw data structure: {list(survey_data.keys()) if isinstance(survey_data, dict) else 'Not a dict'}")
            if "final_output" in survey_data:
                logger.error(f"Final output structure: {list(survey_data['final_output'].keys()) if isinstance(survey_data.get('final_output'), dict) else 'Not a dict'}")
            
            # Try to create a minimal valid response
            try:
                logger.warning(f"⚠️ [Document Parser] Attempting to create minimal valid response")
                minimal_final_output = {
                    "title": survey_data.get("final_output", {}).get("title", "Untitled Survey"),
                    "description": survey_data.get("final_output", {}).get("description", "Survey description not available"),
                    "metadata": {
                        "quality_score": 0.3,
                        "estimated_time": 5,
                        "methodology_tags": [],
                        "target_responses": None,
                        "source_file": None
                    },
                    "questions": survey_data.get("final_output", {}).get("questions", []),
                    "parsing_issues": [f"Validation failed: {str(e)}"]
                }
                
                # Validate the minimal response
                survey = SurveyCreate(**minimal_final_output)
                validated_data = survey.model_dump()
                
                return {
                    "raw_output": survey_data.get("raw_output", {}),
                    "final_output": validated_data
                }
                
            except Exception as e2:
                logger.error(f"❌ [Document Parser] Minimal response creation also failed: {str(e2)}")
                raise DocumentParsingError(f"Generated JSON validation failed: {str(e)}")
    
    async def parse_document(self, docx_content: bytes) -> Dict[str, Any]:
        """Main method to parse DOCX document and return validated JSON."""
        logger.info(f"🤖 [Document Parser] Starting main document parsing process")
        try:
            # Extract text from DOCX
            logger.info(f"📄 [Document Parser] Extracting text from DOCX")
            document_text = self.extract_text_from_docx(docx_content)
            
            if not document_text.strip():
                logger.error(f"❌ [Document Parser] No text content found in document")
                raise DocumentParsingError("No text content found in document")
            
            logger.info(f"✅ [Document Parser] Text extraction successful, length: {len(document_text)} chars")
            
            # Convert to JSON using LLM
            logger.info(f"🤖 [Document Parser] Converting text to JSON using LLM")
            survey_json = await self.convert_to_json(document_text)
            logger.info(f"✅ [Document Parser] LLM conversion completed")
            
            # Validate the JSON
            logger.info(f"🔍 [Document Parser] Validating survey JSON structure")
            validated_survey = self.validate_survey_json(survey_json)
            logger.info(f"✅ [Document Parser] JSON validation successful")
            
            # Log final survey structure
            logger.info(f"📊 [Document Parser] Final survey structure: {list(validated_survey.keys()) if isinstance(validated_survey, dict) else 'Not a dict'}")
            if isinstance(validated_survey, dict):
                logger.info(f"📊 [Document Parser] Survey title: {validated_survey.get('title', 'No title')}")
                logger.info(f"📊 [Document Parser] Questions count: {len(validated_survey.get('questions', []))}")
                logger.info(f"📊 [Document Parser] Confidence score: {validated_survey.get('confidence_score', 'No score')}")
            
            logger.info(f"🎉 [Document Parser] Document parsing completed successfully")
            return validated_survey
            
        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"❌ [Document Parser] Unexpected error during document parsing: {str(e)}", exc_info=True)
            raise DocumentParsingError(f"Unexpected error: {str(e)}")

# Global instance
document_parser = DocumentParser()