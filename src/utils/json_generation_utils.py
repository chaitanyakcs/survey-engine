#!/usr/bin/env python3
"""
JSON Generation Utilities
Simplified utilities for consistent JSON generation and parsing using modern json-repair library
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Import json-repair for malformed JSON fixing
try:
    import json_repair
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False
    logger.warning("⚠️ [JSONGenerationUtils] json-repair library not available. Install with: pip install json-repair")


class JSONParseStrategy(Enum):
    """Strategies for parsing JSON from LLM responses"""
    PROVIDER_EXTRACT = "provider_extract"
    JSON_REPAIR = "json_repair"
    DIRECT = "direct"


@dataclass
class JSONParseResult:
    """Result of JSON parsing attempt"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    strategy_used: Optional[JSONParseStrategy] = None
    original_length: int = 0
    cleaned_length: int = 0


class JSONGenerationUtils:
    """
    Centralized utilities for consistent JSON generation and parsing
    Uses modern json-repair library for reliable malformed JSON handling
    """
    
    # Common JSON generation system prompts
    JSON_ONLY_SYSTEM_PROMPT = """You are a JSON generation assistant. Your ONLY job is to return valid JSON.

CRITICAL RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no backticks
2. Start your response with { and end with }
3. Ensure all strings are properly quoted
4. Ensure all commas are in place
5. No trailing commas before } or ]
6. Response must be parseable by json.loads()

Your response will be parsed as JSON. Make sure it's valid."""

    JSON_SCHEMA_SYSTEM_PROMPT_TEMPLATE = """You are a JSON generation assistant. Your ONLY job is to return valid JSON that matches this schema:

{schema}

CRITICAL RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no backticks
2. Start your response with { and end with }
3. Ensure all required fields from the schema are present
4. Ensure all strings are properly quoted
5. Ensure all commas are in place
6. No trailing commas before } or ]
7. Response must be parseable by json.loads()

Your response will be parsed as JSON. Make sure it's valid and matches the schema."""

    @staticmethod
    def create_json_system_prompt(schema: Optional[Dict[str, Any]] = None, purpose: str = "general") -> str:
        """Create a system prompt optimized for JSON generation"""
        if schema:
            return JSONGenerationUtils.JSON_SCHEMA_SYSTEM_PROMPT_TEMPLATE.format(
                schema=json.dumps(schema, indent=2)
            )
        return JSONGenerationUtils.JSON_ONLY_SYSTEM_PROMPT

    @staticmethod
    def get_survey_generation_schema() -> Dict[str, Any]:
        """Get schema for survey generation (higher creativity)"""
        return {
            "type": "object",
            "required": ["title", "description", "sections", "metadata"],
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "title", "questions"],
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "questions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "text", "type"],
                                    "properties": {
                                        "id": {"type": "string"},
                                        "text": {"type": "string"},
                                        "type": {"type": "string"},
                                        "options": {"type": "array", "items": {"type": "string"}},
                                        "required": {"type": "boolean"},
                                        "validation": {"type": "string"},
                                        "methodology": {"type": "string"},
                                        "routing": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "estimated_time": {"type": "integer"},
                        "methodology_tags": {"type": "array", "items": {"type": "string"}},
                        "target_responses": {"type": "integer"}
                    }
                }
            }
        }

    @staticmethod
    def get_rfq_parsing_schema() -> Dict[str, Any]:
        """Get schema for RFQ parsing (structured, precise)"""
        return {
            "type": "object",
            "required": ["raw_output", "final_output"],
            "properties": {
                "raw_output": {
                    "type": "object",
                    "required": ["document_text", "extraction_timestamp", "source_file", "error"],
                    "properties": {
                        "document_text": {"type": "string"},
                        "extraction_timestamp": {"type": "string"},
                        "source_file": {"type": ["string", "null"]},
                        "error": {"type": ["string", "null"]}
                    }
                },
                "final_output": {
                    "type": "object",
                    "required": ["title", "questions"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": ["string", "null"]},
                        "metadata": {"type": "object"},
                        "questions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["id", "text", "type"],
                                "properties": {
                                    "id": {"type": "string"},
                                    "text": {"type": "string"},
                                    "type": {"type": "string"},
                                    "options": {"type": "array", "items": {"type": "string"}},
                                    "required": {"type": "boolean"},
                                    "validation": {"type": "string"},
                                    "methodology": {"type": "string"},
                                    "routing": {"type": "object"}
                                }
                            }
                        },
                        "parsing_issues": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        }

    @staticmethod
    def parse_json_from_response(
        response_content: str, 
        expected_schema: Optional[Dict[str, Any]] = None,
        provider: str = "replicate"
    ) -> JSONParseResult:
        """
        Parse JSON from LLM response using modern json-repair library
        
        Args:
            response_content: Raw response from LLM
            expected_schema: Optional schema to validate against
            provider: Provider type ("replicate" or "openai") for extraction
            
        Returns:
            JSONParseResult with success status and parsed data
        """
        original_length = len(response_content)
        logger.info(f"🔍 [JSONGenerationUtils] Starting JSON parsing, length: {original_length}, provider: {provider}")
        
        # Step 1: Minimal extraction - just get the content string to parse
        content_to_parse = response_content
        
        if provider == "replicate":
            extract_result = JSONGenerationUtils._replicate_extract(response_content)
            if extract_result.success and extract_result.data:
                # If we got a string, use it; if we got a dict, it's already parsed
                if isinstance(extract_result.data, dict):
                    # Already parsed - validate and return if schema passes
                    if expected_schema:
                        validation_result = JSONGenerationUtils._validate_against_schema(extract_result.data, expected_schema)
                        if validation_result.success:
                            return JSONParseResult(
                                success=True,
                                data=extract_result.data,
                                strategy_used=JSONParseStrategy.PROVIDER_EXTRACT,
                                original_length=original_length,
                                cleaned_length=len(json.dumps(extract_result.data))
                            )
                    else:
                        return JSONParseResult(
                            success=True,
                            data=extract_result.data,
                            strategy_used=JSONParseStrategy.PROVIDER_EXTRACT,
                            original_length=original_length,
                            cleaned_length=len(json.dumps(extract_result.data))
                        )
                else:
                    # String - use it for parsing below
                    content_to_parse = str(extract_result.data)
                    logger.info(f"✅ [JSONGenerationUtils] Extracted 'text' field from Replicate wrapper")
        elif provider == "openai":
            extract_result = JSONGenerationUtils._openai_extract(response_content)
            if extract_result.success and extract_result.data:
                # Already parsed dict - validate and return if schema passes
                if isinstance(extract_result.data, dict):
                    if expected_schema:
                        validation_result = JSONGenerationUtils._validate_against_schema(extract_result.data, expected_schema)
                        if validation_result.success:
                            return JSONParseResult(
                                success=True,
                                data=extract_result.data,
                                strategy_used=JSONParseStrategy.PROVIDER_EXTRACT,
                                original_length=original_length,
                                cleaned_length=len(json.dumps(extract_result.data))
                            )
                    else:
                        return JSONParseResult(
                            success=True,
                            data=extract_result.data,
                            strategy_used=JSONParseStrategy.PROVIDER_EXTRACT,
                            original_length=original_length,
                            cleaned_length=len(json.dumps(extract_result.data))
                        )
        
        # Step 2: Try direct parsing (minimal attempt before json-repair)
        try:
            data = json.loads(content_to_parse.strip())
            logger.info(f"✅ [JSONGenerationUtils] Direct JSON parsing succeeded")
            
            # Validate schema if provided
            if expected_schema:
                validation_result = JSONGenerationUtils._validate_against_schema(data, expected_schema)
                if not validation_result.success:
                    logger.warning(f"⚠️ [JSONGenerationUtils] Schema validation failed: {validation_result.error}")
                    # Continue to json-repair even if direct parse worked but schema fails
                else:
                    return JSONParseResult(
                        success=True,
                        data=data,
                        strategy_used=JSONParseStrategy.DIRECT,
                        original_length=original_length,
                        cleaned_length=len(content_to_parse)
                    )
            else:
                return JSONParseResult(
                    success=True,
                    data=data,
                    strategy_used=JSONParseStrategy.DIRECT,
                    original_length=original_length,
                    cleaned_length=len(content_to_parse)
                )
        except json.JSONDecodeError as e:
            logger.debug(f"⚠️ [JSONGenerationUtils] Direct parsing failed: {e}, trying json-repair")
        
        # Step 3: Use json-repair library - let it do the specialized work
        if JSON_REPAIR_AVAILABLE:
            try:
                # json-repair automatically fixes common JSON issues - minimal preprocessing
                repaired_json = json_repair.repair_json(content_to_parse)
                data = json.loads(repaired_json)
                logger.info(f"✅ [JSONGenerationUtils] JSON repair succeeded using json-repair library")
                
                # Validate schema if provided
                if expected_schema:
                    validation_result = JSONGenerationUtils._validate_against_schema(data, expected_schema)
                    if not validation_result.success:
                        logger.warning(f"⚠️ [JSONGenerationUtils] Schema validation failed after repair: {validation_result.error}")
                        return JSONParseResult(
                            success=False,
                            error=f"Schema validation failed: {validation_result.error}",
                            strategy_used=JSONParseStrategy.JSON_REPAIR,
                            original_length=original_length,
                            cleaned_length=len(repaired_json)
                        )
                
                return JSONParseResult(
                    success=True,
                    data=data,
                    strategy_used=JSONParseStrategy.JSON_REPAIR,
                    original_length=original_length,
                    cleaned_length=len(repaired_json)
                )
            except Exception as e:
                logger.error(f"❌ [JSONGenerationUtils] JSON repair failed: {e}")
        else:
            logger.error(f"❌ [JSONGenerationUtils] json-repair library not available")
        
        # All attempts failed
        logger.error(f"❌ [JSONGenerationUtils] All parsing strategies failed")
        return JSONParseResult(
            success=False,
            error="All parsing strategies failed - JSON is too malformed",
            original_length=original_length,
            cleaned_length=0
        )

    @staticmethod
    def _replicate_extract(content: str) -> JSONParseResult:
        """Minimal extraction: just get 'text' field if it exists, let json-repair handle parsing"""
        try:
            logger.debug(f"🔧 [JSONGenerationUtils] Replicate extract on {len(content)} chars")
            
            # Minimal work: try to parse outer JSON to see if it has a 'text' field
            try:
                outer_json = json.loads(content.strip())
                if isinstance(outer_json, dict) and 'text' in outer_json:
                    text_content = outer_json['text']
                    if isinstance(text_content, str):
                        logger.debug(f"✅ [JSONGenerationUtils] Extracted 'text' field ({len(text_content)} chars), passing to json-repair")
                        # Return as string - let json-repair do all the parsing work
                        return JSONParseResult(success=True, data=text_content)
                    elif isinstance(text_content, dict):
                        # Already parsed, return it directly
                        logger.debug(f"✅ [JSONGenerationUtils] 'text' field is already parsed dict")
                        return JSONParseResult(success=True, data=text_content)
            except json.JSONDecodeError:
                # Outer content is not JSON, might be the JSON string directly - let json-repair handle it
                logger.debug(f"⚠️ [JSONGenerationUtils] Outer content not JSON, passing directly to json-repair")
                pass
            
            # If we get here, either no 'text' field or couldn't parse outer JSON
            # Pass the raw content to json-repair - it's specialized for this
            logger.debug(f"⚠️ [JSONGenerationUtils] No 'text' field or outer parse failed, using raw content")
            return JSONParseResult(success=False, error="No 'text' field found or not JSON")
                
        except Exception as e:
            logger.debug(f"⚠️ [JSONGenerationUtils] Replicate extract failed: {e}, will use raw content")
            return JSONParseResult(success=False, error=f"Extract failed: {e}")

    @staticmethod
    def _openai_extract(content: str) -> JSONParseResult:
        """Minimal extraction: OpenAI usually returns JSON directly, let json-repair handle parsing"""
        try:
            logger.debug(f"🔧 [JSONGenerationUtils] OpenAI extract on {len(content)} chars")
            
            # Minimal work: try direct parse first (OpenAI structured outputs are usually valid JSON)
            try:
                data = json.loads(content.strip())
                logger.debug(f"✅ [JSONGenerationUtils] OpenAI content is valid JSON")
                return JSONParseResult(success=True, data=data)
            except json.JSONDecodeError:
                # Not valid JSON, let json-repair handle it - it's specialized for this
                logger.debug(f"⚠️ [JSONGenerationUtils] OpenAI content not valid JSON, passing to json-repair")
                return JSONParseResult(success=False, error="Not valid JSON, will use json-repair")
                
        except Exception as e:
            logger.debug(f"⚠️ [JSONGenerationUtils] OpenAI extract failed: {e}, will use raw content")
            return JSONParseResult(success=False, error=f"Extract failed: {e}")

    @staticmethod
    def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> JSONParseResult:
        """Validate parsed JSON against expected schema"""
        try:
            # Log what we're validating for debugging
            logger.debug(f"🔍 [JSONGenerationUtils] Validating data with keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
            logger.debug(f"🔍 [JSONGenerationUtils] Schema requires: {schema.get('required', [])}")
            
            # Check required fields
            if "required" in schema:
                for field in schema["required"]:
                    if field not in data:
                        logger.error(f"❌ [JSONGenerationUtils] Missing required field '{field}'. Data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        return JSONParseResult(
                            success=False,
                            error=f"Missing required field: {field}"
                        )
            
            # Basic type checking for top-level fields
            if "properties" in schema:
                for field, field_schema in schema["properties"].items():
                    if field in data:
                        expected_type = field_schema.get("type")
                        if expected_type == "array" and not isinstance(data[field], list):
                            return JSONParseResult(
                                success=False,
                                error=f"Field '{field}' must be an array"
                            )
                        elif expected_type == "object" and not isinstance(data[field], dict):
                            return JSONParseResult(
                                success=False,
                                error=f"Field '{field}' must be an object"
                            )
                        elif expected_type == "string" and not isinstance(data[field], str):
                            return JSONParseResult(
                                success=False,
                                error=f"Field '{field}' must be a string"
                            )
            
            return JSONParseResult(success=True, data=data)
        except Exception as e:
            return JSONParseResult(
                success=False,
                error=f"Schema validation error: {e}"
            )

    @staticmethod
    def log_json_parsing_attempt(
        content: str, 
        result: JSONParseResult, 
        service_name: str
    ) -> None:
        """Log JSON parsing attempt for debugging"""
        if result.success:
            logger.info(
                f"✅ [JSONGenerationUtils] {service_name} successfully parsed JSON "
                f"(strategy: {result.strategy_used.value if result.strategy_used else 'unknown'})"
            )
        else:
            logger.error(
                f"❌ [JSONGenerationUtils] {service_name} failed to parse JSON: {result.error}"
            )


def parse_llm_json_response(
    response_content: str,
    service_name: str = "Unknown",
    expected_schema: Optional[Dict[str, Any]] = None,
    provider: str = "replicate"
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to parse LLM JSON response
    
    Args:
        response_content: Raw response from LLM
        service_name: Name of service calling this (for logging)
        expected_schema: Optional schema to validate against
        provider: Provider type ("replicate" or "openai")
        
    Returns:
        Parsed JSON dict or None if parsing failed
    """
    result = JSONGenerationUtils.parse_json_from_response(
        response_content, expected_schema, provider
    )
    
    JSONGenerationUtils.log_json_parsing_attempt(
        response_content, result, service_name
    )
    
    if result.success:
        return result.data
    else:
        logger.error(f"❌ [JSONGenerationUtils] Failed to parse JSON in {service_name}")
        return None


def get_json_optimized_hyperparameters(purpose: str = "general") -> Dict[str, Any]:
    """
    Get hyperparameters optimized for JSON generation
    
    Args:
        purpose: Purpose of generation (general, survey_generation, rfq_parsing)
        
    Returns:
        Dict of hyperparameters optimized for JSON output
    """
    base_params = {
        "temperature": 0.7,  # Lower temperature for more structured output
        "top_p": 0.9,
        "max_tokens": 16000,  # Increased for large surveys
    }
    
    if purpose == "survey_generation":
        return {
            **base_params,
            "temperature": 0.7,  # Balance creativity and structure
        }
    elif purpose == "rfq_parsing":
        return {
            **base_params,
            "temperature": 0.1,  # Lower temperature for precise extraction
            "max_tokens": 4000,
        }
    
    return base_params


# Standalone wrapper functions for backward compatibility
def create_json_system_prompt(schema: Optional[Dict[str, Any]] = None, purpose: str = "general") -> str:
    """Create a system prompt optimized for JSON generation"""
    return JSONGenerationUtils.create_json_system_prompt(schema, purpose)


def get_rfq_parsing_schema() -> Dict[str, Any]:
    """Get schema for RFQ parsing (structured, precise)"""
    return JSONGenerationUtils.get_rfq_parsing_schema()


def get_survey_generation_schema() -> Dict[str, Any]:
    """Get schema for survey generation (higher creativity)"""
    return JSONGenerationUtils.get_survey_generation_schema()
