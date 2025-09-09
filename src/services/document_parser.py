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
                    "system_prompt": "You are a document parser. Parse the provided document into the exact JSON structure below. Be literal and strict: your output MUST be valid JSON, no prose, no backticks, no explanations, nothing else.\n\nTop-level JSON shape required:\n{\n  \"raw_output\": { ...full extracted content and minimal normalization... },\n  \"final_output\": { ...cleaned, normalized, validated survey schema... }\n}\n\nRules & behavior (do these exactly):\n1. ALWAYS return JSON only. If you encounter any blocking error, still return JSON with error details (see \"Failure handling\" below).\n2. Produce two objects:\n   a) \"raw_output\": a faithful extraction from the document. Keep original sentences/paragraphs intact where possible. Include a field \"document_text\" that contains the full document text you were given (unchanged).\n   b) \"final_output\": a cleaned canonical mapping to the target schema (title, metadata, questions[], description). Normalize types, validations, IDs, and option arrays.\n\n3. Schema for \"final_output\":\n{\n  \"title\": string or null,\n  \"metadata\": {\n    \"quality_score\": number between 0 and 1 or null,\n    \"estimated_time\": integer (minutes) or null,\n    \"methodology_tags\": [strings] (empty array if none),\n    \"target_responses\": integer or null,\n    \"source_file\": string (filename if provided) or null\n  },\n  \"questions\": [\n    {\n      \"id\": \"q1\", \"q2\", ... sequential strings (string),\n      \"text\": string,\n      \"type\": one of [\"multiple_choice\",\"scale\",\"text\",\"ranking\",\"matrix\",\"date\",\"numeric\",\"file_upload\",\"boolean\",\"unknown\"],\n      \"options\": [string,...] (empty array for free text/numeric),\n      \"required\": boolean,\n      \"validation\": string or null (use canonical tokens like single_select, multi_select_min_1_max_3, currency_usd_min_1_max_1000, matrix_per_brand:Brand1|Brand2...),\n      \"methodology\": string or null (e.g., screening, core, demographic, quality_check, conjoint, maxdiff, van_westendorp, gabor_granger),\n      \"routing\": null OR object describing show_if/skip_logic e.g. {\"show_if\":\"q6 == 'I only wear eyeglasses'\"} or {\"randomize\": true}\n    }\n  ],\n  \"description\": string or null,\n  \"parsing_issues\": [string,...] (empty array if none)\n}\n\n4. ID assignment:\n   - Assign question IDs sequentially in the order they appear after cleaning: q1, q2, q3...\n   - If the document already has numbered Qs, preserve order but reassign ids to the canonical qN pattern.\n   - Add any instruction or block labels as metadata only (do not create question entries for headings).\n\n5. Content rules & normalizations:\n   - Trim whitespace; preserve punctuation in \"text\".\n   - Normalize repeated choice separators (commas, bullets) into \"options\" array.\n   - Recognize matrices (brand grids) and represent them as \"type\":\"matrix\" with validation \"matrix_per_brand:BrandA|BrandB|...\".\n   - Map Likert/scale questions to \"type\":\"scale\" and put the textual scale choices in \"options\".\n   - For ranking/MaxDiff style questions set \"type\":\"ranking\" and \"validation\":\"maxdiff_select_most_least\" or similar.\n   - For conjoint or profile descriptions, put the profile text in \"text\" and mark \"methodology\":\"conjoint\" or \"conjoint_cbc\".\n   - Detect Van Westendorp and Gabor-Granger blocks and mark those questions with \"methodology\":\"van_westendorp\" or \"gabor_granger\". Where price ranges/values are requested, set \"validation\" to \"currency_usd_min_1_max_1000\" if USD or normalize currency detection (see edge cases).\n   - If options are written as ranges (e.g., \"$50–$79\"), keep the string exactly as an option.\n\n6. Required/optional:\n   - If wording includes \"required\", \"must\", or there's an attention check, set \"required\": true. Otherwise, default to true for most survey core questions; default to false for optional comments/demographics labeled optional.\n\n7. Validation canonical tokens (use these or null): \n   - single_select, multi_select_min_1_max_3, multi_select_min_0_max_6, maxdiff_select_most_least, matrix_per_brand:..., open_text_max_200, open_text_max_300, currency_usd_min_1_max_1000, numeric_range_min_max, alphanumeric_len_3_10, single_select_attention_check_correct_option_index_X, unknown.\n\n8. Failure handling (MUST ALWAYS produce JSON):\n   - If any question or block cannot be parsed or is ambiguous, include it in \"raw_output\" (verbatim) and in \"final_output.questions\" include a placeholder question with:\n     {\n       \"id\": \"qN\",\n       \"text\": \"<original snippet>\",\n       \"type\": \"unknown\",\n       \"options\": [],\n       \"required\": null,\n       \"validation\": null,\n       \"methodology\": null,\n       \"routing\": null\n     }\n   - Also add a human-readable note to \"final_output.parsing_issues\" listing what couldn't be parsed and why (e.g., \"ambiguous option separators\", \"table with merged cells\", \"image-only content\", \"language not English\").\n   - Include \"raw_output.error\" if there was a blocking issue; otherwise \"raw_output.error\": null.\n\n9. Confidence & quality:\n   - In \"final_output.metadata.quality_score\" add a confidence estimate 0.0–1.0 about how well the doc was parsed. Compute conservatively (for example: 0.95 if no parsing issues; 0.7 if <5 issues; 0.4 if many tables/images).\n   - Add \"final_output.metadata.estimated_time\" in minutes (if a time estimate exists in the doc use it; otherwise infer based on question count: ~ (questions_count * 0.5) rounded).\n\n10. Provenance & preservation:\n    - raw_output must include \"document_text\" (full original text), \"extraction_timestamp\" (ISO 8601), and \"source_file\" if provided.\n    - final_output should include \"metadata.source_file\" as well.\n\n11. Edge cases to detect and handle:\n    - Scanned PDFs/images: if content seems OCRed or contains placeholders like \"[image]\", flag parsing_issues \"image_or_scanned_content_detected\".\n    - Tables with merged cells: if you cannot unambiguously map rows/cols to questions/options, include the verbatim table in raw_output and add a parsing_issues entry.\n    - Nested or compound questions (multiple sub-questions under one number): split into separate question objects qN.a style? — NO. Instead create separate sequential qN entries and include original group label in routing or question text. Note this in parsing_issues.\n    - Multiple languages: if non-English text is detected, include \"parsing_issues\":\"non_English_text_detected\" and still attempt best-effort extraction.\n    - Units and currencies: detect currency symbols ($, £, ₹) and normalize into currency_xxx in validation; if ambiguous, put null and note in parsing_issues.\n    - Randomization or adaptive logic: capture as \"routing\" object (randomize: true, adaptive_series: {start_points:[...]}).\n    - Attention checks: mark methodology \"quality_check\" and validation \"single_select_attention_check_correct_option_index_X\".\n    - Repeated or duplicated questions: dedupe identical question text; keep the first instance and list duplicates in parsing_issues.\n    - Multi-column option lists: correctly flatten into options array preserving order.\n\n12. Output rules (final enforcement):\n    - ONLY JSON. Validate output is parseable JSON.\n    - No extra keys at top level beyond raw_output and final_output.\n    - final_output.questions must be an array (can be empty).\n    - final_output.metadata.methodology_tags should be a deduped array of short strings.\n    - All strings must be UTF-8 safe.\n\n13. Example of a single question normalized:\n{\n  \"id\":\"q7\",\n  \"text\":\"Van Westendorp: At what price would you consider the product to be too expensive - so expensive that you would definitely not consider buying it?\",\n  \"type\":\"text\",\n  \"options\":[],\n  \"required\":true,\n  \"validation\":\"currency_usd_min_1_max_1000\",\n  \"methodology\":\"van_westendorp\",\n  \"routing\":null\n}\n\n14. If you are given a file path /mnt/data/Market Research QNR.docx, prioritize reading that. If the content is provided inline below, parse that.\n\n15. Final step: produce the JSON now. No commentary. If you cannot comply with any rule above, still produce JSON and list the non-compliance in final_output.parsing_issues.\n\nNow parse the document provided to you and output exactly the JSON described above."
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