"""Document parsing service for converting DOCX files to JSON using LLM."""

import json
import logging
from typing import Dict, Any, Optional, List
from io import BytesIO
from docx import Document
import replicate
from pydantic import ValidationError
import uuid
import time

from ..models.survey import SurveyCreate, Question, QuestionType
from ..config.settings import settings
from ..utils.error_messages import UserFriendlyError, get_api_configuration_error
from ..utils.llm_audit_decorator import LLMAuditContext
from ..services.llm_audit_service import LLMAuditService

logger = logging.getLogger(__name__)

class DocumentParsingError(Exception):
    """Exception raised when document parsing fails."""
    pass

class DocumentParser:
    """Service for parsing DOCX documents and converting to survey JSON."""

    def __init__(self, db_session: Optional[Any] = None, rfq_parsing_manager: Optional[Any] = None):
        if not settings.replicate_api_token:
            error_info = get_api_configuration_error()
            raise UserFriendlyError(
                message=error_info["message"],
                technical_details="REPLICATE_API_TOKEN environment variable is not set",
                action_required="Configure AI service provider (Replicate or OpenAI)"
            )
        self.replicate_client = replicate.Client(api_token=settings.replicate_api_token)
        self.model = self._get_rfq_parsing_model(db_session)  # Get model from RFQ parsing settings
        self.db_session = db_session
        self.rfq_parsing_manager = rfq_parsing_manager

    def _get_rfq_parsing_model(self, db_session: Optional[Any] = None) -> str:
        """Get RFQ parsing model from database settings or fallback to config"""
        try:
            logger.info(f"🔍 [DocumentParser] Starting RFQ parsing model selection...")
            logger.info(f"🔍 [DocumentParser] Database session available: {bool(db_session)}")
            logger.info(f"🔍 [DocumentParser] Config default model: {settings.generation_model}")
            
            if db_session:
                from src.services.settings_service import SettingsService
                settings_service = SettingsService(db_session)
                rfq_settings = settings_service.get_rfq_parsing_settings()
                
                logger.info(f"🔍 [DocumentParser] Database RFQ parsing settings: {rfq_settings}")
                
                if rfq_settings and 'parsing_model' in rfq_settings:
                    model = rfq_settings['parsing_model']
                    logger.info(f"🔧 [DocumentParser] Using model from RFQ parsing settings: {model}")
                    logger.info(f"🔧 [DocumentParser] Model source: RFQ_PARSING_DATABASE")
                    return model
                else:
                    logger.info(f"🔧 [DocumentParser] No RFQ parsing settings found, using config default: {settings.generation_model}")
                    logger.info(f"🔧 [DocumentParser] Model source: CONFIG_FALLBACK")
                    return settings.generation_model
            else:
                logger.info(f"🔧 [DocumentParser] No database session, using config default: {settings.generation_model}")
                logger.info(f"🔧 [DocumentParser] Model source: CONFIG_NO_DB")
                return settings.generation_model
        except Exception as e:
            logger.warning(f"⚠️ [DocumentParser] Failed to get RFQ parsing model from database: {str(e)}")
            logger.info(f"🔧 [DocumentParser] Using config default: {settings.generation_model}")
            logger.info(f"🔧 [DocumentParser] Model source: CONFIG_ERROR_FALLBACK")
            return settings.generation_model

    async def _send_progress(self, session_id: str, stage: str, progress: int, message: str, details: Optional[str] = None):
        """Send progress update via WebSocket if manager is available."""
        if self.rfq_parsing_manager and session_id:
            progress_data = {
                "type": "progress",
                "stage": stage,
                "progress": progress,
                "message": message,
                "details": details,
                "timestamp": time.time()
            }
            try:
                await self.rfq_parsing_manager.send_progress(session_id, progress_data)
                logger.debug(f"📤 [DocumentParser] Sent progress: {stage} ({progress}%)")
            except Exception as e:
                logger.warning(f"⚠️ [DocumentParser] Failed to send progress update: {str(e)}")
    
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
            
            # Create audit context for this LLM interaction
            interaction_id = f"document_parsing_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if self.db_session else None
            
            # Try to use audit service, but don't let audit failures break the core functionality
            try:
                if audit_service:
                    async with LLMAuditContext(
                        audit_service=audit_service,
                        interaction_id=interaction_id,
                        model_name=self.model,
                        model_provider="replicate",
                        purpose="document_parsing",
                        input_prompt=prompt,
                        sub_purpose="survey_conversion",
                        context_type="document",
                        hyperparameters={
                            "temperature": 0.1,
                            "max_tokens": 4000
                        },
                        metadata={
                            "document_length": len(document_text),
                            "prompt_length": len(prompt)
                        },
                        tags=["document_parsing", "survey_conversion"]
                    ) as audit_context:
                        logger.info(f"🚀 [Document Parser] Calling Replicate API with auditing")
                        start_time = time.time()
                        output = await self.replicate_client.async_run(
                            self.model,
                            input={
                                "prompt": prompt,
                                "temperature": 0.1,
                                "max_tokens": 4000,
                                "system_prompt": "You are a document parser. Parse the provided document into the exact JSON structure below. Be literal and strict: your output MUST be valid JSON, no prose, no backticks, no explanations, nothing else.\n\nCRITICAL: Your response must be valid JSON that can be parsed by json.loads().\n\nTop-level JSON shape required:\n{\n  \"raw_output\": { ...full extracted content and minimal normalization... },\n  \"final_output\": { ...cleaned, normalized, validated survey schema... }\n}\n\nMANDATORY STRUCTURE:\n1. \"raw_output\" must contain:\n   - \"document_text\": the full original text (unchanged)\n   - \"extraction_timestamp\": ISO 8601 timestamp\n   - \"source_file\": filename if provided, null otherwise\n   - \"error\": null (unless there was a blocking issue)\n\n2. \"final_output\" must contain:\n   - \"title\": string (required, cannot be null)\n   - \"description\": string or null\n   - \"metadata\": object with quality_score, estimated_time, methodology_tags, target_responses, source_file\n   - \"questions\": array (required, cannot be null, can be empty)\n   - \"parsing_issues\": array of strings\n\n3. Each question in \"questions\" must have:\n   - \"id\": string (q1, q2, q3...)\n   - \"text\": string (required)\n   - \"type\": string (one of: multiple_choice, scale, text, ranking, matrix, date, numeric, file_upload, boolean, unknown)\n   - \"options\": array of strings (empty for free text)\n   - \"required\": boolean\n   - \"validation\": string or null\n   - \"methodology\": string or null\n   - \"routing\": object or null\n\nRULES:\n1. ALWAYS return valid JSON - if you cannot parse something, include it as \"unknown\" type question\n2. Assign sequential IDs: q1, q2, q3...\n3. For multiple choice: put options in \"options\" array\n4. For scales: use \"type\":\"scale\" and put scale labels in \"options\"\n5. For matrices: use \"type\":\"matrix\" with validation \"matrix_per_brand:BrandA|BrandB\"\n6. For Van Westendorp: use \"methodology\":\"van_westendorp\"\n7. For MaxDiff: use \"type\":\"ranking\" with \"methodology\":\"maxdiff\"\n8. For Conjoint: use \"methodology\":\"conjoint\"\n9. Set \"required\": true for most questions, false for optional\n10. Use validation tokens: single_select, multi_select_min_1_max_3, currency_usd_min_1_max_1000, etc.\n\nEXAMPLE OUTPUT:\n{\n  \"raw_output\": {\n    \"document_text\": \"[full document text here]\",\n    \"extraction_timestamp\": \"2024-01-01T00:00:00Z\",\n    \"source_file\": null,\n    \"error\": null\n  },\n  \"final_output\": {\n    \"title\": \"Customer Satisfaction Survey\",\n    \"description\": \"Survey to measure customer satisfaction\",\n    \"metadata\": {\n      \"quality_score\": 0.9,\n      \"estimated_time\": 10,\n      \"methodology_tags\": [\"satisfaction\", \"nps\"],\n      \"target_responses\": 100,\n      \"source_file\": null\n    },\n    \"questions\": [\n      {\n        \"id\": \"q1\",\n        \"text\": \"How satisfied are you with our service?\",\n        \"type\": \"scale\",\n        \"options\": [\"Very Dissatisfied\", \"Dissatisfied\", \"Neutral\", \"Satisfied\", \"Very Satisfied\"],\n        \"required\": true,\n        \"validation\": \"single_select\",\n        \"methodology\": \"satisfaction\",\n        \"routing\": null\n      }\n    ],\n    \"parsing_issues\": []\n  }\n}\n\nNow parse the document and return ONLY the JSON structure above."
                            }
                        )
                        
                        # Process the output and set audit context
                        response_time_ms = int((time.time() - start_time) * 1000)
                        audit_context.set_output(
                            output_content=str(output)
                        )
                else:
                    # Fallback without auditing
                    logger.info(f"🚀 [Document Parser] Calling Replicate API without auditing")
                    output = await self.replicate_client.async_run(
                        self.model,
                        input={
                        "prompt": prompt,
                        "temperature": 0.1,
                        "max_tokens": 4000,
                        "system_prompt": "You are a document parser. Parse the provided document into the exact JSON structure below. Be literal and strict: your output MUST be valid JSON, no prose, no backticks, no explanations, nothing else.\n\nCRITICAL: Your response must be valid JSON that can be parsed by json.loads().\n\nTop-level JSON shape required:\n{\n  \"raw_output\": { ...full extracted content and minimal normalization... },\n  \"final_output\": { ...cleaned, normalized, validated survey schema... }\n}\n\nMANDATORY STRUCTURE:\n1. \"raw_output\" must contain:\n   - \"document_text\": the full original text (unchanged)\n   - \"extraction_timestamp\": ISO 8601 timestamp\n   - \"source_file\": filename if provided, null otherwise\n   - \"error\": null (unless there was a blocking issue)\n\n2. \"final_output\" must contain:\n   - \"title\": string (required, cannot be null)\n   - \"description\": string or null\n   - \"metadata\": object with quality_score, estimated_time, methodology_tags, target_responses, source_file\n   - \"questions\": array (required, cannot be null, can be empty)\n   - \"parsing_issues\": array of strings\n\n3. Each question in \"questions\" must have:\n   - \"id\": string (q1, q2, q3...)\n   - \"text\": string (required)\n   - \"type\": string (one of: multiple_choice, scale, text, ranking, matrix, date, numeric, file_upload, boolean, unknown)\n   - \"options\": array of strings (empty for free text)\n   - \"required\": boolean\n   - \"validation\": string or null\n   - \"methodology\": string or null\n   - \"routing\": object or null\n\nRULES:\n1. ALWAYS return valid JSON - if you cannot parse something, include it as \"unknown\" type question\n2. Assign sequential IDs: q1, q2, q3...\n3. For multiple choice: put options in \"options\" array\n4. For scales: use \"type\":\"scale\" and put scale labels in \"options\"\n5. For matrices: use \"type\":\"matrix\" with validation \"matrix_per_brand:BrandA|BrandB\"\n6. For Van Westendorp: use \"methodology\":\"van_westendorp\"\n7. For MaxDiff: use \"type\":\"ranking\" with \"methodology\":\"maxdiff\"\n8. For Conjoint: use \"methodology\":\"conjoint\"\n9. Set \"required\": true for most questions, false for optional\n10. Use validation tokens: single_select, multi_select_min_1_max_3, currency_usd_min_1_max_1000, etc.\n\nEXAMPLE OUTPUT:\n{\n  \"raw_output\": {\n    \"document_text\": \"[full document text here]\",\n    \"extraction_timestamp\": \"2024-01-01T00:00:00Z\",\n    \"source_file\": null,\n    \"error\": null\n  },\n  \"final_output\": {\n    \"title\": \"Customer Satisfaction Survey\",\n    \"description\": \"Survey to measure customer satisfaction\",\n    \"metadata\": {\n      \"quality_score\": 0.9,\n      \"estimated_time\": 10,\n      \"methodology_tags\": [\"satisfaction\", \"nps\"],\n      \"target_responses\": 100,\n      \"source_file\": null\n    },\n    \"questions\": [\n      {\n        \"id\": \"q1\",\n        \"text\": \"How satisfied are you with our service?\",\n        \"type\": \"scale\",\n        \"options\": [\"Very Dissatisfied\", \"Dissatisfied\", \"Neutral\", \"Satisfied\", \"Very Satisfied\"],\n        \"required\": true,\n        \"validation\": \"single_select\",\n        \"methodology\": \"satisfaction\",\n        \"routing\": null\n      }\n    ],\n    \"parsing_issues\": []\n  }\n}\n\nNow parse the document and return ONLY the JSON structure above."
                    }
                )
            except Exception as audit_error:
                # If audit fails, log the error but continue with core functionality
                logger.warning(f"⚠️ [Document Parser] Audit system failed, continuing without audit: {str(audit_error)}")
                logger.info(f"🚀 [Document Parser] Calling Replicate API without auditing (audit failed)")
                output = await self.replicate_client.async_run(
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
            logger.info(f"📄 [Document Parser] LLM response preview: {json_content[:500]}...")
            logger.info(f"📄 [Document Parser] LLM response ending: ...{json_content[-200:]}")
            
            # Try to parse the JSON
            logger.info(f"🔍 [Document Parser] Parsing JSON response")
            try:
                survey_data = json.loads(json_content)
                logger.info(f"✅ [Document Parser] JSON parsing successful")
                logger.info(f"📊 [Document Parser] Parsed data keys: {list(survey_data.keys()) if isinstance(survey_data, dict) else 'Not a dict'}")
                logger.info(f"📊 [Document Parser] Full parsed data: {survey_data}")
                
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
    
    def create_rfq_extraction_prompt(self, document_text: str) -> str:
        """Create the system prompt for RFQ-specific data extraction."""

        prompt = f"""You are an expert research consultant. Extract RFQ (Request for Quotation) information from the following document and convert it to structured data.

DOCUMENT TEXT:
{document_text}

FIELD PRIORITIZATION (extract in this order of importance):
CRITICAL FIELDS (highest priority - extract first):
1. title - The main title or subject of the RFQ (usually in headers or at the beginning)
2. description - Core description of what research is needed (often the largest text block)
3. objectives - Specific research objectives or goals (look for numbered lists, bullet points)

HIGH PRIORITY FIELDS:
4. research_goal - Overall purpose of the research (business questions to answer)
5. target_segment - Target audience or demographics (age groups, income levels, behaviors)
6. product_category - The product/service being researched (explicit mentions or context clues)

MEDIUM PRIORITY FIELDS:
7. constraints - Budget, timeline, methodology constraints (look for "must", "cannot", "within")
8. deliverables - Expected outputs (reports, presentations, data files)
9. timeline - Project deadlines or milestones

SURVEY STRUCTURE FIELDS (methodology-driven):
10. qnr_sections - Required QNR sections based on methodology (7-section standard)
11. text_requirements - Required text introductions based on methodology
12. survey_logic - Survey logic requirements (piping, sampling, screener logic)
13. brand_usage_requirements - Brand tracking and usage requirements

SIMPLIFIED FIELD-SPECIFIC EXTRACTION GUIDANCE:

CRITICAL FIELDS (extract with high confidence):

TITLE (Critical):
- Keywords: "title", "project", "study", "research", headers, bold text
- Patterns: "Research Study", "Market Research", "RFQ:", document title
- Strategy: Extract from document headers, subject lines, first prominent text

DESCRIPTION (Critical):
- Keywords: "overview", "description", "purpose", "objective", "we need"
- Patterns: Introduction paragraphs, executive summary text
- Strategy: Extract comprehensive overview paragraphs

COMPANY_PRODUCT_BACKGROUND (Critical):
- Keywords: "company", "background", "business", "product", "about us"
- Patterns: "Company background", "Business context", "About [company]"
- Strategy: Extract company and product context paragraphs

BUSINESS_PROBLEM (High):
- Keywords: "problem", "challenge", "issue", "need", "goal"
- Patterns: "Business challenge", "We need to", "The problem is"
- Strategy: Extract problem statement sentences

BUSINESS_OBJECTIVE (High):
- Keywords: "objective", "goal", "achieve", "outcome", "want to"
- Patterns: "Business objective", "We want to achieve", "The goal is"
- Strategy: Extract objective statements

METHODOLOGY DETECTION (High):
- Van Westendorp: "van westendorp", "price sensitivity", "too cheap", "too expensive"
- Gabor Granger: "gabor granger", "price acceptance", "purchase intent"
- Conjoint: "conjoint", "trade-off", "choice task", "feature importance"
- Strategy: Keyword-based methodology detection

RESEARCH_AUDIENCE (Medium):
- Keywords: "audience", "target", "respondents", "participants", "demographics"
- Patterns: "Target audience", "Respondent profile", demographic descriptions
- Strategy: Extract audience descriptions

SAMPLE_PLAN (Medium):
- Keywords: "sample", "LOI", "length of interview", "recruiting", "n="
- Patterns: "Sample size", "LOI: X minutes", "Recruit X participants"
- Strategy: Extract sampling specifications

SURVEY STRUCTURE FIELDS (methodology-driven):

QNR_SECTIONS_DETECTED (Medium):
- Keywords: "questionnaire", "survey sections", "screener", "demographics", "concept"
- Patterns: Based on detected methodologies (see methodology mapping below)
- Strategy: Auto-detect required QNR sections based on methodology
- Default sections: ["sample_plan", "screener", "brand_awareness", "concept_exposure", "methodology_section", "additional_questions", "programmer_instructions"]

TEXT_REQUIREMENTS_DETECTED (Medium):
- Keywords: "introduction", "instructions", "confidentiality", "study intro", "concept presentation"
- Patterns: Based on methodology requirements (see text requirements mapping below)
- Strategy: Auto-detect required text blocks based on methodology

SURVEY_LOGIC_REQUIREMENTS (Medium):
- requires_piping_logic: Keywords: "pipe", "carry forward", "previous answer", "based on response"
- requires_sampling_logic: Keywords: "random", "quota", "balance", "representative sample"
- requires_screener_logic: Keywords: "qualify", "screen out", "terminate", "continue if", "skip if"
- custom_logic_requirements: Keywords: "logic", "skip pattern", "routing", "conditional"
- Strategy: Infer logic needs from content complexity and methodology

BRAND_USAGE_REQUIREMENTS (Medium):
- brand_recall_required: Keywords: "brand awareness", "top of mind", "unaided", "aided recall"
- brand_awareness_funnel: Keywords: "awareness", "consideration", "trial", "purchase", "loyalty"
- brand_product_satisfaction: Keywords: "satisfaction", "rating", "experience", "recommend"
- usage_frequency_tracking: Keywords: "how often", "frequency", "usage", "habits", "occasions"
- Strategy: Detect brand/product research focus

ENHANCED BUSINESS CONTEXT (Medium):
- stakeholder_requirements: Keywords: "stakeholders", "requirements", "needs", "expectations"
- decision_criteria: Keywords: "criteria", "decision", "evaluate", "success metrics"
- budget_range: Keywords: "budget", "cost", "investment", "under", "over", "$", "k", "million"
- timeline_constraints: Keywords: "urgent", "deadline", "timeline", "rush", "flexible", "standard"

ENHANCED RESEARCH OBJECTIVES (Medium):
- success_metrics: Keywords: "success", "metrics", "KPI", "measure", "target", "goal"
- validation_requirements: Keywords: "validate", "verify", "confirm", "test", "proof"
- measurement_approach: Keywords: "quantitative", "qualitative", "mixed", "approach", "method"

ENHANCED METHODOLOGY (Medium):
- complexity_level: Keywords: "simple", "standard", "complex", "advanced", "basic", "sophisticated"
- required_methodologies: Keywords: Multiple methodology names in array format
- sample_size_target: Keywords: "sample", "respondents", "participants", "n=", "size"

ENHANCED SURVEY REQUIREMENTS (Medium):
- completion_time_target: Keywords: "time", "minutes", "duration", "length", "LOI"
- device_compatibility: Keywords: "mobile", "desktop", "tablet", "device", "responsive"
- accessibility_requirements: Keywords: "accessibility", "ADA", "508", "WCAG", "accessible"
- data_quality_requirements: Keywords: "quality", "validation", "attention", "checks"

EXTRACTION STRATEGY:
1. First scan for CRITICAL FIELDS using field-specific patterns above
2. Look for explicit section headers that match field types
3. Identify numbered/bulleted lists that may contain objectives or constraints
4. Use field-specific language patterns for targeted extraction
5. For missing CRITICAL FIELDS, be more aggressive - synthesize from available context
6. For MEDIUM PRIORITY fields, extract if clear evidence exists
7. Apply METHODOLOGY-BASED AUTO-DETECTION for survey structure fields using mappings below

METHODOLOGY-TO-QNR-SECTIONS MAPPING:
- concept_test: ["sample_plan", "screener", "brand_awareness", "concept_exposure", "methodology_section", "additional_questions", "programmer_instructions"]
- conjoint: ["sample_plan", "screener", "concept_exposure", "methodology_section", "additional_questions", "programmer_instructions"]
- van_westendorp/gabor_granger: ["sample_plan", "screener", "brand_awareness", "methodology_section", "additional_questions", "programmer_instructions"]
- brand_tracker: ["sample_plan", "screener", "brand_awareness", "additional_questions", "programmer_instructions"]
- max_diff: ["sample_plan", "screener", "methodology_section", "additional_questions", "programmer_instructions"]

METHODOLOGY-TO-TEXT-REQUIREMENTS MAPPING:
- concept_test: ["Study_Intro", "Concept_Intro"]
- conjoint: ["Study_Intro", "Confidentiality_Agreement"]
- van_westendorp/gabor_granger: ["Study_Intro", "Product_Usage"]
- brand_tracker: ["Study_Intro", "Product_Usage"]
- max_diff: ["Study_Intro"]
- All methodologies: Always include "Study_Intro" (mandatory)

SURVEY_LOGIC AUTO-DETECTION RULES:
- Requires Piping Logic: If conjoint, complex branching, or "based on previous response" detected
- Requires Sampling Logic: If quota requirements, randomization, or balanced design mentioned
- Requires Screener Logic: If qualification criteria, screening questions, or termination logic present

BRAND_USAGE AUTO-DETECTION RULES:
- Brand Recall Required: If brand awareness, recall, or brand tracking mentioned
- Brand Awareness Funnel: If awareness-to-purchase funnel or brand consideration mentioned
- Brand Product Satisfaction: If satisfaction, ratings, or experience evaluation mentioned
- Usage Frequency Tracking: If usage patterns, frequency, or habits research mentioned

CONFIDENCE SCORING GUIDELINES:
- 0.9-1.0: Explicit mention with clear mapping (exact field labels or unambiguous content)
- 0.7-0.8: Strong contextual evidence (business language patterns, section positioning)
- 0.5-0.6: Reasonable inference from surrounding context
- 0.3-0.4: Weak inference or partial information
- 0.0-0.2: Speculative or very uncertain

INSTRUCTIONS:
1. Extract the following RFQ components following the prioritization above:
   - Research objectives and goals (CRITICAL)
   - Business context and background (HIGH)
   - Target audience and demographics (HIGH)
   - Constraints (budget, timeline, sample size, methodology) (MEDIUM)
   - Stakeholder requirements
   - Success metrics
   - Preferred or excluded methodologies

2. Structure the output as JSON with the following schema:
   - confidence: number (0.0-1.0) - how confident you are in the extraction
   - identified_sections: object with potential matches for each RFQ component
   - extracted_entities: object with lists of identified entities (stakeholders, industries, etc.)
   - field_mappings: array of specific field mappings with confidence scores

3. For each field mapping, include:
   - field: the RFQ field name (prioritized as above)
   - value: the extracted value
   - confidence: extraction confidence (0.0-1.0)
   - source: the text snippet this was extracted from
   - reasoning: why this text maps to this field
   - priority: field priority level (critical/high/medium)

EXPECTED JSON STRUCTURE:
{{
  "confidence": 0.85,
  "identified_sections": {{
    "objectives": {{
      "confidence": 0.9,
      "source_text": "extracted text snippet",
      "source_section": "section where found",
      "extracted_data": ["objective 1", "objective 2"]
    }},
    "business_context": {{ ... }},
    "target_audience": {{ ... }},
    "constraints": {{ ... }},
    "methodologies": {{ ... }}
  }},
  "extracted_entities": {{
    "stakeholders": ["decision maker", "end user"],
    "industries": ["technology", "healthcare"],
    "research_types": ["market research", "pricing study"],
    "methodologies": ["van westendorp", "conjoint analysis"]
  }},
  "field_mappings": [
    {{
      "field": "title",
      "value": "Product Feature Research Study",
      "confidence": 0.95,
      "source": "Title: Product Feature Research Study",
      "reasoning": "Clear title in document header",
      "priority": "critical"
    }},
    {{
      "field": "description",
      "value": "Research to understand customer preferences for new product features",
      "confidence": 0.85,
      "source": "We need to understand what features customers value most...",
      "reasoning": "Main research description in introduction",
      "priority": "critical"
    }},
    {{
      "field": "company_product_background",
      "value": "TechCorp is a leading software company developing productivity tools for small businesses.",
      "confidence": 0.80,
      "source": "About TechCorp: We are a leading software company...",
      "reasoning": "Company background section with clear business context",
      "priority": "critical"
    }},
    {{
      "field": "business_problem",
      "value": "Need to prioritize which features to develop for next product release",
      "confidence": 0.85,
      "source": "The challenge we face is determining which features...",
      "reasoning": "Clear problem statement in business context",
      "priority": "high"
    }},
    {{
      "field": "primary_method",
      "value": "conjoint",
      "confidence": 0.90,
      "source": "We want to use conjoint analysis to understand feature trade-offs",
      "reasoning": "Explicit mention of conjoint analysis methodology",
      "priority": "high"
    }},
    {{
      "field": "research_audience",
      "value": "Small business owners, 25-50 years old, currently using productivity software",
      "confidence": 0.9,
      "source": "Target participants: small business owners aged 25-50...",
      "reasoning": "Clear demographic and behavioral criteria",
      "priority": "medium"
    }},
    {{
      "field": "qnr_sections_detected",
      "value": ["sample_plan", "screener", "concept_exposure", "methodology_section", "additional_questions", "programmer_instructions"],
      "confidence": 0.80,
      "source": "Conjoint analysis methodology detected",
      "reasoning": "Based on conjoint methodology, these QNR sections are required",
      "priority": "medium"
    }},
    {{
      "field": "text_requirements_detected",
      "value": ["Study_Intro", "Confidentiality_Agreement"],
      "confidence": 0.9,
      "source": "Conjoint study with sensitive data collection",
      "reasoning": "Conjoint studies require study intro and confidentiality agreement",
      "priority": "medium"
    }},
    {{
      "field": "requires_piping_logic",
      "value": true,
      "confidence": 0.9,
      "source": "Complex conjoint design with feature dependencies",
      "reasoning": "Conjoint analysis typically requires piping logic for dynamic choice tasks",
      "priority": "medium"
    }},
    {{
      "field": "requires_sampling_logic",
      "value": false,
      "confidence": 0.65,
      "source": "No specific quota or randomization requirements mentioned",
      "reasoning": "Standard sampling approach implied",
      "priority": "medium"
    }},
    {{
      "field": "brand_recall_required",
      "value": false,
      "confidence": 0.80,
      "source": "Focus on product features, not brand awareness",
      "reasoning": "Feature research doesn't require brand recall questions",
      "priority": "medium"
    }}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON, no explanations or additional text
- Use null for missing or unclear information
- Be conservative with confidence scores
- Include source text snippets for traceability
"""
        return prompt

    async def extract_rfq_data(self, document_text: str) -> Dict[str, Any]:
        """Extract RFQ-specific data from document text using LLM."""
        logger.info(f"🎯 [Document Parser] Starting RFQ data extraction")
        try:
            prompt = self.create_rfq_extraction_prompt(document_text)
            logger.info(f"📝 [Document Parser] Created RFQ extraction prompt, length: {len(prompt)} chars")

            # Create audit context for this LLM interaction
            interaction_id = f"rfq_extraction_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if self.db_session else None
            
            # Try to use audit service, but don't let audit failures break the core functionality
            try:
                if audit_service:
                    async with LLMAuditContext(
                        audit_service=audit_service,
                        interaction_id=interaction_id,
                        model_name=self.model,
                        model_provider="replicate",
                        purpose="document_parsing",
                        input_prompt=prompt,
                        sub_purpose="rfq_extraction",
                        context_type="document",
                        hyperparameters={
                            "temperature": 0.1,
                            "max_tokens": 3000
                        },
                        metadata={
                            "document_length": len(document_text),
                            "prompt_length": len(prompt)
                        },
                        tags=["document_parsing", "rfq_extraction"]
                    ) as audit_context:
                        logger.info(f"🚀 [Document Parser] Calling Replicate API for RFQ extraction with auditing")
                        start_time = time.time()
                        output = await self.replicate_client.async_run(
                            self.model,
                            input={
                                "prompt": prompt,
                                "temperature": 0.1,
                                "max_tokens": 3000,
                                "system_prompt": "You are an expert at extracting structured information from research documents. Return only valid JSON that matches the exact schema provided."
                            }
                        )
                        
                        # Process the output and set audit context
                        response_time_ms = int((time.time() - start_time) * 1000)
                        audit_context.set_output(
                            output_content=str(output)
                        )
                else:
                    # Fallback without auditing
                    logger.info(f"🚀 [Document Parser] Calling Replicate API for RFQ extraction without auditing")
                    output = await self.replicate_client.async_run(
                        self.model,
                        input={
                            "prompt": prompt,
                            "temperature": 0.1,
                            "max_tokens": 3000,
                            "system_prompt": "You are an expert at extracting structured information from research documents. Return only valid JSON that matches the exact schema provided."
                        }
                    )
            except Exception as audit_error:
                # If audit fails, log the error but continue with core functionality
                logger.warning(f"⚠️ [Document Parser] Audit system failed, continuing without audit: {str(audit_error)}")
                logger.info(f"🚀 [Document Parser] Calling Replicate API for RFQ extraction without auditing (audit failed)")
                output = await self.replicate_client.async_run(
                    self.model,
                    input={
                        "prompt": prompt,
                        "temperature": 0.1,
                        "max_tokens": 3000,
                        "system_prompt": "You are an expert at extracting structured information from research documents. Return only valid JSON that matches the exact schema provided."
                    }
                )

            # Process the response
            if hasattr(output, '__iter__') and not isinstance(output, str):
                json_content = "".join(str(chunk) for chunk in output).strip()
            else:
                json_content = str(output).strip()

            logger.info(f"✅ [Document Parser] RFQ extraction response received, length: {len(json_content)} chars")
            logger.info(f"🔍 [Document Parser] Raw LLM response: {json_content[:500]}...")

            # Parse and validate JSON using robust extraction like survey generation
            rfq_data = self._extract_rfq_json(json_content)
            logger.info(f"✅ [Document Parser] RFQ data parsing successful")
            logger.info(f"🔍 [Document Parser] Parsed data keys: {list(rfq_data.keys())}")
            return rfq_data

        except Exception as e:
            logger.error(f"❌ [Document Parser] Failed to extract RFQ data: {str(e)}", exc_info=True)
            return self._get_fallback_rfq_structure(str(e))

    def _extract_rfq_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract RFQ JSON from raw LLM output using multiple strategies.
        Based on the robust extraction method from survey generation.
        """
        logger.info(f"🔍 [Document Parser] Starting JSON extraction from raw text (length: {len(raw_text)})")

        # Strategy 1: Try to parse JSON directly without any sanitization
        logger.info("🔧 [Document Parser] Trying direct JSON parsing (no sanitization)...")
        try:
            result = json.loads(raw_text)
            logger.info(f"✅ [Document Parser] Direct JSON parsing succeeded! Keys: {list(result.keys())}")
            self._validate_and_fix_rfq_structure(result)
            return result
        except json.JSONDecodeError as e:
            logger.info(f"⚠️ [Document Parser] Direct JSON parsing failed: {e}")
            logger.info(f"🔍 [Document Parser] JSON error at position {e.pos}: {raw_text[max(0, e.pos-50):e.pos+50]}")

        # Strategy 2: Try to extract JSON from markdown code blocks
        logger.info("🔧 [Document Parser] Trying JSON extraction from markdown...")
        try:
            import re
            # Look for JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
            if json_match:
                extracted_json = json_match.group(1)
                logger.info(f"🔧 [Document Parser] Found JSON in markdown code block, length: {len(extracted_json)}")
                result = json.loads(extracted_json)
                logger.info(f"✅ [Document Parser] Markdown JSON extraction succeeded!")
                self._validate_and_fix_rfq_structure(result)
                return result
        except (json.JSONDecodeError, AttributeError) as e:
            logger.info(f"⚠️ [Document Parser] Markdown JSON extraction failed: {e}")

        # Strategy 3: Try to find JSON between first { and last }
        logger.info("🔧 [Document Parser] Trying JSON extraction between braces...")
        try:
            import re
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end != 0 and end > start:
                extracted_json = raw_text[start:end]
                logger.info(f"🔧 [Document Parser] Found JSON between braces, length: {len(extracted_json)}")
                result = json.loads(extracted_json)
                logger.info(f"✅ [Document Parser] Braces JSON extraction succeeded!")
                self._validate_and_fix_rfq_structure(result)
                return result
        except json.JSONDecodeError as e:
            logger.info(f"⚠️ [Document Parser] Braces JSON extraction failed: {e}")

        # Strategy 4: Try gentle sanitization and parse
        logger.info("🔧 [Document Parser] Trying gentle sanitization...")
        try:
            sanitized = self._gentle_sanitize_json(raw_text)
            result = json.loads(sanitized)
            logger.info(f"✅ [Document Parser] Sanitized JSON parsing succeeded!")
            self._validate_and_fix_rfq_structure(result)
            return result
        except json.JSONDecodeError as e:
            logger.info(f"⚠️ [Document Parser] Sanitized JSON parsing failed: {e}")

        # Strategy 5: Try to extract field mappings array specifically
        logger.info("🔧 [Document Parser] Trying field mappings extraction...")
        try:
            field_mappings = self._extract_field_mappings_from_text(raw_text)
            if field_mappings:
                logger.info(f"✅ [Document Parser] Extracted {len(field_mappings)} field mappings from text")
                return {
                    "confidence": 0.9,
                    "identified_sections": {},
                    "extracted_entities": {
                        "stakeholders": [],
                        "industries": [],
                        "research_types": [],
                        "methodologies": []
                    },
                    "field_mappings": field_mappings
                }
        except Exception as e:
            logger.info(f"⚠️ [Document Parser] Field mappings extraction failed: {e}")

        # All strategies failed - return fallback
        logger.error(f"❌ [Document Parser] All JSON extraction strategies failed!")
        logger.error(f"❌ [Document Parser] Raw response: {raw_text[:1000]}...")
        return self._get_fallback_rfq_structure("All JSON extraction strategies failed")

    def _gentle_sanitize_json(self, raw_text: str) -> str:
        """Gentle JSON sanitization to fix common LLM output issues"""
        import re

        logger.info(f"🧹 [Document Parser] Starting gentle sanitization of text (length: {len(raw_text)})")

        # Remove any text before the first {
        start_idx = raw_text.find('{')
        if start_idx > 0:
            raw_text = raw_text[start_idx:]
            logger.info(f"🧹 [Document Parser] Removed text before first brace")

        # Remove any text after the last }
        end_idx = raw_text.rfind('}')
        if end_idx > 0 and end_idx < len(raw_text) - 1:
            raw_text = raw_text[:end_idx + 1]
            logger.info(f"🧹 [Document Parser] Removed text after last brace")

        # Fix common JSON issues
        sanitized = raw_text

        # Remove trailing commas before closing brackets/braces
        sanitized = re.sub(r',\s*}', '}', sanitized)
        sanitized = re.sub(r',\s*]', ']', sanitized)

        # Fix newlines within strings (common LLM issue)
        sanitized = re.sub(r'"([^"]*)\n([^"]*)"', r'"\1 \2"', sanitized)

        logger.info(f"🧹 [Document Parser] Gentle sanitization complete. Length: {len(raw_text)} -> {len(sanitized)}")
        return sanitized

    def _extract_field_mappings_from_text(self, raw_text: str) -> List[Dict[str, Any]]:
        """Extract field mappings from raw text using regex patterns"""
        import re

        field_mappings = []

        # Look for field mapping patterns in the text
        # Pattern: "field": "value" with confidence
        field_patterns = [
            r'"field":\s*"([^"]+)",\s*"value":\s*"([^"]+)",\s*"confidence":\s*([\d.]+)',
            r'"field":\s*"([^"]+)",\s*"value":\s*"([^"]+)"',
            r'Field:\s*([^\n]+)\s*Value:\s*([^\n]+)\s*Confidence:\s*([\d.]+)',
        ]

        for pattern in field_patterns:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            for match in matches:
                if len(match) == 3:
                    field, value, confidence = match
                    field_mappings.append({
                        "field": field.strip(),
                        "value": value.strip(),
                        "confidence": float(confidence),
                        "source": "regex_extraction",
                        "reasoning": "Extracted via pattern matching",
                        "priority": "medium"
                    })
                elif len(match) == 2:
                    field, value = match
                    field_mappings.append({
                        "field": field.strip(),
                        "value": value.strip(),
                        "confidence": 0.6,
                        "source": "regex_extraction",
                        "reasoning": "Extracted via pattern matching",
                        "priority": "medium"
                    })

        return field_mappings

    def _validate_and_fix_rfq_structure(self, rfq_data: Dict[str, Any]) -> None:
        """Validate and fix RFQ data structure"""
        # Ensure required keys exist
        if "field_mappings" not in rfq_data:
            rfq_data["field_mappings"] = []

        if "confidence" not in rfq_data:
            rfq_data["confidence"] = 0.8

        if "identified_sections" not in rfq_data:
            rfq_data["identified_sections"] = {}

        if "extracted_entities" not in rfq_data:
            rfq_data["extracted_entities"] = {
                "stakeholders": [],
                "industries": [],
                "research_types": [],
                "methodologies": []
            }

        # Validate field mappings structure
        valid_mappings = []
        for mapping in rfq_data.get("field_mappings", []):
            if isinstance(mapping, dict) and "field" in mapping and "value" in mapping:
                # Ensure required fields exist
                if "confidence" not in mapping:
                    mapping["confidence"] = 0.6
                if "source" not in mapping:
                    mapping["source"] = "llm_extraction"
                if "reasoning" not in mapping:
                    mapping["reasoning"] = "Extracted by LLM"
                if "priority" not in mapping:
                    mapping["priority"] = "medium"
                valid_mappings.append(mapping)

        rfq_data["field_mappings"] = valid_mappings
        logger.info(f"✅ [Document Parser] Validated RFQ structure with {len(valid_mappings)} field mappings")

    def _get_fallback_rfq_structure(self, error_message: str) -> Dict[str, Any]:
        """Return fallback RFQ structure when parsing fails"""
        return {
            "confidence": 0.0,
            "identified_sections": {},
            "extracted_entities": {
                "stakeholders": [],
                "industries": [],
                "research_types": [],
                "methodologies": []
            },
            "field_mappings": [],
            "extraction_error": f"RFQ extraction failed: {error_message}"
        }

    async def parse_document_for_rfq(self, docx_content: bytes, filename: str = None, session_id: str = None) -> Dict[str, Any]:
        """Parse DOCX document specifically for RFQ data extraction."""
        logger.info(f"🎯 [Document Parser] Starting RFQ-specific document parsing")

        # Import progress tracker
        from .progress_tracker import get_progress_tracker
        tracker = get_progress_tracker(session_id or "document_parse")

        try:
            # Send initial progress
            progress_data = tracker.get_progress_data("extracting_document")
            await self._send_progress(session_id, "extracting", progress_data["percent"], progress_data["message"])

            # Extract text from DOCX
            logger.info(f"📄 [Document Parser] Extracting text from DOCX")
            document_text = self.extract_text_from_docx(docx_content)

            if not document_text.strip():
                logger.error(f"❌ [Document Parser] No text content found in document")
                await self._send_progress(session_id, "error", 0, "No text content found in document")
                raise DocumentParsingError("No text content found in document")

            logger.info(f"✅ [Document Parser] Text extraction successful, length: {len(document_text)} chars")

            # Send progress update for document processing
            progress_data = tracker.get_progress_data("processing_document")
            await self._send_progress(session_id, "prompting", progress_data["percent"], progress_data["message"])

            # Extract RFQ-specific data
            logger.info(f"🎯 [Document Parser] Extracting RFQ data from text")
            progress_data = tracker.get_progress_data("analyzing_document")
            await self._send_progress(session_id, "llm_processing", progress_data["percent"], progress_data["message"])

            rfq_data = await self.extract_rfq_data(document_text)
            logger.info(f"✅ [Document Parser] RFQ data extraction completed")

            # Send progress for parsing completion
            progress_data = tracker.get_progress_data("parsing_complete")
            await self._send_progress(session_id, "parsing", progress_data["percent"], progress_data["message"])

            # Structure the response for frontend consumption
            result = {
                "document_content": {
                    "raw_text": document_text,
                    "filename": filename,
                    "word_count": len(document_text.split()),
                    "extraction_timestamp": "2024-01-01T00:00:00Z"
                },
                "rfq_analysis": rfq_data,
                "processing_status": "completed",
                "errors": []
            }

            logger.info(f"🎉 [Document Parser] RFQ document parsing completed successfully")
            logger.info(f"📊 [Document Parser] Extraction confidence: {rfq_data.get('confidence', 0)}")
            logger.info(f"📊 [Document Parser] Field mappings found: {len(rfq_data.get('field_mappings', []))}")

            # Send completion progress
            completion_data = tracker.get_completion_data("parsing_complete")
            await self._send_progress(session_id, "completed", completion_data["percent"], completion_data["message"])

            return result

        except DocumentParsingError:
            await self._send_progress(session_id, "error", 0, "Document parsing failed")
            raise
        except Exception as e:
            logger.error(f"❌ [Document Parser] Unexpected error during RFQ document parsing: {str(e)}", exc_info=True)
            await self._send_progress(session_id, "error", 0, f"Unexpected error: {str(e)}")
            raise DocumentParsingError(f"Unexpected error: {str(e)}")

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