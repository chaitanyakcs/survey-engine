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
    ESCAPED_JSON_HANDLE = "escaped_json_handle"
    LARGE_JSON_PARSE = "large_json_parse"
    PARTIAL_JSON_RECOVERY = "partial_json_recovery"
    BROKEN_JSON_RECOVERY = "broken_json_recovery"


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
            "max_tokens": 2000,  # Reduced from 8000 for faster processing
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
            elif strategy == JSONParseStrategy.ESCAPED_JSON_HANDLE:
                return JSONGenerationUtils._handle_escaped_json(content)
            elif strategy == JSONParseStrategy.LARGE_JSON_PARSE:
                return JSONGenerationUtils._parse_large_json(content)
            elif strategy == JSONParseStrategy.PARTIAL_JSON_RECOVERY:
                return JSONGenerationUtils._partial_json_recovery(content)
            elif strategy == JSONParseStrategy.BROKEN_JSON_RECOVERY:
                return JSONGenerationUtils._broken_json_recovery(content)
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
            logger.info(f"🔧 [JSONGenerationUtils] Replicate extract on {len(content)} chars")
            
            # Handle Python dictionary string representation from Replicate
            # This handles cases like: "{'json_output': {'description': '...', 'sections': [...]}}"
            
            # First, try to parse as Python dict string representation
            import ast
            parsed_dict = ast.literal_eval(content)
            logger.info(f"🔍 [JSONGenerationUtils] ast.literal_eval succeeded, type: {type(parsed_dict)}")
            
            if isinstance(parsed_dict, dict):
                logger.info(f"🔍 [JSONGenerationUtils] Parsed dict keys: {list(parsed_dict.keys())}")
            
            # Check if it's a Replicate response with 'text' field
            if isinstance(parsed_dict, dict) and 'text' in parsed_dict:
                text_content = parsed_dict['text']
                logger.info(f"🔍 [JSONGenerationUtils] Found 'text' field, type: {type(text_content)}")
                if isinstance(text_content, str) and text_content.strip().startswith('{'):
                    # Apply sanitization to fix common JSON issues
                    sanitized_content = JSONGenerationUtils._gentle_sanitize(text_content.strip())
                    try:
                        # Try to parse the sanitized JSON
                        data = json.loads(sanitized_content)
                        logger.info(f"✅ [JSONGenerationUtils] Parsed text field as JSON")
                        return JSONParseResult(success=True, data=data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ [JSONGenerationUtils] Text field JSON parsing failed: {e}")
                        # Try more aggressive sanitization
                        try:
                            aggressive_sanitized = JSONGenerationUtils._aggressive_sanitize_content(text_content.strip())
                            data = json.loads(aggressive_sanitized)
                            logger.info(f"✅ [JSONGenerationUtils] Parsed text field with aggressive sanitization")
                            return JSONParseResult(success=True, data=data)
                        except json.JSONDecodeError as e2:
                            logger.warning(f"⚠️ [JSONGenerationUtils] Aggressive sanitization also failed: {e2}")
                            # Continue to other strategies
            
            # Check if it's a Replicate response with 'json_output' field
            if isinstance(parsed_dict, dict) and 'json_output' in parsed_dict:
                json_content = parsed_dict['json_output']
                logger.info(f"🔍 [JSONGenerationUtils] Found 'json_output' field, type: {type(json_content)}")
                if isinstance(json_content, dict):
                    # The json_output is already a dictionary, return it directly
                    logger.info(f"✅ [JSONGenerationUtils] Found json_output dict with keys: {list(json_content.keys())}")
                    return JSONParseResult(success=True, data=json_content)
                elif isinstance(json_content, str) and json_content.strip().startswith('{'):
                    # Apply sanitization to fix common JSON issues
                    sanitized_content = JSONGenerationUtils._gentle_sanitize(json_content.strip())
                    # Try to parse the sanitized JSON
                    data = json.loads(sanitized_content)
                    logger.info(f"✅ [JSONGenerationUtils] Parsed json_output string as JSON")
                    return JSONParseResult(success=True, data=data)
                else:
                    # json_output exists but is not a dict or valid JSON string
                    # Try to extract the actual survey data from the response
                    logger.warning(f"⚠️ [JSONGenerationUtils] json_output field found but not in expected format: {type(json_content)}")
                    # Fall through to other strategies
            
            # Enhanced: Check for nested response structures
            # Handle cases where the response might be wrapped in additional layers
            if isinstance(parsed_dict, dict):
                # Look for any field that contains survey-like data
                for key, value in parsed_dict.items():
                    if isinstance(value, dict):
                        # Check if this nested dict has survey structure
                        if any(survey_key in value for survey_key in ['title', 'description', 'sections', 'questions', 'metadata']):
                            logger.info(f"✅ [JSONGenerationUtils] Found survey data in nested field '{key}' with keys: {list(value.keys())}")
                            return JSONParseResult(success=True, data=value)
                
                # Check if the entire parsed_dict looks like survey data
                if any(key in parsed_dict for key in ['title', 'description', 'sections', 'questions', 'metadata']):
                    logger.info(f"✅ [JSONGenerationUtils] Found survey data in root dict with keys: {list(parsed_dict.keys())}")
                    return JSONParseResult(success=True, data=parsed_dict)
            
            logger.warning(f"⚠️ [JSONGenerationUtils] No valid JSON found in Replicate response")
            return JSONParseResult(success=False, error="No valid JSON found in Replicate response")
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError) as e:
            # If ast.literal_eval fails, try alternative approaches
            try:
                # Try to extract JSON from the string using regex patterns
                # Look for patterns like: {'json_output': {...}}
                import re
                
                # Pattern to match Python dict with json_output key
                pattern = r"'json_output':\s*(\{.*?\})"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    # Convert Python dict string to JSON string
                    json_str = json_str.replace("'", '"')  # Replace single quotes with double quotes
                    json_str = json_str.replace('True', 'true')  # Convert Python booleans
                    json_str = json_str.replace('False', 'false')
                    json_str = json_str.replace('None', 'null')
                    
                    # Try to parse the converted JSON
                    data = json.loads(json_str)
                    return JSONParseResult(success=True, data=data)
                
                # If no json_output pattern found, try to extract the main dict content
                # Look for the main dictionary content between the outer braces
                start = content.find('{')
                if start != -1:
                    # Find the matching closing brace
                    brace_count = 0
                    end = start
                    for i in range(start, len(content)):
                        if content[i] == '{':
                            brace_count += 1
                        elif content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    
                    if brace_count == 0:
                        dict_content = content[start:end]
                        # Try to convert Python dict string to JSON
                        dict_content = dict_content.replace("'", '"')
                        dict_content = dict_content.replace('True', 'true')
                        dict_content = dict_content.replace('False', 'false')
                        dict_content = dict_content.replace('None', 'null')
                        
                        data = json.loads(dict_content)
                        return JSONParseResult(success=True, data=data)
                
                return JSONParseResult(success=False, error=f"Replicate extract failed: {e}")
            except Exception as e2:
                return JSONParseResult(success=False, error=f"Replicate extract failed: {e2}")

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
    def _handle_escaped_json(content: str) -> JSONParseResult:
        """Handle JSON with escaped characters and complex formatting"""
        try:
            # First, try to decode common escape sequences
            decoded_content = content
            
            # Handle common escape sequences
            escape_sequences = {
                '\\"': '"',  # Escaped quotes
                '\\n': '\n',  # Newlines
                '\\r': '\r',  # Carriage returns
                '\\t': '\t',  # Tabs
                '\\\\': '\\',  # Backslashes
            }
            
            for escaped, unescaped in escape_sequences.items():
                decoded_content = decoded_content.replace(escaped, unescaped)
            
            # Try to parse the decoded content
            data = json.loads(decoded_content)
            return JSONParseResult(success=True, data=data)
            
        except json.JSONDecodeError as e:
            # If that fails, try more aggressive cleaning
            try:
                # Remove problematic characters that might cause parsing issues
                cleaned = content
                
                # Remove null bytes and control characters (except newlines, tabs, carriage returns)
                cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
                
                # Fix common JSON issues
                cleaned = re.sub(r',\s*}', '}', cleaned)  # Remove trailing commas
                cleaned = re.sub(r',\s*]', ']', cleaned)  # Remove trailing commas in arrays
                
                # Try to find the JSON boundaries more intelligently
                start = cleaned.find('{')
                end = cleaned.rfind('}')
                if start != -1 and end > start:
                    cleaned = cleaned[start:end+1]
                
                data = json.loads(cleaned)
                return JSONParseResult(success=True, data=data)
                
            except json.JSONDecodeError as e2:
                return JSONParseResult(success=False, error=f"Escaped JSON handling failed: {e2}")
        except Exception as e:
            return JSONParseResult(success=False, error=f"Escaped JSON handling exception: {e}")

    @staticmethod
    def _parse_large_json(content: str) -> JSONParseResult:
        """Handle very large JSON responses that might cause memory issues"""
        try:
            # For large JSON, try to parse in chunks or with streaming
            # First, try normal parsing
            data = json.loads(content)
            return JSONParseResult(success=True, data=data)
            
        except json.JSONDecodeError as e:
            # If normal parsing fails, try to identify and fix common large JSON issues
            try:
                # Check if it's a memory issue by looking at content length
                if len(content) > 1000000:  # 1MB threshold
                    logger.warning(f"⚠️ [JSONGenerationUtils] Large JSON detected ({len(content)} chars), using chunked parsing")
                
                # Try to find the main JSON object boundaries
                start = content.find('{')
                if start == -1:
                    return JSONParseResult(success=False, error="No JSON object found")
                
                # Find the matching closing brace
                brace_count = 0
                end = start
                for i in range(start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                
                if brace_count != 0:
                    return JSONParseResult(success=False, error="Unbalanced braces in large JSON")
                
                # Extract the main JSON object
                json_content = content[start:end]
                
                # Apply gentle sanitization
                sanitized = JSONGenerationUtils._gentle_sanitize(json_content)
                data = json.loads(sanitized)
                return JSONParseResult(success=True, data=data)
                
            except json.JSONDecodeError as e2:
                return JSONParseResult(success=False, error=f"Large JSON parsing failed: {e2}")
        except Exception as e:
            return JSONParseResult(success=False, error=f"Large JSON parsing exception: {e}")

    @staticmethod
    def _partial_json_recovery(content: str) -> JSONParseResult:
        """Attempt to recover partial JSON structures and extract survey data"""
        try:
            # This is the most sophisticated recovery method
            # Try to extract survey structure even from malformed JSON
            
            # First, try to find any valid JSON fragments
            json_objects = []
            
            # Look for complete JSON objects within the content
            start = 0
            while start < len(content):
                obj_start = content.find('{', start)
                if obj_start == -1:
                    break
                
                # Try to find the matching closing brace
                brace_count = 0
                obj_end = obj_start
                for i in range(obj_start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            obj_end = i + 1
                            break
                
                if brace_count == 0:
                    # Found a complete object, try to parse it
                    obj_content = content[obj_start:obj_end]
                    try:
                        obj_data = json.loads(obj_content)
                        json_objects.append(obj_data)
                    except json.JSONDecodeError:
                        pass  # Skip invalid objects
                
                start = obj_end + 1
            
            # If we found valid JSON objects, try to merge them or use the largest one
            if json_objects:
                # Find the object with the most survey-like structure
                best_object = None
                best_score = 0
                
                for obj in json_objects:
                    score = 0
                    if isinstance(obj, dict):
                        # Score based on survey-like fields
                        if 'title' in obj:
                            score += 10
                        if 'sections' in obj:
                            score += 20
                        if 'questions' in obj:
                            score += 15
                        if 'metadata' in obj:
                            score += 5
                        
                        # Check for question arrays
                        if 'sections' in obj and isinstance(obj['sections'], list):
                            for section in obj['sections']:
                                if isinstance(section, dict) and 'questions' in section:
                                    score += len(section['questions']) * 2
                        
                        if 'questions' in obj and isinstance(obj['questions'], list):
                            score += len(obj['questions']) * 2
                    
                    if score > best_score:
                        best_score = score
                        best_object = obj
                
                if best_object and best_score > 0:
                    return JSONParseResult(success=True, data=best_object)
            
            # If no valid JSON objects found, try to extract survey data using text patterns
            return JSONParseResult(success=False, error="No recoverable JSON structure found")
            
        except Exception as e:
            return JSONParseResult(success=False, error=f"Partial JSON recovery exception: {e}")

    @staticmethod
    def _broken_json_recovery(content: str) -> JSONParseResult:
        """Attempt to recover from severely broken JSON with scattered text and malformed structure"""
        try:
            logger.info(f"🔧 [JSONGenerationUtils] Attempting broken JSON recovery on {len(content)} characters")
            
            # First, try to extract any complete JSON objects
            json_objects = []
            
            # Look for complete JSON objects within the content
            start = 0
            while start < len(content):
                obj_start = content.find('{', start)
                if obj_start == -1:
                    break
                
                # Try to find the matching closing brace
                brace_count = 0
                obj_end = obj_start
                for i in range(obj_start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            obj_end = i + 1
                            break
                
                if brace_count == 0:
                    # Found a complete object, try to parse it
                    obj_content = content[obj_start:obj_end]
                    try:
                        # Apply aggressive sanitization first
                        sanitized = JSONGenerationUtils._aggressive_sanitize_content(obj_content)
                        obj_data = json.loads(sanitized)
                        json_objects.append(obj_data)
                        logger.info(f"✅ [JSONGenerationUtils] Recovered JSON object with keys: {list(obj_data.keys()) if isinstance(obj_data, dict) else 'not dict'}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"⚠️ [JSONGenerationUtils] Failed to parse object: {e}")
                        # Try to fix common issues and parse again
                        try:
                            # Fix common broken JSON patterns
                            fixed_content = obj_content
                            
                            # Fix missing quotes around keys
                            fixed_content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed_content)
                            
                            # Fix single quotes to double quotes
                            fixed_content = re.sub(r"'([^']*)'", r'"\1"', fixed_content)
                            
                            # Fix Python-style booleans and nulls
                            fixed_content = re.sub(r'\bTrue\b', 'true', fixed_content)
                            fixed_content = re.sub(r'\bFalse\b', 'false', fixed_content)
                            fixed_content = re.sub(r'\bNone\b', 'null', fixed_content)
                            
                            # Fix trailing commas
                            fixed_content = re.sub(r',\s*}', '}', fixed_content)
                            fixed_content = re.sub(r',\s*]', ']', fixed_content)
                            
                            # Try parsing the fixed content
                            obj_data = json.loads(fixed_content)
                            json_objects.append(obj_data)
                            logger.info(f"✅ [JSONGenerationUtils] Fixed and recovered JSON object with keys: {list(obj_data.keys()) if isinstance(obj_data, dict) else 'not dict'}")
                        except json.JSONDecodeError as e2:
                            logger.debug(f"⚠️ [JSONGenerationUtils] Failed to fix object: {e2}")
                
                start = obj_end + 1
            
            # If we found valid JSON objects, try to merge them or use the best one
            if json_objects:
                # Find the object with the most survey-like structure
                best_object = None
                best_score = 0
                
                for obj in json_objects:
                    score = 0
                    if isinstance(obj, dict):
                        # Score based on survey-like fields
                        if 'title' in obj:
                            score += 10
                        if 'sections' in obj:
                            score += 20
                        if 'questions' in obj:
                            score += 15
                        if 'metadata' in obj:
                            score += 5
                        
                        # Check for question arrays
                        if 'sections' in obj and isinstance(obj['sections'], list):
                            for section in obj['sections']:
                                if isinstance(section, dict) and 'questions' in section:
                                    score += len(section['questions']) * 2
                        
                        if 'questions' in obj and isinstance(obj['questions'], list):
                            score += len(obj['questions']) * 2
                    
                    if score > best_score:
                        best_score = score
                        best_object = obj
                
                if best_object and best_score > 0:
                    logger.info(f"✅ [JSONGenerationUtils] Broken JSON recovery succeeded with score {best_score}")
                    return JSONParseResult(success=True, data=best_object)
            
            # If no valid JSON objects found, try to extract survey data using text patterns
            # This is a last resort - try to build a minimal survey structure
            logger.warning(f"⚠️ [JSONGenerationUtils] No complete JSON objects found, attempting text pattern extraction")
            
            # Look for common survey patterns in the text
            survey_data = {}
            
            # Try to extract title
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', content)
            if title_match:
                survey_data['title'] = title_match.group(1)
            
            # Try to extract description
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', content)
            if desc_match:
                survey_data['description'] = desc_match.group(1)
            
            # Try to extract sections count
            sections_match = re.search(r'"sections_count"\s*:\s*(\d+)', content)
            if sections_match:
                survey_data['sections_count'] = int(sections_match.group(1))
            
            # Try to extract methodology tags
            tags_match = re.search(r'"methodology_tags"\s*:\s*\[(.*?)\]', content, re.DOTALL)
            if tags_match:
                tags_text = tags_match.group(1)
                # Extract individual tags
                tag_matches = re.findall(r'"([^"]*)"', tags_text)
                survey_data['methodology_tags'] = tag_matches
            
            if survey_data:
                logger.info(f"✅ [JSONGenerationUtils] Extracted partial survey data: {list(survey_data.keys())}")
                return JSONParseResult(success=True, data=survey_data)
            
            return JSONParseResult(success=False, error="No recoverable JSON structure found in broken content")
            
        except Exception as e:
            return JSONParseResult(success=False, error=f"Broken JSON recovery exception: {e}")

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
            
            # Additional diagnostic information
            logger.error(f"   Character analysis:")
            null_bytes_present = '\x00' in response_content
            logger.error(f"     - Contains null bytes: {null_bytes_present}")
            control_chars_present = any(ord(c) < 32 and c not in '\n\r\t' for c in response_content[:1000])
            logger.error(f"     - Contains control chars: {control_chars_present}")
            starts_with_brace = response_content.strip().startswith('{')
            logger.error(f"     - Starts with {{: {starts_with_brace}")
            ends_with_brace = response_content.strip().endswith('}')
            logger.error(f"     - Ends with }}: {ends_with_brace}")
            contains_sections = 'sections' in response_content.lower()
            logger.error(f"     - Contains sections: {contains_sections}")
            contains_questions = 'questions' in response_content.lower()
            logger.error(f"     - Contains questions: {contains_questions}")
            
            # Check for common issues
            issues = []
            if '\\"' in response_content:
                issues.append("escaped quotes")
            if response_content.count('{') != response_content.count('}'):
                issues.append("unbalanced braces")
            if response_content.count('[') != response_content.count(']'):
                issues.append("unbalanced brackets")
            if ',\\n}' in response_content or ',\\n]' in response_content:
                issues.append("trailing commas")
            
            if issues:
                logger.error(f"   Detected issues: {', '.join(issues)}")
        else:
            # Log success details
            if result.data and isinstance(result.data, dict):
                data_keys = list(result.data.keys())
                logger.info(f"   Parsed data keys: {data_keys}")
                
                # Check for survey structure
                if 'sections' in result.data:
                    sections_count = len(result.data['sections']) if isinstance(result.data['sections'], list) else 0
                    logger.info(f"   Sections found: {sections_count}")
                    
                    if sections_count > 0 and isinstance(result.data['sections'], list):
                        total_questions = 0
                        for section in result.data['sections']:
                            if isinstance(section, dict) and 'questions' in section:
                                questions_count = len(section['questions']) if isinstance(section['questions'], list) else 0
                                total_questions += questions_count
                        logger.info(f"   Total questions found: {total_questions}")
                
                if 'questions' in result.data:
                    questions_count = len(result.data['questions']) if isinstance(result.data['questions'], list) else 0
                    logger.info(f"   Direct questions found: {questions_count}")


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

