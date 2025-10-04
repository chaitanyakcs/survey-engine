#!/usr/bin/env python3
"""
JSON Generation Utilities
Centralized utilities for consistent JSON generation and parsing across all LLM services
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class JSONParseStrategy(Enum):
    """Strategies for parsing JSON from LLM responses"""
    DIRECT = "direct"
    REPLICATE_EXTRACT = "replicate_extract"
    MARKDOWN_EXTRACT = "markdown_extract"
    BOUNDARY_EXTRACT = "boundary_extract"
    SANITIZE_AND_PARSE = "sanitize_and_parse"
    AGGRESSIVE_SANITIZE = "aggressive_sanitize"
    FORCE_REBUILD = "force_rebuild"


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
    """
    
    # Common JSON generation system prompts
    JSON_ONLY_SYSTEM_PROMPT = """You are a JSON generation assistant. Your ONLY job is to return valid JSON.

CRITICAL RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no code blocks
2. Start your response with { and end with }
3. Use proper JSON syntax with double quotes, correct commas, and brackets
4. All string values must be on single lines - no line breaks within strings
5. No trailing commas in objects or arrays
6. Use null for empty values, not undefined or empty strings
7. Ensure all required fields are present and properly formatted

Your response must be parseable by json.loads() without any modification."""

    JSON_SCHEMA_SYSTEM_PROMPT_TEMPLATE = """You are a JSON generation assistant. Your ONLY job is to return valid JSON that matches the specified schema.

CRITICAL RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no code blocks
2. Start your response with { and end with }
3. Use proper JSON syntax with double quotes, correct commas, and brackets
4. All string values must be on single lines - no line breaks within strings
5. No trailing commas in objects or arrays
6. Use null for empty values, not undefined or empty strings
7. Follow the exact schema structure provided below
8. Ensure all required fields are present and properly formatted

REQUIRED SCHEMA:
{schema}

Your response must be parseable by json.loads() without any modification."""

    @staticmethod
    def get_optimal_hyperparameters_for_json(purpose: str = "general") -> Dict[str, Any]:
        """Get optimal hyperparameters for JSON generation based on purpose"""
        base_params = {
            "top_p": 0.9,
            "max_tokens": 8000,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop_sequences": ["```", "```json", "```\n", "\n\n\n"]  # Stop at code blocks or excessive newlines
        }
        
        # Purpose-specific temperature settings
        if purpose in ["survey_generation", "generation"]:
            base_params["temperature"] = 0.7  # Higher creativity for survey generation
        elif purpose in ["rfq_parsing", "document_parsing", "evaluation"]:
            base_params["temperature"] = 0.1  # Lower temperature for structured parsing
        else:
            base_params["temperature"] = 0.1  # Default to low temperature for consistency
            
        return base_params

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
        strategies: Optional[List[JSONParseStrategy]] = None
    ) -> JSONParseResult:
        """
        Parse JSON from LLM response using multiple strategies
        
        Args:
            response_content: Raw response from LLM
            expected_schema: Optional schema to validate against
            strategies: List of strategies to try (defaults to all)
            
        Returns:
            JSONParseResult with success status and parsed data
        """
        if strategies is None:
            strategies = list(JSONParseStrategy)
        
        original_length = len(response_content)
        logger.info(f"🔍 [JSONGenerationUtils] Starting JSON parsing, length: {original_length}")
        
        for strategy in strategies:
            try:
                logger.info(f"🔧 [JSONGenerationUtils] Trying strategy: {strategy.value}")
                result = JSONGenerationUtils._apply_parse_strategy(response_content, strategy)
                
                if result.success:
                    # Validate against schema if provided
                    if expected_schema:
                        validation_result = JSONGenerationUtils._validate_against_schema(
                            result.data, expected_schema
                        )
                        if not validation_result.success:
                            logger.warning(f"⚠️ [JSONGenerationUtils] Schema validation failed: {validation_result.error}")
                            continue
                    
                    logger.info(f"✅ [JSONGenerationUtils] Success with strategy: {strategy.value}")
                    return JSONParseResult(
                        success=True,
                        data=result.data,
                        strategy_used=strategy,
                        original_length=original_length,
                        cleaned_length=len(str(result.data)) if result.data else 0
                    )
                else:
                    logger.debug(f"⚠️ [JSONGenerationUtils] Strategy {strategy.value} failed: {result.error}")
                    
            except Exception as e:
                logger.debug(f"⚠️ [JSONGenerationUtils] Strategy {strategy.value} exception: {e}")
                continue
        
        # All strategies failed
        logger.error(f"❌ [JSONGenerationUtils] All parsing strategies failed")
        return JSONParseResult(
            success=False,
            error="All parsing strategies failed",
            original_length=original_length,
            cleaned_length=0
        )

    @staticmethod
    def _apply_parse_strategy(content: str, strategy: JSONParseStrategy) -> JSONParseResult:
        """Apply a specific parsing strategy"""
        try:
            if strategy == JSONParseStrategy.DIRECT:
                return JSONGenerationUtils._direct_parse(content)
            elif strategy == JSONParseStrategy.MARKDOWN_EXTRACT:
                return JSONGenerationUtils._markdown_extract(content)
            elif strategy == JSONParseStrategy.BOUNDARY_EXTRACT:
                return JSONGenerationUtils._boundary_extract(content)
            elif strategy == JSONParseStrategy.SANITIZE_AND_PARSE:
                return JSONGenerationUtils._sanitize_and_parse(content)
            elif strategy == JSONParseStrategy.AGGRESSIVE_SANITIZE:
                return JSONGenerationUtils._aggressive_sanitize(content)
            elif strategy == JSONParseStrategy.REPLICATE_EXTRACT:
                return JSONGenerationUtils._replicate_extract(content)
            elif strategy == JSONParseStrategy.FORCE_REBUILD:
                return JSONGenerationUtils._force_rebuild(content)
            else:
                return JSONParseResult(success=False, error=f"Unknown strategy: {strategy}")
        except Exception as e:
            return JSONParseResult(success=False, error=str(e))

    @staticmethod
    def _direct_parse(content: str) -> JSONParseResult:
        """Try to parse JSON directly without any modification"""
        try:
            data = json.loads(content.strip())
            return JSONParseResult(success=True, data=data)
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Direct parse failed: {e}")

    @staticmethod
    def _markdown_extract(content: str) -> JSONParseResult:
        """Extract JSON from markdown code blocks"""
        try:
            # Look for JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                extracted_json = json_match.group(1)
                data = json.loads(extracted_json)
                return JSONParseResult(success=True, data=data)
            else:
                return JSONParseResult(success=False, error="No JSON found in markdown blocks")
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Markdown extract failed: {e}")

    @staticmethod
    def _boundary_extract(content: str) -> JSONParseResult:
        """Extract JSON by finding balanced braces"""
        try:
            start = content.find('{')
            if start == -1:
                return JSONParseResult(success=False, error="No opening brace found")
            
            # Find balanced braces
            brace_count = 0
            end = start
            
            for i in range(start, len(content)):
                char = content[i]
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if brace_count != 0:
                return JSONParseResult(success=False, error="Unbalanced braces")
            
            extracted_json = content[start:end]
            data = json.loads(extracted_json)
            return JSONParseResult(success=True, data=data)
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Boundary extract failed: {e}")

    @staticmethod
    def _sanitize_and_parse(content: str) -> JSONParseResult:
        """Apply gentle sanitization and try to parse"""
        try:
            sanitized = JSONGenerationUtils._gentle_sanitize(content)
            data = json.loads(sanitized)
            return JSONParseResult(success=True, data=data)
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Sanitize and parse failed: {e}")

    @staticmethod
    def _aggressive_sanitize(content: str) -> JSONParseResult:
        """Apply aggressive sanitization and try to parse"""
        try:
            sanitized = JSONGenerationUtils._aggressive_sanitize_content(content)
            data = json.loads(sanitized)
            return JSONParseResult(success=True, data=data)
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Aggressive sanitize failed: {e}")

    @staticmethod
    def _replicate_extract(content: str) -> JSONParseResult:
        """Extract JSON from Replicate API response format"""
        try:
            # Try to parse as Python dict string representation
            # This handles cases like: "{'response_id': '...', 'text': '{\"json\": \"content\"}'}"
            import ast
            parsed_dict = ast.literal_eval(content)
            
            # Check if it's a Replicate response with 'text' field
            if isinstance(parsed_dict, dict) and 'text' in parsed_dict:
                text_content = parsed_dict['text']
                if isinstance(text_content, str) and text_content.strip().startswith('{'):
                    # Apply sanitization to fix common JSON issues
                    sanitized_content = JSONGenerationUtils._gentle_sanitize(text_content.strip())
                    # Try to parse the sanitized JSON
                    data = json.loads(sanitized_content)
                    return JSONParseResult(success=True, data=data)
            
            return JSONParseResult(success=False, error="No valid JSON found in Replicate response")
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError) as e:
            return JSONParseResult(success=False, error=f"Replicate extract failed: {e}")

    @staticmethod
    def _force_rebuild(content: str) -> JSONParseResult:
        """Force rebuild JSON from parts (last resort)"""
        try:
            # This is a placeholder for more sophisticated rebuilding logic
            # For now, we'll try to extract key-value pairs and rebuild
            rebuilt = JSONGenerationUtils._rebuild_json_from_parts(content)
            if rebuilt:
                data = json.loads(rebuilt)
                return JSONParseResult(success=True, data=data)
            else:
                return JSONParseResult(success=False, error="Force rebuild failed")
        except json.JSONDecodeError as e:
            return JSONParseResult(success=False, error=f"Force rebuild failed: {e}")

    @staticmethod
    def _gentle_sanitize(content: str) -> str:
        """Apply gentle sanitization to fix common JSON issues"""
        sanitized = content.strip()
        
        # Remove any leading/trailing non-JSON text
        start = sanitized.find('{')
        end = sanitized.rfind('}') + 1
        if start != -1 and end > start:
            sanitized = sanitized[start:end]
        
        # Fix common JSON syntax issues
        # Remove trailing commas
        sanitized = re.sub(r',\s*}', '}', sanitized)
        sanitized = re.sub(r',\s*]', ']', sanitized)
        
        # Fix missing commas between objects/arrays
        sanitized = re.sub(r'}\s*{', '}, {', sanitized)
        sanitized = re.sub(r']\s*\[', '], [', sanitized)
        sanitized = re.sub(r'}\s*\[', '}, [', sanitized)
        sanitized = re.sub(r']\s*{', '], {', sanitized)
        
        # Fix extra quotes after numbers (common LLM error)
        # Only fix quotes after numbers that are property values (not keys)
        # Look for pattern: "property": number" -> "property": number
        sanitized = re.sub(r':\s*(\d+)"\s*}', r': \1}', sanitized)
        sanitized = re.sub(r':\s*(\d+)"\s*,', r': \1,', sanitized)
        sanitized = re.sub(r':\s*(\d+)"\s*$', r': \1', sanitized)
        
        # Fix missing quotes around string values
        sanitized = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', sanitized)
        
        return sanitized

    @staticmethod
    def _aggressive_sanitize_content(content: str) -> str:
        """Apply aggressive sanitization to fix more complex JSON issues"""
        # Start with gentle sanitization
        sanitized = JSONGenerationUtils._gentle_sanitize(content)
        
        # Remove control characters except newlines, tabs, and carriage returns
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        # Fix common issues with quotes
        sanitized = re.sub(r"'([^']*)'", r'"\1"', sanitized)  # Single quotes to double quotes
        sanitized = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', sanitized)  # Unquoted keys
        
        # Fix boolean values
        sanitized = re.sub(r'\bTrue\b', 'true', sanitized)
        sanitized = re.sub(r'\bFalse\b', 'false', sanitized)
        sanitized = re.sub(r'\bNone\b', 'null', sanitized)
        
        return sanitized

    @staticmethod
    def _rebuild_json_from_parts(content: str) -> Optional[str]:
        """Rebuild JSON from parts (placeholder for more sophisticated logic)"""
        # This is a simplified version - in practice, you might want more sophisticated rebuilding
        try:
            # Try to extract key-value pairs and rebuild
            # This is a basic implementation - could be enhanced
            return None  # Placeholder
        except Exception:
            return None

    @staticmethod
    def _validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> JSONParseResult:
        """Validate parsed data against expected schema"""
        try:
            # Basic schema validation - could be enhanced with jsonschema library
            if not isinstance(data, dict):
                return JSONParseResult(success=False, error="Data is not a dictionary")
            
            # Check required fields
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in data:
                    return JSONParseResult(success=False, error=f"Missing required field: {field}")
            
            return JSONParseResult(success=True, data=data)
        except Exception as e:
            return JSONParseResult(success=False, error=f"Schema validation failed: {e}")

    @staticmethod
    def create_fallback_json(error_message: str, context: str = "") -> Dict[str, Any]:
        """Create a fallback JSON structure when all parsing fails"""
        return {
            "error": True,
            "message": f"JSON parsing failed: {error_message}",
            "context": context,
            "fallback": True,
            "data": None
        }

    @staticmethod
    def log_json_parsing_attempt(
        response_content: str, 
        result: JSONParseResult, 
        service_name: str = "Unknown"
    ) -> None:
        """Log detailed information about JSON parsing attempt"""
        logger.info(f"📊 [JSONGenerationUtils] {service_name} JSON parsing result:")
        logger.info(f"   Success: {result.success}")
        logger.info(f"   Strategy: {result.strategy_used.value if result.strategy_used else 'None'}")
        logger.info(f"   Original length: {result.original_length}")
        logger.info(f"   Cleaned length: {result.cleaned_length}")
        
        if not result.success:
            logger.error(f"   Error: {result.error}")
            logger.error(f"   Response preview: {response_content[:200]}...")
            logger.error(f"   Response ending: ...{response_content[-200:]}")


# Convenience functions for easy integration
def parse_llm_json_response(
    response_content: str, 
    expected_schema: Optional[Dict[str, Any]] = None,
    service_name: str = "Unknown"
) -> Union[Dict[str, Any], None]:
    """
    Parse JSON from LLM response with comprehensive error handling
    
    Args:
        response_content: Raw response from LLM
        expected_schema: Optional schema to validate against
        service_name: Name of the service for logging
        
    Returns:
        Parsed JSON data or None if parsing failed
    """
    result = JSONGenerationUtils.parse_json_from_response(
        response_content, expected_schema
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
    """Get hyperparameters optimized for JSON generation based on purpose"""
    return JSONGenerationUtils.get_optimal_hyperparameters_for_json(purpose)


def create_json_system_prompt(schema: Optional[Dict[str, Any]] = None, purpose: str = "general") -> str:
    """Create a system prompt optimized for JSON generation"""
    return JSONGenerationUtils.create_json_system_prompt(schema, purpose)


def get_survey_generation_schema() -> Dict[str, Any]:
    """Get schema for survey generation (higher creativity)"""
    return JSONGenerationUtils.get_survey_generation_schema()


def get_rfq_parsing_schema() -> Dict[str, Any]:
    """Get schema for RFQ parsing (structured, precise)"""
    return JSONGenerationUtils.get_rfq_parsing_schema()

