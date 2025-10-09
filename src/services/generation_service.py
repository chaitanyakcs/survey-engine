from typing import Dict, List, Any, Optional
from src.config import settings
from src.services.prompt_service import PromptService
import logging

logger = logging.getLogger(__name__)
from src.utils.error_messages import UserFriendlyError, get_api_configuration_error
from src.utils.survey_utils import get_questions_count
from sqlalchemy.orm import Session
import replicate
import json
import logging
import uuid
import time
import re
import asyncio
import os

from src.utils.llm_audit_decorator import audit_llm_call, LLMAuditContext
from src.services.llm_audit_service import LLMAuditService
from src.services.progress_tracker import get_progress_tracker
from src.utils.json_generation_utils import parse_llm_json_response, get_json_optimized_hyperparameters, create_json_system_prompt, get_survey_generation_schema

logger = logging.getLogger(__name__)


class SurveyGenerationError(UserFriendlyError):
    """Exception raised when survey generation fails"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            message=message,
            technical_details=f"Error Code: {error_code}" if error_code else None,
            action_required=details.get("suggestion") if details else None
        )


class GenerationService:
    def __init__(self, db_session: Optional[Session] = None, workflow_id: Optional[str] = None, connection_manager=None) -> None:
        logger.info(f"🚀 [GenerationService] Starting initialization...")
        logger.info(f"🚀 [GenerationService] Database session provided: {bool(db_session)}")
        logger.info(f"🚀 [GenerationService] Config generation_model: {settings.generation_model}")

        self.db_session = db_session  # Store the database session
        self.workflow_id = workflow_id
        self.connection_manager = connection_manager

        # Initialize WebSocket client for progress updates
        if connection_manager and workflow_id:
            from src.services.websocket_client import WebSocketNotificationService
            self.ws_client = WebSocketNotificationService(connection_manager)
        else:
            self.ws_client = None
        # Get model from database settings if available, otherwise fallback to config
        self.model = self._get_generation_model()

        logger.info(f"🔧 [GenerationService] Model selected: {self.model}")
        logger.info(f"🔧 [GenerationService] Model type: {type(self.model)}")

        self.prompt_service = PromptService(db_session=db_session)

        logger.info(f"🔧 [GenerationService] Initializing with model: {self.model}")
        logger.info(f"🔧 [GenerationService] Replicate API token configured: {bool(settings.replicate_api_token)}")
        logger.info(f"🔧 [GenerationService] Replicate API token length: {len(settings.replicate_api_token) if settings.replicate_api_token else 0}")
        if settings.replicate_api_token:
            logger.info(f"🔧 [GenerationService] Replicate API token preview: {settings.replicate_api_token[:8]}...")

        # Check if we have the required API token
        if not settings.replicate_api_token:
            logger.warning("⚠️ [GenerationService] No Replicate API token configured. Survey generation will fail.")
            logger.warning(f"⚠️ [GenerationService] Model '{self.model}' requires Replicate API token")
        else:
            logger.info("✅ [GenerationService] Replicate API token is configured")

        # Initialize Replicate client with proper authentication
        self.replicate_client = replicate.Client(api_token=settings.replicate_api_token)

    def _get_generation_model(self) -> str:
        """Get generation model from database settings or fallback to config"""
        try:
            logger.info(f"🔍 [GenerationService] Starting model selection process...")
            logger.info(f"🔍 [GenerationService] Database session available: {bool(self.db_session)}")
            logger.info(f"🔍 [GenerationService] Config default model: {settings.generation_model}")

            if self.db_session:
                from src.services.settings_service import SettingsService
                settings_service = SettingsService(self.db_session)
                evaluation_settings = settings_service.get_evaluation_settings()

                logger.info(f"🔍 [GenerationService] Database evaluation settings: {evaluation_settings}")

                if evaluation_settings and 'generation_model' in evaluation_settings:
                    model = evaluation_settings['generation_model']
                    logger.info(f"🔧 [GenerationService] Using model from database settings: {model}")
                    logger.info(f"🔧 [GenerationService] Model source: DATABASE")
                    return model
                else:
                    logger.info(f"🔧 [GenerationService] No database settings found, using config default: {settings.generation_model}")
                    logger.info(f"🔧 [GenerationService] Model source: CONFIG_FALLBACK")
                    return settings.generation_model
            else:
                logger.info(f"🔧 [GenerationService] No database session, using config default: {settings.generation_model}")
                logger.info(f"🔧 [GenerationService] Model source: CONFIG_NO_DB")
                return settings.generation_model
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Failed to get model from database settings: {e}, using config default")
            logger.info(f"🔧 [GenerationService] Model source: CONFIG_EXCEPTION")
            return settings.generation_model

    async def generate_survey_with_custom_prompt(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Dict[str, Any] = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Generate survey using a custom system prompt (e.g., from human review edits)
        """
        try:
            logger.info("🚀 [GenerationService] Starting survey generation with custom prompt...")
            logger.info(f"📊 [GenerationService] Input context keys: {list(context.keys()) if context else 'None'}")
            logger.info(f"📊 [GenerationService] Golden examples: {len(golden_examples) if golden_examples else 0}")
            logger.info(f"📊 [GenerationService] Methodology blocks: {len(methodology_blocks) if methodology_blocks else 0}")
            logger.info(f"📊 [GenerationService] Custom rules: {len(custom_rules.get('rules', [])) if custom_rules else 0}")
            logger.info(f"📝 [GenerationService] Custom system prompt length: {len(system_prompt) if system_prompt else 0}")

            # Check if API token is configured
            logger.info(f"🔑 [GenerationService] Checking API token configuration...")
            logger.info(f"🔑 [GenerationService] Replicate API token present: {bool(settings.replicate_api_token)}")
            logger.info(f"🔑 [GenerationService] Replicate API token length: {len(settings.replicate_api_token) if settings.replicate_api_token else 0}")
            if settings.replicate_api_token:
                logger.info(f"🔑 [GenerationService] Replicate API token preview: {settings.replicate_api_token[:8]}...")

            # Check if we have a valid API token for the configured model
            if not settings.replicate_api_token:
                logger.error("❌ [GenerationService] No Replicate API token configured!")
                logger.error(f"❌ [GenerationService] Model '{self.model}' requires Replicate API token")
                error_info = get_api_configuration_error()
                raise UserFriendlyError(
                    message=error_info["message"],
                    technical_details="REPLICATE_API_TOKEN environment variable is not set",
                    action_required="Configure AI service provider (Replicate or OpenAI)"
                )

            logger.info("✅ [GenerationService] API token validation passed")

            # Use the custom system prompt instead of generating a new one
            if system_prompt:
                logger.info("📝 [GenerationService] Using custom system prompt from human review")
                prompt = system_prompt
            else:
                logger.info("🔨 [GenerationService] Building default prompt...")
                prompt = self.prompt_service.build_golden_enhanced_prompt(
                    context=context,
                    golden_examples=golden_examples,
                    methodology_blocks=methodology_blocks,
                    custom_rules=custom_rules
                )

            logger.info(f"🤖 [GenerationService] Generating survey with model: {self.model}")
            logger.info(f"📝 [GenerationService] Prompt length: {len(prompt)} characters")

            # Create audit context for this LLM interaction
            interaction_id = f"survey_generation_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session)

            # Log basic context info
            logger.info(f"🔍 [GenerationService] Context keys: {list(context.keys()) if context else 'None'}")

            async with LLMAuditContext(
                audit_service=audit_service,
                interaction_id=interaction_id,
                model_name=self.model,
                model_provider="replicate",
                purpose="survey_generation",
                input_prompt=prompt,
                context_type="generation",
                parent_workflow_id=context.get('workflow_id'),
                parent_survey_id=context.get('audit_survey_id'),
                parent_rfq_id=context.get('rfq_id'),
                hyperparameters=get_json_optimized_hyperparameters("survey_generation"),
                metadata={
                    'golden_examples_count': len(golden_examples) if golden_examples else 0,
                    'methodology_blocks_count': len(methodology_blocks) if methodology_blocks else 0,
                    'custom_rules_count': len(custom_rules.get('rules', [])) if custom_rules else 0,
                    'context_keys': list(context.keys()) if context else [],
                    'custom_prompt_used': bool(system_prompt)
                },
                tags=["survey", "generation", "replicate", "custom_prompt"]
            ) as audit_context:
                try:
                    # Use streaming generation with custom prompt
                    generation_result = await self._generate_survey_with_streaming(prompt, system_prompt)

                    # Extract metadata for audit context
                    response_time_ms = generation_result["generation_metadata"]["response_time_ms"]
                    survey_data = generation_result["survey"]
                    output_text = json.dumps(survey_data, indent=2)
                    raw_response = generation_result["generation_metadata"].get("raw_response", "")

                    # Set raw response first
                    if raw_response:
                        audit_context.set_raw_response(raw_response)
                    
                    audit_context.set_output(
                        output_content=output_text,
                        input_tokens=len(prompt.split()) if prompt else 0,
                        output_tokens=len(output_text.split()) if output_text else 0
                    )

                    logger.info(f"✅ [GenerationService] Survey generation completed in {response_time_ms}ms")
                    logger.info(f"📊 [GenerationService] Output length: {len(output_text)} characters")

                    # Survey is already parsed in streaming method
                    return {
                        "survey": survey_data,
                        "generation_metadata": {
                            "model": self.model,
                            "response_time_ms": response_time_ms,
                            "custom_prompt_used": bool(system_prompt),
                            "prompt_length": len(prompt),
                            "streaming_enabled": generation_result["generation_metadata"].get("streaming_enabled", False)
                        }
                    }

                except Exception as api_error:
                    logger.error(f"❌ [GenerationService] API call failed: {str(api_error)}")
                    audit_context.set_output(
                        output_content=""
                    )
                    raise UserFriendlyError(
                        message="Survey generation failed due to AI service error",
                        technical_details=str(api_error),
                        action_required="Please try again or contact support if the issue persists"
                    )

        except UserFriendlyError:
            raise
        except Exception as e:
            logger.error(f"❌ [GenerationService] Unexpected error in survey generation: {str(e)}")
            raise UserFriendlyError(
                message="Survey generation failed due to an unexpected error",
                technical_details=str(e),
                action_required="Please try again or contact support if the issue persists"
            )

    async def generate_survey(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]],
        custom_rules: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate survey using GPT with rules-based prompts and golden examples
        """
        try:
            logger.info("🚀 [GenerationService] Starting survey generation...")
            logger.info(f"📊 [GenerationService] Input context keys: {list(context.keys()) if context else 'None'}")
            logger.info(f"📊 [GenerationService] Golden examples: {len(golden_examples) if golden_examples else 0}")
            logger.info(f"📊 [GenerationService] Methodology blocks: {len(methodology_blocks) if methodology_blocks else 0}")
            logger.info(f"📊 [GenerationService] Custom rules: {len(custom_rules.get('rules', [])) if custom_rules else 0}")

            # Check if API token is configured
            logger.info(f"🔑 [GenerationService] Checking API token configuration...")
            logger.info(f"🔑 [GenerationService] Replicate API token present: {bool(settings.replicate_api_token)}")
            logger.info(f"🔑 [GenerationService] Replicate API token length: {len(settings.replicate_api_token) if settings.replicate_api_token else 0}")
            if settings.replicate_api_token:
                logger.info(f"🔑 [GenerationService] Replicate API token preview: {settings.replicate_api_token[:8]}...")

            # Check if we have a valid API token for the configured model
            if not settings.replicate_api_token:
                logger.error("❌ [GenerationService] No Replicate API token configured!")
                logger.error(f"❌ [GenerationService] Model '{self.model}' requires Replicate API token")
                error_info = get_api_configuration_error()
                raise UserFriendlyError(
                    message=error_info["message"],
                    technical_details="REPLICATE_API_TOKEN environment variable is not set",
                    action_required="Configure AI service provider (Replicate or OpenAI)"
                )

            logger.info("✅ [GenerationService] API token validation passed")

            # Build comprehensive prompt with rules and golden examples
            logger.info("🔨 [GenerationService] Building prompt...")
            prompt = self.prompt_service.build_golden_enhanced_prompt(
                context=context,
                golden_examples=golden_examples,
                methodology_blocks=methodology_blocks,
                custom_rules=custom_rules
            )

            logger.info(f"🤖 [GenerationService] Generating survey with model: {self.model}")
            logger.info(f"📝 [GenerationService] Prompt length: {len(prompt)} characters")

            # System prompt is now automatically logged via LLMAuditContext decorator

            logger.info("🌐 [GenerationService] Making API call to Replicate...")
            logger.info(f"🌐 [GenerationService] Model: {self.model}")
            logger.info(f"🌐 [GenerationService] Replicate client available: {bool(self.replicate_client)}")

            # Create audit context for this LLM interaction
            interaction_id = f"survey_generation_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session)

            logger.info(f"🔍 [GenerationService] Context keys: {list(context.keys()) if context else 'None'}")

            async with LLMAuditContext(
                audit_service=audit_service,
                interaction_id=interaction_id,
                model_name=self.model,
                model_provider="replicate",
                purpose="survey_generation",
                input_prompt=prompt,
                context_type="generation",
                parent_workflow_id=context.get('workflow_id'),
                parent_survey_id=context.get('audit_survey_id'),
                parent_rfq_id=context.get('rfq_id'),
                hyperparameters=get_json_optimized_hyperparameters("survey_generation"),
                metadata={
                    'golden_examples_count': len(golden_examples) if golden_examples else 0,
                    'methodology_blocks_count': len(methodology_blocks) if methodology_blocks else 0,
                    'custom_rules_count': len(custom_rules.get('rules', [])) if custom_rules else 0,
                    'context_keys': list(context.keys()) if context else []
                },
                tags=["survey", "generation", "replicate"]
            ) as audit_context:
                try:
                    # Use streaming generation instead of sync call
                    generation_result = await self._generate_survey_with_streaming(prompt)

                    # Extract metadata for audit context
                    response_time_ms = generation_result["generation_metadata"]["response_time_ms"]
                    survey_data = generation_result["survey"]
                    output_content = json.dumps(survey_data, indent=2)
                    raw_response = generation_result["generation_metadata"].get("raw_response", "")

                    # Set raw response first
                    if raw_response:
                        audit_context.set_raw_response(raw_response)

                    # Set output and metrics in audit context
                    audit_context.set_output(
                        output_content=output_content,
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=len(output_content.split()),  # Rough estimate
                        cost_usd=None  # Replicate doesn't provide cost info in response
                    )

                except Exception as api_error:
                    logger.error(f"❌ [GenerationService] API call failed: {str(api_error)}")
                    logger.error(f"❌ [GenerationService] API error type: {type(api_error)}")

                    # Check if it's an authentication error
                    if "authentication" in str(api_error).lower() or "unauthorized" in str(api_error).lower():
                        error_info = get_api_configuration_error()
                        raise UserFriendlyError(
                            message=error_info["message"],
                            technical_details=str(api_error),
                            action_required="Configure AI service provider (Replicate or OpenAI)"
                        )
                    else:
                        raise Exception(f"API call failed: {str(api_error)}")

                logger.info(f"✅ [GenerationService] Streaming generation completed successfully")
                logger.info(f"📊 [GenerationService] Generation metadata: {generation_result['generation_metadata']}")

                # Return the already processed survey data
                return {
                    "survey": survey_data
                }

        except UserFriendlyError as e:
            logger.error(f"❌ [GenerationService] UserFriendlyError: {e.message}")
            # Re-raise user-friendly errors as-is
            raise
        except Exception as e:
            logger.error(f"❌ [GenerationService] Survey generation failed: {str(e)}", exc_info=True)
            # Check if it's an API token related error
            if "api" in str(e).lower() and "token" in str(e).lower():
                logger.error("❌ [GenerationService] API token related error detected")
                error_info = get_api_configuration_error()
                raise UserFriendlyError(
                    message=error_info["message"],
                    technical_details=str(e),
                    action_required="Configure AI service provider (Replicate or OpenAI)"
                )
            else:
                logger.error(f"❌ [GenerationService] Generic error: {str(e)}")
                raise Exception(f"Survey generation failed: {str(e)}")


    def _smart_normalize_whitespace(self, json_text: str) -> str:
        """
        Smart JSON whitespace normalization that preserves string content
        while fixing structural whitespace issues.
        """
        def fix_structural_whitespace(text):
            result = []
            in_string = False
            escape_next = False

            for i, char in enumerate(text):
                if escape_next:
                    result.append(char)
                    escape_next = False
                    continue

                if char == '\\' and in_string:
                    result.append(char)
                    escape_next = True
                    continue

                if char == '"':
                    in_string = not in_string
                    result.append(char)
                    continue

                if in_string:
                    # Inside strings: preserve all characters including whitespace
                    result.append(char)
                else:
                    # Outside strings: normalize whitespace and add proper spacing
                    if char.isspace():
                        # Only add space if needed for structural separation
                        if result and not result[-1].isspace():
                            # Check if we need a space based on context
                            prev_char = result[-1] if result else ''
                            next_char = text[i + 1] if i + 1 < len(text) else ''

                            # Add space around structural elements but not inside values
                            if (prev_char in ',:' or next_char in ',:{}[]') and prev_char not in '{}[]':
                                result.append(' ')
                    else:
                        result.append(char)

            return ''.join(result)

        # Apply the structural whitespace fix
        normalized = fix_structural_whitespace(json_text)

        # Final cleanup: ensure proper spacing around structural elements
        import re
        # Add space after colons and commas if not already present
        normalized = re.sub(r'(:)([^\s])', r'\1 \2', normalized)
        normalized = re.sub(r'(,)([^\s\]}])', r'\1 \2', normalized)

        # Remove extra spaces around brackets and braces
        normalized = re.sub(r'\s*([{}[\]])\s*', r'\1', normalized)

        return normalized

    def _sanitize_raw_output(self, response_text: str) -> str:
        """
        Smart JSON sanitization that preserves string content while fixing structure.
        Fixed to handle malformed JSON without adding extra closing braces.
        """
        import re

        logger.info("🧹 [GenerationService] Starting Smart JSON sanitization...")
        logger.info(f"🔍 [GenerationService] Input length: {len(response_text)}")

        # Performance optimization: Skip processing if response is too large
        if len(response_text) > 50000:
            logger.warning(f"⚠️ [GenerationService] Response too large ({len(response_text)} chars), using minimal processing")
            # Minimal processing for very large responses to prevent hanging
            sanitized = response_text.replace('\n', ' ').replace('\r', ' ')
            sanitized = re.sub(r'\s+', ' ', sanitized)
            # Find JSON boundaries quickly
            start = sanitized.find('{')
            end = sanitized.rfind('}')
            if start >= 0 and end > start:
                sanitized = sanitized[start:end + 1]
        else:
            # Normal processing for reasonable-sized responses
            # Remove markdown code blocks
            sanitized = re.sub(r'^.*?```(?:json)?\s*', '', response_text, flags=re.DOTALL)
            sanitized = re.sub(r'```.*$', '', sanitized, flags=re.DOTALL)

            # Remove any leading text before the first {
            sanitized = re.sub(r'^[^{]*', '', sanitized)

            # Fix trailing text - find last } and trim properly (don't add extra braces!)
            last_brace_pos = sanitized.rfind('}')
            if last_brace_pos >= 0:
                sanitized = sanitized[:last_brace_pos + 1]

        # AGGRESSIVE control character and newline removal for malformed LLM JSON
        # First pass: Remove ALL control characters including embedded newlines
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # Second pass: Remove problematic newlines that break JSON structure
        # Replace sequences like: {\n\n \n " with: {"
        sanitized = re.sub(r'\{\s*\n\s*\n\s*\n?\s*"', '{"', sanitized)
        sanitized = re.sub(r'"\s*\n\s*\n?\s*:', '":', sanitized)
        sanitized = re.sub(r':\s*\n\s*\n?\s*"', ':"', sanitized)
        sanitized = re.sub(r'",\s*\n\s*\n?\s*"', '","', sanitized)

        # Third pass: Normalize any remaining structural whitespace
        sanitized = re.sub(r'\s*\n\s*', ' ', sanitized)  # Replace newlines with single spaces
        sanitized = re.sub(r'\s{2,}', ' ', sanitized)    # Collapse multiple spaces

        # Smart whitespace normalization that preserves string content
        # Performance optimization: Use simpler normalization for large responses
        if len(sanitized) > 15000:
            logger.warning(f"⚠️ [GenerationService] Large response ({len(sanitized)} chars), using fast normalization")
            # Fast normalization for large responses to prevent hanging
            sanitized = re.sub(r'\s+', ' ', sanitized)  # Collapse all whitespace to single spaces
            sanitized = re.sub(r'\s*([{}[\]:,])\s*', r'\1', sanitized)  # Remove spaces around JSON syntax
            sanitized = re.sub(r'([{}[\],])\s*(["}])', r'\1\2', sanitized)  # Remove spaces between JSON elements
        else:
            # Use detailed smart normalization for smaller responses
            sanitized = self._smart_normalize_whitespace(sanitized)

        # Fix missing commas between objects/arrays (critical for corrupted format)
        sanitized = re.sub(r'}\s*{', '}, {', sanitized)
        sanitized = re.sub(r']\s*\[', '], [', sanitized)
        sanitized = re.sub(r'}\s*\[', '}, [', sanitized)
        sanitized = re.sub(r']\s*{', '], {', sanitized)

        # Fix quote escaping issues in corrupted format
        # The corrupted format has quotes separated by newlines that need to be properly escaped
        # This is a more targeted fix for the specific corruption pattern we're seeing
        sanitized = re.sub(r'"([^"]*)"([^":,}\]]*)"([^":,}\]]*)"', r'"\1\2\3"', sanitized)
        
        # Remove trailing commas
        sanitized = re.sub(r',\s*}', '}', sanitized)
        sanitized = re.sub(r',\s*]', ']', sanitized)

        logger.info(f"🧹 [GenerationService] Smart sanitization complete. Length: {len(response_text)} -> {len(sanitized)}")
        logger.info(f"🔍 [GenerationService] Sanitized text: {sanitized[:200]}...")

        return sanitized

    def _gentle_sanitize_json(self, raw_text: str) -> str:
        """
        Gentle JSON sanitization that fixes control characters and obvious issues without corrupting valid JSON.
        """
        import re

        logger.info("🧹 [GenerationService] Starting gentle JSON sanitization...")

        # CRITICAL FIX: Remove invalid control characters first
        # Remove all control characters except \n, \t, \r which are handled later
        control_chars_pattern = r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'
        sanitized = re.sub(control_chars_pattern, '', raw_text)
        logger.info(f"🧹 [GenerationService] Removed control characters. Length: {len(raw_text)} -> {len(sanitized)}")

        # Only remove markdown code blocks if present
        sanitized = re.sub(r'^.*?```(?:json)?\s*', '', sanitized, flags=re.DOTALL)
        sanitized = re.sub(r'```.*$', '', sanitized, flags=re.DOTALL)

        # Remove any leading text before the first {
        sanitized = re.sub(r'^[^{]*', '', sanitized)

        # Find last } and trim properly
        last_brace_pos = sanitized.rfind('}')
        if last_brace_pos >= 0:
            sanitized = sanitized[:last_brace_pos + 1]

        # Fix control characters and newlines within JSON strings
        # Replace problematic newlines, tabs, carriage returns within quoted strings
        def clean_string_content(match):
            content = match.group(1)
            # Replace control characters with spaces
            content = re.sub(r'[\t\r\n]+', ' ', content)
            # Collapse multiple spaces
            content = re.sub(r'\s+', ' ', content)
            # Fix spacing issues: remove spaces before punctuation
            content = re.sub(r'\s+([,\.;:!?])', r'\1', content)
            return f'"{content.strip()}"'

        # Apply to quoted strings
        sanitized = re.sub(r'"([^"]*)"', clean_string_content, sanitized)

        # Only fix obvious JSON issues:
        # 1. Remove trailing commas
        sanitized = re.sub(r',\s*}', '}', sanitized)
        sanitized = re.sub(r',\s*]', ']', sanitized)

        logger.info(f"🧹 [GenerationService] Gentle sanitization complete. Length: {len(raw_text)} -> {len(sanitized)}")
        return sanitized

    def _extract_survey_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract survey JSON from raw LLM output using centralized JSON utilities.
        """
        logger.info(f"🔍 [GenerationService] Starting JSON extraction from raw text (length: {len(raw_text)})")
        
        # Use the centralized JSON parsing utility
        result = parse_llm_json_response(raw_text, service_name="GenerationService")
        
        if result is not None:
            logger.info(f"✅ [GenerationService] JSON parsing succeeded! Keys: {list(result.keys())}")
            self._validate_and_fix_survey_structure(result)
            return result
        else:
            logger.error("❌ [GenerationService] All JSON extraction strategies failed")
            logger.error(f"❌ [GenerationService] Raw response length: {len(raw_text)}")
            logger.error(f"❌ [GenerationService] Raw response preview (first 1000 chars): {raw_text[:1000]}")
            logger.error(f"❌ [GenerationService] Raw response ending (last 500 chars): {raw_text[-500:]}")

            # Check for specific problematic patterns
            if '\x00' in raw_text:
                logger.error("❌ [GenerationService] Response contains NULL bytes")
            if any(ord(c) < 32 and c not in '\n\r\t' for c in raw_text[:1000]):
                logger.error("❌ [GenerationService] Response contains unexpected control characters")
                # Show hex representation of problematic characters
                problem_chars = [f"0x{ord(c):02x}" for c in raw_text[:100] if ord(c) < 32 and c not in '\n\r\t']
                logger.error(f"❌ [GenerationService] Control characters found: {problem_chars}")

            # Hard fail for LLM generation failures - no minimal survey fallback
            raise SurveyGenerationError(
                "LLM generation failed - unable to parse response as valid survey JSON. "
                "Please try again with a different model or check your input parameters.",
                error_code="GEN_001",
                details={
                    "raw_response_length": len(raw_text),
                    "response_preview": raw_text[:500],
                    "suggestion": "Try selecting a different model or retry the generation"
                }
            )

    def _extract_direct_json(self, sanitized_text: str) -> Optional[Dict[str, Any]]:
        """
        Direct JSON parsing for pre-sanitized text.
        This should work for most cases since the text is already cleaned.
        """
        logger.info(f"🔍 [GenerationService] Direct JSON: Attempting to parse {len(sanitized_text)} characters")
        logger.info(f"🔍 [GenerationService] Direct JSON: First 200 chars: {sanitized_text[:200]}...")
        logger.info(f"🔍 [GenerationService] Direct JSON: Last 200 chars: ...{sanitized_text[-200:]}")

        try:
            # First try direct parsing
            result = json.loads(sanitized_text)
            logger.info(f"✅ [GenerationService] Direct JSON parsing succeeded! Keys: {list(result.keys())}")

            # Count questions for verification
            if 'sections' in result:
                total_questions = sum(len(section.get('questions', [])) for section in result.get('sections', []))
                logger.info(f"✅ [GenerationService] Direct JSON found {total_questions} total questions")
            elif 'questions' in result:
                total_questions = len(result.get('questions', []))
                logger.info(f"✅ [GenerationService] Direct JSON found {total_questions} total questions (flat format)")

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ [GenerationService] Direct JSON parsing failed: {e}")
            logger.info(f"🔍 [GenerationService] JSON error at position {e.pos}: {sanitized_text[max(0, e.pos-50):e.pos+50]}")

            # Try to fix common JSON issues
            try:
                # Fix line breaks within string values
                import re
                fixed_text = re.sub(r'"([^"]*)\n([^"]*)"', r'"\1 \2"', sanitized_text)
                fixed_text = re.sub(r'"([^"]*)\n([^"]*)"', r'"\1 \2"', fixed_text)  # Run twice for nested breaks

                # Remove any remaining newlines within quoted strings
                fixed_text = re.sub(r'"([^"]*)\n([^"]*)"', r'"\1 \2"', fixed_text)

                logger.info(f"🔧 [GenerationService] Attempting to parse fixed JSON...")
                fixed_result = json.loads(fixed_text)
                logger.info(f"✅ [GenerationService] Fixed JSON parsing succeeded!")
                return fixed_result

            except json.JSONDecodeError as e2:
                logger.warning(f"⚠️ [GenerationService] Fixed JSON parsing also failed: {e2}")
                logger.info(f"🔍 [GenerationService] Fixed JSON error at position {e2.pos}: {fixed_text[max(0, e2.pos-50):e2.pos+50]}")
                return None

    def _log_question_extraction_metrics(self, response_text: str) -> None:
        """
        Log detailed metrics about question extraction potential
        """
        import re

        logger.info("📊 [GenerationService] === QUESTION EXTRACTION METRICS ===")

        # Count different question-like patterns
        patterns = {
            "Complete JSON objects": r'\{[^{}]*\}',
            "ID+Text patterns": r'"id"[^}]*"text"[^}]*["}]',
            "Text+ID patterns": r'"text"[^}]*"id"[^}]*["}]',
            "Question text fields": r'"text"\s*:\s*"[^"]{10,200}"',
            "Question-like strings": r'"[^"]*\?[^"]*"',
            "Survey questions": r'"(what|how|why|when|where|which|would|do|are|is|can|could|should)[^"]*\?"',
        }

        for pattern_name, pattern in patterns.items():
            matches = list(re.finditer(pattern, response_text, re.IGNORECASE))
            logger.info(f"📊 [GenerationService] - {pattern_name}: {len(matches)} found")

            # Show samples for debugging
            for i, match in enumerate(matches[:3]):  # Show first 3
                sample = match.group(0)[:100]
                logger.info(f"📊 [GenerationService]   Sample {i+1}: {sample}...")

        # Count sections mentions
        sections_mentions = len(re.findall(r'"sections"', response_text))
        questions_mentions = len(re.findall(r'"questions"', response_text))
        logger.info(f"📊 [GenerationService] - Sections mentions: {sections_mentions}")
        logger.info(f"📊 [GenerationService] - Questions mentions: {questions_mentions}")

        logger.info("📊 [GenerationService] ========================================")

    def _log_final_extraction_summary(self, survey_json: Dict[str, Any], original_text: str) -> None:
        """
        Log final summary of what was successfully extracted vs what was available
        """
        logger.info("🎯 [GenerationService] === FINAL EXTRACTION SUMMARY ===")

        # Count what we successfully extracted
        sections = survey_json.get("sections", [])
        total_questions = sum(len(section.get("questions", [])) for section in sections)

        logger.info(f"🎯 [GenerationService] Successfully extracted:")
        logger.info(f"🎯 [GenerationService] - {len(sections)} sections")
        logger.info(f"🎯 [GenerationService] - {total_questions} total questions")

        # Show section breakdown
        for section in sections:
            q_count = len(section.get("questions", []))
            logger.info(f"🎯 [GenerationService] - Section '{section.get('title', 'Unknown')}': {q_count} questions")

        # Compare to original potential
        import re
        original_potential = len(re.findall(r'"text"\s*:\s*"[^"]{10,200}"', original_text))
        json_objects = len(re.findall(r'\{[^{}]*\}', original_text))

        logger.info(f"🎯 [GenerationService] Original response contained:")
        logger.info(f"🎯 [GenerationService] - ~{original_potential} potential question texts")
        logger.info(f"🎯 [GenerationService] - ~{json_objects} JSON objects")

        if original_potential > 0:
            extraction_rate = (total_questions / original_potential) * 100
            logger.info(f"🎯 [GenerationService] Extraction success rate: {extraction_rate:.1f}%")

            if extraction_rate < 50:
                logger.warning(f"⚠️ [GenerationService] Low extraction rate - many questions may have been dropped!")
            elif extraction_rate > 90:
                logger.info(f"✅ [GenerationService] Excellent extraction rate!")
            else:
                logger.info(f"✅ [GenerationService] Good extraction rate")

        logger.info("🎯 [GenerationService] =======================================")

    # All the JSON extraction methods remain unchanged...
    def _extract_balanced_json_robust(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Robust balanced JSON extraction with error tolerance
        """
        try:
            # First try to find the main JSON block
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None

            brace_count = 0
            in_string = False
            escape_next = False
            quote_char = None

            for i in range(start_idx, len(response_text)):
                char = response_text[i]

                if escape_next:
                    escape_next = False
                    continue

                if in_string:
                    if char == '\\':
                        escape_next = True
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                else:
                    if char in ['"', "'"]:
                        in_string = True
                        quote_char = char
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_text = response_text[start_idx:i + 1]
                            try:
                                return json.loads(json_text)
                            except json.JSONDecodeError:
                                # Continue looking for next complete JSON
                                continue

            return None
        except Exception as e:
            logger.warning(f"⚠️ Balanced extraction error: {e}")
            return None

    def _extract_cleaned_json(self, sanitized_text: str) -> Optional[Dict[str, Any]]:
        """
        Simplified cleaned JSON extraction for pre-sanitized text.
        Since the text is already sanitized, this is just a fallback with minimal additional cleaning.
        """
        try:
            # Since text is already sanitized, just try direct parsing first
            return json.loads(sanitized_text)
        except json.JSONDecodeError:
            # If direct parsing fails, try one more round of whitespace fixing
            try:
                import re
                # Apply additional whitespace fixes if needed
                cleaned = self._fix_malformed_json_whitespace(sanitized_text)
                return json.loads(cleaned)
            except Exception:
                return None

    def _fix_malformed_json_whitespace(self, json_text: str) -> str:
        """
        Fix malformed JSON with excessive whitespace and line breaks
        """
        import re
        
        # First, fix newlines within quoted strings - this is the main issue
        # Pattern: "text" : "content\nwith\nnewlines" -> "text": "content with newlines"
        def fix_newlines_in_strings(match):
            key = match.group(1).strip()
            content = match.group(2)
            # Replace all newlines and excessive whitespace within the string content
            cleaned_content = re.sub(r'\s+', ' ', content).strip()
            # Fix spacing issues: remove spaces before punctuation
            cleaned_content = re.sub(r'\s+([,\.;:!?])', r'\1', cleaned_content)
            return f'"{key}": "{cleaned_content}"'
        
        # This pattern matches: "key" : "content with newlines"
        json_text = re.sub(r'"([^"]+)"\s*:\s*"([^"]*)"', fix_newlines_in_strings, json_text)
        
        # Fix strings that are broken across lines with more complex patterns
        # Pattern: "text" : "broken\nacross\nlines" -> "text": "broken across lines"
        def fix_broken_strings(match):
            content = match.group(1).replace(chr(10), " ").replace(chr(13), " ").strip()
            return f'": "{content}"'
        
        json_text = re.sub(r'"\s*:\s*"\s*([^"]*?)\s*"', fix_broken_strings, json_text)
        
        # Fix strings that are broken with excessive whitespace
        # Pattern: "text" : "word1\n\n\nword2" -> "text": "word1 word2"
        def fix_whitespace_strings(match):
            content = re.sub(r'\s+', ' ', match.group(1)).strip()
            # Fix spacing issues: remove spaces before punctuation
            content = re.sub(r'\s+([,\.;:!?])', r'\1', content)
            return f'": "{content}"'
        
        json_text = re.sub(r'"\s*:\s*"([^"]*?)"', fix_whitespace_strings, json_text)
        
        # Remove excessive whitespace around colons and commas
        json_text = re.sub(r'\s*:\s*', ': ', json_text)
        json_text = re.sub(r'\s*,\s*', ', ', json_text)
        
        # Fix broken object/array structures
        # Remove line breaks between object properties
        json_text = re.sub(r'}\s*\n\s*{', '}, {', json_text)
        json_text = re.sub(r']\s*\n\s*\[', '], [', json_text)
        
        # Fix broken string concatenation
        # Pattern: "word1"\n"word2" -> "word1 word2"
        json_text = re.sub(r'"\s*\n\s*"', ' ', json_text)
        
        # Clean up any remaining excessive whitespace
        json_text = re.sub(r'\s+', ' ', json_text)
        
        # Fix common JSON syntax issues
        json_text = re.sub(r',\s*}', '}', json_text)  # Remove trailing commas
        json_text = re.sub(r',\s*]', ']', json_text)  # Remove trailing commas in arrays
        
        return json_text

    def _extract_with_progressive_repair(self, sanitized_text: str) -> Optional[Dict[str, Any]]:
        """
        Progressive repair approach for pre-sanitized text.
        Since basic sanitization is done, focus on JSON-specific repairs.
        """
        try:
            import re

            # Since text is already sanitized, start with the text as-is
            json_text = sanitized_text

            # Progressive repair steps (focused on JSON-specific issues)
            repairs = [
                # Fix malformed whitespace (most common issue)
                lambda t: self._fix_malformed_json_whitespace(t),
                # Fix missing commas between properties
                lambda t: re.sub(r'"\s*\n\s*"([^"]*"):', r'",\n        "\1:', t),
                # Fix missing commas between array elements
                lambda t: re.sub(r'("\s*)\n\s*(")', r'\1,\n        \2', t),
                # Fix missing commas after objects
                lambda t: re.sub(r'}\s*\n\s*{', '},\n        {', t),
                lambda t: re.sub(r'}\s*\n\s*"', '},\n        "', t),
                # Remove trailing commas
                lambda t: re.sub(r',(\s*[}\]])', r'\1', t),
                # Fix common quote issues
                lambda t: re.sub(r'([^"\\])"([^",:}\]\s])', r'\1\\"\2', t)
            ]

            for i, repair_func in enumerate(repairs):
                try:
                    json_text = repair_func(json_text)
                    result = json.loads(json_text)
                    logger.info(f"✅ Progressive repair succeeded at step {i+1}")
                    return result
                except json.JSONDecodeError:
                    continue

            return None
        except Exception:
            return None

    def _force_rebuild_survey_json(self, sanitized_text: str) -> Optional[Dict[str, Any]]:
        """
        Force rebuild survey from extractable parts
        """
        try:
            import re

            logger.info("🔧 [GenerationService] Force rebuilding survey from parts")

            # Extract basic fields
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', sanitized_text)
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', sanitized_text)

            survey = {
                "title": title_match.group(1) if title_match else "Generated Survey",
                "description": desc_match.group(1) if desc_match else "AI-generated survey",
                "sections": []
            }

            # Check if content is markdown format (no JSON sections)
            # Since LLM returns markdown format, prioritize markdown extraction
            logger.info("🔍 [GenerationService] LLM returns markdown format, extracting questions directly")
            try:
                questions = self._extract_questions_by_force(sanitized_text)
                if questions:
                    logger.info(f"✅ [GenerationService] Successfully extracted {len(questions)} questions from markdown")
                    # Group questions intelligently instead of one big section
                    grouped_sections = self._group_questions_into_sections(questions)
                    survey["sections"] = grouped_sections
                else:
                    logger.warning("⚠️ [GenerationService] No questions extracted from markdown")
                    survey["sections"] = []
            except Exception as question_error:
                logger.warning(f"⚠️ [GenerationService] Error in markdown question extraction: {question_error}")
                # Try direct extraction as fallback
                try:
                    questions = self._extract_questions_from_text_force(sanitized_text)
                    if questions:
                        logger.info(f"✅ [GenerationService] Recovered {len(questions)} questions with direct extraction")
                        grouped_sections = self._group_questions_into_sections(questions)
                        survey["sections"] = grouped_sections
                    else:
                        survey["sections"] = []
                except Exception as recovery_error:
                    logger.warning(f"⚠️ [GenerationService] Recovery also failed: {recovery_error}")
                    survey["sections"] = []

            # Add metadata
            survey["estimated_time"] = 5
            survey["confidence_score"] = 0.7
            survey["methodologies"] = ["survey"]
            survey["golden_examples"] = []
            survey["metadata"] = {"target_responses": 100, "methodology": ["survey"]}

            question_count = sum(len(section.get("questions", [])) for section in survey["sections"])
            logger.info(f"🔧 Force rebuild extracted {question_count} questions")

            return survey if question_count > 0 else None

        except Exception as e:
            logger.error(f"❌ Force rebuild failed: {e}")
            return None

    def _extract_sections_by_force(self, text: str) -> List[Dict[str, Any]]:
        """
        Force extract sections using regex patterns
        """
        import re
        sections = []
        processed_sections = set()  # Track processed section IDs to prevent duplicates

        # Look for section-like patterns
        section_patterns = [
            r'"id"\s*:\s*(\d+)[^}]*"title"\s*:\s*"([^"]*)"[^}]*"questions"\s*:\s*\[(.*?)\]',
            r'\{\s*"id"\s*:\s*(\d+).*?"title"\s*:\s*"([^"]*)".*?"questions".*?\[(.*?)\]',
        ]

        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Check if we have the expected number of groups
                    if len(match.groups()) < 3:
                        logger.warning(f"⚠️ [GenerationService] Pattern match has only {len(match.groups())} groups, expected 3")
                        continue
                        
                    section_id = int(match.group(1))
                    section_title = match.group(2)
                    questions_text = match.group(3)
                except (IndexError, ValueError) as e:
                    logger.warning(f"⚠️ [GenerationService] Pattern match failed: {e}")
                    continue

                # Skip if we've already processed this section
                if section_id in processed_sections:
                    logger.info(f"🔍 [GenerationService] Skipping duplicate section {section_id}")
                    continue

                processed_sections.add(section_id)
                logger.info(f"🔍 [GenerationService] Processing section {section_id}: {section_title}")

                questions = self._extract_questions_from_text_force(questions_text)
                if questions:
                    sections.append({
                        "id": section_id,
                        "title": section_title,
                        "description": f"Section {section_id}",
                        "questions": questions
                    })

        return sections

    def _extract_questions_by_force(self, text: str) -> List[Dict[str, Any]]:
        """
        Force extract questions using multiple patterns
        """
        return self._extract_questions_from_text_force(text)

    def _extract_questions_from_text_force(self, text: str) -> List[Dict[str, Any]]:
        """
        Ultra-robust question extraction with detailed drop tracking
        """
        import re
        import time

        logger.info("🔍 [GenerationService] === QUESTION EXTRACTION TRACKING ===")
        logger.info(f"🔍 [GenerationService] Input text length: {len(text)} characters")

        # Add timeout to prevent infinite loops
        start_time = time.time()
        max_processing_time = 30  # 30 seconds max

        # Multiple question patterns - improved to catch more formats
        patterns = [
            # Complete JSON objects with various field orders
            ("Complete ID+Text objects", r'\{\s*"id"\s*:\s*"([^"]*)"[^}]*"text"\s*:\s*"([^"]*)"[^}]*\}'),
            ("Complete Text+ID objects", r'\{\s*"text"\s*:\s*"([^"]*)"[^}]*"id"\s*:\s*"([^"]*)"[^}]*\}'),
            ("Complete Question+ID objects", r'\{\s*"question"\s*:\s*"([^"]*)"[^}]*"id"\s*:\s*"([^"]*)"[^}]*\}'),
            ("Complete ID+Question objects", r'\{\s*"id"\s*:\s*"([^"]*)"[^}]*"question"\s*:\s*"([^"]*)"[^}]*\}'),

            # Partial patterns with more flexible matching
            ("Partial ID+Text patterns", r'"id"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"text"\s*:\s*"([^"]*)"'),
            ("Partial Text+ID patterns", r'"text"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"id"\s*:\s*"([^"]*)"'),
            ("Partial Question+ID patterns", r'"question"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"id"\s*:\s*"([^"]*)"'),
            ("Partial ID+Question patterns", r'"id"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"question"\s*:\s*"([^"]*)"'),

            # More flexible patterns that catch malformed JSON
            ("Flexible ID+Text", r'"id"\s*:\s*"([^"]*)"[^}]*?"text"\s*:\s*"([^"]*)"'),
            ("Flexible Text+ID", r'"text"\s*:\s*"([^"]*)"[^}]*?"id"\s*:\s*"([^"]*)"'),
            ("Flexible Question+ID", r'"question"\s*:\s*"([^"]*)"[^}]*?"id"\s*:\s*"([^"]*)"'),
            ("Flexible ID+Question", r'"id"\s*:\s*"([^"]*)"[^}]*?"question"\s*:\s*"([^"]*)"'),

            # Patterns for questions without explicit IDs
            ("Text only patterns", r'"text"\s*:\s*"([^"]*)"'),
            ("Question only patterns", r'"question"\s*:\s*"([^"]*)"'),
            
            # Markdown format patterns (common LLM output format)
            ("Markdown numbered questions", r'(\d+)\)\s*([^?\n]+[?])'),
            ("Markdown numbered questions multiline", r'(\d+)\)\s*([^?\n]+(?:\n[^?\n]+)*[?])'),
            ("Markdown bullet questions", r'[-*]\s*([^?\n]+[?])'),
            ("Markdown simple questions", r'^([^?\n]+[?])\s*$', re.MULTILINE),
        ]

        all_matches = []
        questions = []
        dropped_questions = []

        for i, pattern_item in enumerate(patterns):
            # Handle patterns that might have regex flags as third element
            if len(pattern_item) == 3:
                pattern_name, pattern, flags = pattern_item
            else:
                pattern_name, pattern = pattern_item
                flags = 0
            # Check timeout
            if time.time() - start_time > max_processing_time:
                logger.warning(f"⚠️ [GenerationService] Timeout reached after {max_processing_time}s, stopping question extraction")
                break

            try:
                matches = list(re.finditer(pattern, text, re.DOTALL | flags))
                logger.info(f"🔍 [GenerationService] Pattern '{pattern_name}': {len(matches)} matches found")

                for match in matches:
                    # Check timeout in inner loop too
                    if time.time() - start_time > max_processing_time:
                        logger.warning(f"⚠️ [GenerationService] Timeout reached during pattern processing, stopping")
                        break
                    
                    # Handle different pattern types with proper error handling
                    try:
                        logger.info(f"🔍 [GenerationService] Processing pattern {i} '{pattern_name}' with {len(match.groups())} groups: {match.groups()}")
                    
                        if i < 4:  # JSON patterns with ID+Text or Text+ID
                            q_id = match.group(1) if i < 2 else match.group(2)
                            q_text = match.group(2) if i < 2 else match.group(1)
                        elif i < 8:  # Partial JSON patterns
                            q_id = match.group(1) if i < 6 else match.group(2)
                            q_text = match.group(2) if i < 6 else match.group(1)
                        elif i < 12:  # Flexible JSON patterns
                            q_id = match.group(1) if i < 10 else match.group(2)
                            q_text = match.group(2) if i < 10 else match.group(1)
                        elif i < 14:  # Text/Question only patterns
                            q_id = None
                            q_text = match.group(1)
                        else:  # Markdown patterns
                            if i == 14:  # Markdown numbered questions
                                q_id = f"q{match.group(1)}"
                                q_text = match.group(2)
                            elif i == 15:  # Markdown numbered questions multiline
                                q_id = f"q{match.group(1)}"
                                q_text = match.group(2)
                            else:  # Markdown bullet or simple questions
                                q_id = None
                                q_text = match.group(1)
                        
                        logger.info(f"🔍 [GenerationService] Extracted q_id='{q_id}', q_text='{q_text[:50]}...'")
                        
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"⚠️ [GenerationService] Error unpacking match groups for pattern '{pattern_name}': {e}")
                        try:
                            logger.warning(f"⚠️ [GenerationService] Match groups: {match.groups()}")
                        except:
                            logger.warning(f"⚠️ [GenerationService] Match groups: Not available")
                        continue
                    except Exception as e:
                        logger.error(f"❌ [GenerationService] Unexpected error in pattern processing: {e}")
                        try:
                            logger.error(f"❌ [GenerationService] Pattern: {pattern_name}, Match: {match.groups()}")
                        except:
                            logger.error(f"❌ [GenerationService] Pattern: {pattern_name}, Match: Not available")
                        import traceback
                        logger.error(f"❌ [GenerationService] Traceback: {traceback.format_exc()}")
                        continue

                        # Clean the text - handle excessive newlines and formatting issues
                        original_text = q_text
                        # Remove escaped newlines and excessive whitespace
                        q_text = re.sub(r'\\n', ' ', q_text)
                        # Remove actual newlines and excessive whitespace
                        q_text = re.sub(r'\n+', ' ', q_text)
                        # Normalize all whitespace to single spaces
                        q_text = re.sub(r'\s+', ' ', q_text).strip()
                        # Fix spacing issues: remove spaces before punctuation
                        q_text = re.sub(r'\s+([,\.;:!?])', r'\1', q_text)
                        # Remove leading/trailing punctuation that might be artifacts
                        q_text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', q_text).strip()

                        all_matches.append({
                            "pattern": pattern_name,
                            "id": q_id,
                            "text": q_text,
                            "original_text": original_text,
                            "match_text": match.group(0)[:200]
                        })

                        # Validation checks
                        drop_reason = None
                        if not q_text:
                            drop_reason = "Empty text after cleaning"
                        elif len(q_text) <= 5:
                            drop_reason = f"Text too short ({len(q_text)} chars)"
                        elif len(q_text) > 500:
                            drop_reason = f"Text too long ({len(q_text)} chars)"
                        elif not any(char.isalpha() for char in q_text):
                            drop_reason = "No alphabetic characters"

                        if drop_reason:
                            dropped_questions.append({
                                "id": q_id,
                                "text": q_text[:100],
                                "reason": drop_reason,
                                "pattern": pattern_name
                            })
                            logger.warning(f"⚠️ [GenerationService] Dropped question '{q_id}': {drop_reason}")
                        else:
                            # Extract options from the original match text
                            try:
                                if i >= 14:  # Markdown patterns - extract options from surrounding text
                                    options = self._extract_options_from_markdown(text, match.start(), match.end())
                                else:  # JSON patterns
                                    options = self._extract_options_from_question_text(match.group(0))
                            except Exception as options_error:
                                logger.warning(f"⚠️ [GenerationService] Error extracting options: {options_error}")
                                options = []
                            
                            if options:
                                logger.info(f"🔍 [GenerationService] Extracted {len(options)} options for question '{q_id}': {options}")
                            
                            try:
                                # Determine question type based on content and options
                                question_type = "text"
                                if options:
                                    if len(options) <= 5:
                                        question_type = "single_choice"
                                    else:
                                        question_type = "multiple_choice"
                                elif any(keyword in q_text.lower() for keyword in ["price", "amount", "cost", "number", "age", "quantity", "how much", "how many"]):
                                    question_type = "numeric_open"
                                elif any(keyword in q_text.lower() for keyword in ["rate", "score", "matrix", "scale"]):
                                    question_type = "matrix_likert"
                                
                                question = {
                                    "id": q_id or f"q{len(questions) + 1}",
                                    "text": q_text,
                                    "type": question_type,
                                    "options": options,
                                    "required": True,
                                    "category": "general"
                                }
                                questions.append(question)
                            except Exception as question_error:
                                logger.warning(f"⚠️ [GenerationService] Error creating question: {question_error}")
                                logger.warning(f"⚠️ [GenerationService] Question data: q_id='{q_id}', q_text='{q_text[:50]}...', options={len(options) if options else 0}")
                        continue

            except Exception as pattern_error:
                logger.warning(f"⚠️ [GenerationService] Error processing pattern '{pattern_name}': {pattern_error}")
                logger.warning(f"⚠️ [GenerationService] Pattern index: {i}, Pattern: {pattern}")
                import traceback
                logger.warning(f"⚠️ [GenerationService] Traceback: {traceback.format_exc()}")
                continue

        logger.info(f"🔍 [GenerationService] Total matches found: {len(all_matches)}")
        logger.info(f"🔍 [GenerationService] Valid questions before dedup: {len(questions)}")
        logger.info(f"🔍 [GenerationService] Questions dropped (validation): {len(dropped_questions)}")
        
        # Debug: Show the questions we extracted
        for i, q in enumerate(questions):
            question_text = q.get('text', 'N/A')
            text_preview = question_text[:50] if question_text is not None else '<null>'
            logger.info(f"🔍 [GenerationService] Question {i+1}: id='{q.get('id', 'N/A')}', text='{text_preview}...', options={len(q.get('options', []))}")

        # Remove duplicates based on text similarity
        unique_questions = []
        duplicate_count = 0

        try:
            logger.info(f"🔍 [GenerationService] Starting deduplication with {len(questions)} questions")
            
            for i, q in enumerate(questions):
                try:
                    logger.info(f"🔍 [GenerationService] Processing question {i+1}: {q.get('id', 'N/A')}")
                    is_duplicate = False
                    for j, uq in enumerate(unique_questions):
                        try:
                            if self._texts_similar(q["text"], uq["text"]):
                                is_duplicate = True
                                duplicate_count += 1
                                logger.info(f"🔍 [GenerationService] Duplicate found: '{q['id']}' similar to '{uq['id']}'")
                                break
                        except Exception as sim_error:
                            logger.warning(f"⚠️ [GenerationService] Error in similarity check: {sim_error}")
                            logger.warning(f"⚠️ [GenerationService] Question q: {q}")
                            logger.warning(f"⚠️ [GenerationService] Question uq: {uq}")
                            continue
                            
                    if not is_duplicate:
                        unique_questions.append(q)
                        
                except Exception as q_error:
                    logger.warning(f"⚠️ [GenerationService] Error processing question {i+1}: {q_error}")
                    logger.warning(f"⚠️ [GenerationService] Question data: {q}")
                    # Continue with next question instead of failing completely
                    continue

            logger.info(f"🔍 [GenerationService] Questions dropped (duplicates): {duplicate_count}")
            logger.info(f"✅ [GenerationService] Final unique questions: {len(unique_questions)}")

            # Log samples of dropped questions
            if dropped_questions:
                logger.info("❌ [GenerationService] Sample dropped questions:")
                for dropped in dropped_questions[:5]:  # Show first 5
                    logger.info(f"❌ [GenerationService] - '{dropped['id']}': {dropped['reason']} | Text: '{dropped['text']}'")

            logger.info("🔍 [GenerationService] =====================================")

            return unique_questions
            
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Error in question deduplication: {e}")
            logger.warning(f"⚠️ [GenerationService] Error type: {type(e)}")
            logger.warning(f"⚠️ [GenerationService] Questions so far: {len(questions)}")
            logger.warning(f"⚠️ [GenerationService] All matches: {len(all_matches)}")
            # Return the questions we have so far instead of failing
            logger.info(f"✅ [GenerationService] Returning {len(questions)} questions despite deduplication error")
            return questions

    def _extract_options_from_question_text(self, question_text: str) -> List[str]:
        """
        Extract options/choices from question text using regex patterns
        """
        import re
        options = []
        
        try:
            # Look for options array patterns
            options_patterns = [
                r'"options"\s*:\s*\[(.*?)\]',  # "options": ["opt1", "opt2"]
                r'"choices"\s*:\s*\[(.*?)\]',  # "choices": ["opt1", "opt2"]
                r'"answers"\s*:\s*\[(.*?)\]',  # "answers": ["opt1", "opt2"]
                r'"scale"\s*:\s*\[(.*?)\]',    # "scale": ["opt1", "opt2"]
                r'"items"\s*:\s*\[(.*?)\]',    # "items": ["opt1", "opt2"]
                r'"values"\s*:\s*\[(.*?)\]',   # "values": ["opt1", "opt2"]
            ]
            
            for pattern in options_patterns:
                match = re.search(pattern, question_text, re.DOTALL)
                if match:
                    options_text = match.group(1)
                    # Extract individual options
                    option_matches = re.findall(r'"([^"]*)"', options_text)
                    for opt in option_matches:
                        if opt.strip():
                            options.append(opt.strip())
                    break
            
            # If no options array found, look for individual option patterns
            if not options:
                # Look for patterns like "option1", "option2" or "choice1", "choice2"
                individual_patterns = [
                    r'"option\d*"\s*:\s*"([^"]*)"',
                    r'"choice\d*"\s*:\s*"([^"]*)"',
                    r'"answer\d*"\s*:\s*"([^"]*)"',
                    r'"item\d*"\s*:\s*"([^"]*)"',
                    r'"value\d*"\s*:\s*"([^"]*)"',
                ]
                
                for pattern in individual_patterns:
                    matches = re.findall(pattern, question_text)
                    for match in matches:
                        if match.strip():
                            options.append(match.strip())
            
            # Limit to reasonable number of options
            return options[:10]
            
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Error extracting options: {e}")
            return []

    def _extract_options_from_markdown(self, text: str, question_start: int, question_end: int) -> List[str]:
        """
        Extract options from markdown format text around a question
        """
        import re
        options = []
        
        try:
            # Look for bullet points or dashes after the question
            # Find the text after the question until the next question or end
            text_after_question = text[question_end:]
            
            # Look for bullet points or dashes
            bullet_patterns = [
                r'^[-*]\s*([^?\n]+)$',  # - Option text
                r'^[-*]\s*([^?\n]+)\s*$',  # - Option text (with spaces)
            ]
            
            for pattern in bullet_patterns:
                matches = re.finditer(pattern, text_after_question, re.MULTILINE)
                for match in matches:
                    option_text = match.group(1).strip()
                    # Stop if we hit another question (starts with number or bullet)
                    if re.match(r'^\d+\)', option_text) or re.match(r'^[-*]', option_text):
                        break
                    if option_text and len(option_text) > 2:
                        options.append(option_text)
                        if len(options) >= 10:  # Limit options
                            break
                if options:
                    break
            
            # If no bullet points found, look for numbered options
            if not options:
                numbered_pattern = r'^(\d+[\.\)])\s*([^?\n]+)$'
                matches = re.finditer(numbered_pattern, text_after_question, re.MULTILINE)
                for match in matches:
                    try:
                        option_text = match.group(2).strip()
                        if option_text and len(option_text) > 2:
                            options.append(option_text)
                            if len(options) >= 10:  # Limit options
                                break
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"⚠️ [GenerationService] Error extracting numbered option: {e}")
                        logger.warning(f"⚠️ [GenerationService] Match groups: {match.groups()}")
                        continue
            
            return options[:10]
            
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Error extracting markdown options: {e}")
            return []

    def _texts_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar"""
        if not text1 or not text2:
            return False

        # Simple similarity check
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return (intersection / union) >= threshold

    def _validate_and_fix_survey_structure(self, survey: Dict[str, Any]) -> None:
        """
        Validate and fix survey structure in place
        """
        # Ensure basic fields exist
        if not survey.get("title"):
            survey["title"] = "Generated Survey"
        if not survey.get("description"):
            survey["description"] = "AI-generated survey"

        # Handle sections/questions format
        has_sections = "sections" in survey and isinstance(survey["sections"], list)
        has_questions = "questions" in survey and isinstance(survey["questions"], list)

        if has_sections and has_questions:
            del survey["questions"]  # Prefer sections format
        elif has_questions and not has_sections:
            # Convert questions to sections format
            survey["sections"] = [{
                "id": 1,
                "title": "Survey Questions",
                "description": "All questions",
                "questions": survey["questions"]
            }]
            del survey["questions"]
        elif not has_sections:
            survey["sections"] = []

        # Consolidate sections to avoid too many single-question sections
        survey["sections"] = self._consolidate_sections(survey.get("sections", []))

        # Ensure each section has required fields
        for i, section in enumerate(survey.get("sections", [])):
            if not isinstance(section, dict):
                continue
            if "id" not in section:
                section["id"] = i + 1
            if "title" not in section:
                section["title"] = f"Section {section['id']}"
            if "description" not in section:
                section["description"] = f"Section {section['id']} questions"
            if "questions" not in section:
                section["questions"] = []

        # Add metadata if missing
        if "estimated_time" not in survey:
            survey["estimated_time"] = 5
        if "confidence_score" not in survey:
            survey["confidence_score"] = 0.8
        if "methodologies" not in survey:
            survey["methodologies"] = ["survey"]
        if "golden_examples" not in survey:
            survey["golden_examples"] = []
        if "metadata" not in survey:
            survey["metadata"] = {"target_responses": 100, "methodology": ["survey"]}

    def _consolidate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate sections to avoid too many single-question sections
        """
        if not sections:
            return sections

        logger.info(f"🔧 [GenerationService] Consolidating {len(sections)} sections")

        # Count questions per section
        section_questions = [(i, len(section.get("questions", []))) for i, section in enumerate(sections)]
        total_questions = sum(count for _, count in section_questions)

        logger.info(f"🔧 [GenerationService] Total questions: {total_questions}")

        # If we have many single-question sections, consolidate them
        single_question_sections = [i for i, count in section_questions if count == 1]
        multi_question_sections = [i for i, count in section_questions if count > 1]

        logger.info(f"🔧 [GenerationService] Single-question sections: {len(single_question_sections)}")
        logger.info(f"🔧 [GenerationService] Multi-question sections: {len(multi_question_sections)}")

        # If we have a well-structured survey with multiple sections that each have multiple questions,
        # don't consolidate them - just return as-is
        if len(multi_question_sections) >= 3 and len(single_question_sections) <= 2:
            logger.info(f"🔧 [GenerationService] Well-structured survey detected, keeping {len(sections)} sections as-is")
            return sections

        # Strategy: If we have more than 2 single-question sections, consolidate them
        if len(single_question_sections) > 2:
            consolidated_sections = []

            # Keep multi-question sections as-is
            for i in multi_question_sections:
                consolidated_sections.append(sections[i])

            # Group single-question sections by topic/category or combine them
            single_questions = []
            for i in single_question_sections:
                section = sections[i]
                questions = section.get("questions", [])
                for question in questions:
                    # Add section context to question if needed
                    if not question.get("category") and section.get("title"):
                        question["category"] = section["title"]
                    single_questions.append(question)

            # Create consolidated sections from single questions
            if single_questions:
                # Group by category if available, otherwise put all in one section
                categorized_questions = {}
                uncategorized_questions = []

                for question in single_questions:
                    category = question.get("category")
                    if category and category not in ["general", "Section 1", "Section 2", "Section 3"]:
                        if category not in categorized_questions:
                            categorized_questions[category] = []
                        categorized_questions[category].append(question)
                    else:
                        uncategorized_questions.append(question)

                # Create sections from categories, but be aggressive about grouping
                section_id = len(consolidated_sections) + 1

                # Collect all questions that don't have enough for their own category
                mixed_questions = []

                for category, questions in categorized_questions.items():
                    if len(questions) >= 3:  # Only create category section if 3+ questions
                        consolidated_sections.append({
                            "id": section_id,
                            "title": category,
                            "description": f"Questions about {category.lower()}",
                            "questions": questions
                        })
                        section_id += 1
                    else:
                        mixed_questions.extend(questions)

                # Add uncategorized questions to the mix
                mixed_questions.extend(uncategorized_questions)

                # Group all remaining questions into fewer sections
                if mixed_questions:
                    if len(mixed_questions) <= 4:
                        # Few questions, one section
                        consolidated_sections.append({
                            "id": section_id,
                            "title": "Additional Questions",
                            "description": "Additional survey questions",
                            "questions": mixed_questions
                        })
                    else:
                        # Many questions, split into 2 sections max
                        mid_point = len(mixed_questions) // 2
                        consolidated_sections.append({
                            "id": section_id,
                            "title": "Survey Questions - Part 1",
                            "description": "First set of survey questions",
                            "questions": mixed_questions[:mid_point]
                        })
                        consolidated_sections.append({
                            "id": section_id + 1,
                            "title": "Survey Questions - Part 2",
                            "description": "Second set of survey questions",
                            "questions": mixed_questions[mid_point:]
                        })

            logger.info(f"🔧 [GenerationService] Consolidated to {len(consolidated_sections)} sections")
            return consolidated_sections

        else:
            # Not too many single sections, keep as-is but ensure proper numbering
            for i, section in enumerate(sections):
                section["id"] = i + 1
            logger.info(f"🔧 [GenerationService] Keeping {len(sections)} sections as-is")
            return sections

    def _group_questions_into_sections(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group questions into logical sections based on content analysis
        """
        if len(questions) <= 5:
            # Few questions, put them all in one section
            return [{
                "id": 1,
                "title": "Survey Questions",
                "description": "All survey questions",
                "questions": questions
            }]

        # Group questions by category or topic keywords
        topic_groups = {
            "demographics": [],
            "experience": [],
            "satisfaction": [],
            "preferences": [],
            "feedback": [],
            "product": [],
            "concept": [],
            "general": []
        }

        # Keywords to identify question types
        topic_keywords = {
            "demographics": ["age", "gender", "location", "education", "income", "occupation", "demographic", "describes you", "best describes", "which of the following"],
            "experience": ["experience", "how long", "previous", "background", "history", "used", "past", "often have you", "how often", "frequency"],
            "satisfaction": ["satisfied", "happy", "pleased", "rating", "rate", "score", "scale", "satisfaction", "satisfied with", "how satisfied"],
            "preferences": ["prefer", "favorite", "choose", "select", "like", "want", "desire", "preference", "would you prefer", "which would you choose"],
            "feedback": ["improve", "suggest", "feedback", "recommend", "opinion", "thoughts", "comment", "suggestions", "recommendations"],
            "product": ["product", "camera", "device", "feature", "functionality", "capability", "performance", "quality", "design"],
            "concept": ["concept", "introduction", "new", "innovation", "review", "description", "presentation", "show", "demonstrate"]
        }

        for question in questions:
            question_text = question.get("text", "").lower()
            assigned = False

            for topic, keywords in topic_keywords.items():
                if any(keyword in question_text for keyword in keywords):
                    topic_groups[topic].append(question)
                    assigned = True
                    break

            if not assigned:
                topic_groups["general"].append(question)

        # Create sections from groups
        sections = []
        section_id = 1

        # Debug: Log the topic_groups structure
        logger.info(f"🔍 [GenerationService] Topic groups structure: {topic_groups}")
        logger.info(f"🔍 [GenerationService] Topic groups type: {type(topic_groups)}")
        logger.info(f"🔍 [GenerationService] Topic groups keys: {list(topic_groups.keys())}")
        
        for topic, group_questions in topic_groups.items():
            logger.info(f"🔍 [GenerationService] Topic '{topic}': {type(group_questions)} with {len(group_questions) if isinstance(group_questions, list) else 'N/A'} items")

        title_map = {
            "demographics": "Demographics & Screening",
            "experience": "Background & Experience",
            "satisfaction": "Satisfaction & Rating",
            "preferences": "Preferences & Choices",
            "feedback": "Feedback & Suggestions",
            "product": "Product Features & Capabilities",
            "concept": "Product Introduction & Concepts",
            "general": "General Questions"
        }

        # Create sections for groups with questions
        for topic, group_questions in topic_groups.items():
            # Ensure group_questions is a list
            if not isinstance(group_questions, list):
                logger.warning(f"⚠️ [GenerationService] Invalid group_questions type for topic '{topic}': {type(group_questions)}")
                continue
                
            if len(group_questions) >= 1:  # Create section for any group with questions
                sections.append({
                    "id": section_id,
                    "title": title_map[topic],
                    "description": f"{title_map[topic].lower()} questions",
                    "questions": group_questions
                })
                section_id += 1

        # If no sections were created (shouldn't happen with new logic), fallback to single section
        if len(sections) == 0:
            sections.append({
                "id": 1,
                "title": "Survey Questions",
                "description": "All survey questions",
                "questions": questions
            })

        logger.info(f"🔧 [GenerationService] Grouped {len(questions)} questions into {len(sections)} logical sections")

        # Log section breakdown
        for section in sections:
            logger.info(f"🔧 [GenerationService] - {section['title']}: {len(section['questions'])} questions")

        return sections

    def _repair_corrupted_format(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Special repair method for the corrupted format where every character is separated by newlines.
        This handles the specific case we're seeing in production.
        """
        logger.info("🔧 [GenerationService] Starting corrupted format repair...")
        
        try:
            import re
            
            # Step 1: Handle extreme corruption where every character is on a new line
            # First, try to identify if this is the extreme case
            if raw_text.count('\n') > len(raw_text) * 0.1:  # More than 10% newlines
                logger.info("🔧 [GenerationService] Detected extreme corruption - every character on new line")
                # For extreme corruption, we need to extract content and reconstruct
                return self._extract_content_from_corrupted_json(raw_text)
            else:
                # Normal case - just remove extra whitespace
                cleaned = re.sub(r'\s+', ' ', raw_text)
            
            # Step 2: Fix the specific corruption pattern where quotes are separated
            # Pattern: "word" -> "word" (remove extra quotes)
            cleaned = re.sub(r'"([^"]*)"([^":,}\]]*)"([^":,}\]]*)"', r'"\1\2\3"', cleaned)
            
            # Step 3: Fix missing commas between objects
            cleaned = re.sub(r'}\s*{', '}, {', cleaned)
            cleaned = re.sub(r']\s*\[', '], [', cleaned)
            cleaned = re.sub(r'}\s*\[', '}, [', cleaned)
            cleaned = re.sub(r']\s*{', '], {', cleaned)
            
            # Step 4: Remove trailing commas
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            
            # Step 5: Try to parse the cleaned JSON
            result = json.loads(cleaned)
            logger.info(f"✅ [GenerationService] Corrupted format repair successful!")
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Corrupted format repair failed: {e}")
            return None

    def _extract_content_from_corrupted_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract content from severely corrupted JSON where every character is on a new line.
        This method reconstructs a valid survey by extracting key information.
        """
        logger.info("🔧 [GenerationService] Extracting content from corrupted JSON...")
        
        try:
            import re
            
            # First, normalize the text by removing excessive newlines but preserving spaces
            # Replace multiple whitespace with single spaces, but be more careful about quotes
            normalized = re.sub(r'\s+', ' ', raw_text)
            
            # Now extract key information using regex patterns that account for spaces around quotes
            title_match = re.search(r'\"\s*title\s*\"\s*:\s*\"\s*([^\"]*?)\s*\"', normalized)
            description_match = re.search(r'\"\s*description\s*\"\s*:\s*\"\s*([^\"]*?)\s*\"', normalized)
            
            # Extract sections information
            sections_match = re.search(r'\"\s*sections\s*\"\s*:\s*\[\s*(.*?)\s*\]', normalized, re.DOTALL)
            
            # Extract metadata
            estimated_time_match = re.search(r'\"\s*estimated_time\s*\"\s*:\s*(\d+)', normalized)
            target_responses_match = re.search(r'\"\s*target_responses\s*\"\s*:\s*(\d+)', normalized)
            
            # Clean up extracted text by removing extra spaces
            def clean_text(text):
                if not text:
                    return text
                # Remove extra spaces but preserve single spaces
                cleaned = re.sub(r'\s+', ' ', text.strip())
                # Fix specific corruption patterns - only remove spaces that are clearly from corruption
                # Remove spaces around punctuation that should be attached
                cleaned = re.sub(r'([a-zA-Z])\s+([&])', r'\1\2', cleaned)  # Remove spaces before &
                cleaned = re.sub(r'([&])\s+([a-zA-Z])', r'\1\2', cleaned)  # Remove spaces after &
                cleaned = re.sub(r'([a-zA-Z])\s+([(])', r'\1\2', cleaned)  # Remove spaces before (
                cleaned = re.sub(r'([)])\s+([a-zA-Z])', r'\1\2', cleaned)  # Remove spaces after )
                # Fix specific patterns from the corruption
                cleaned = re.sub(r'([a-zA-Z])\s+([-])', r'\1\2', cleaned)  # Remove spaces before -
                cleaned = re.sub(r'([-])\s+([a-zA-Z])', r'\1\2', cleaned)  # Remove spaces after -
                # Fix specific corruption patterns we see in the data
                cleaned = re.sub(r'Me\s+vo', 'Mevo', cleaned)  # Fix "Me vo" -> "Mevo"
                cleaned = re.sub(r'Str\s+atos', 'Stratos', cleaned)  # Fix "Str atos" -> "Stratos"
                cleaned = re.sub(r'Tech\s+ies', 'Techies', cleaned)  # Fix "Tech ies" -> "Techies"
                cleaned = re.sub(r'Expression\s+ists', 'Expressionists', cleaned)  # Fix "Expression ists" -> "Expressionists"
                cleaned = re.sub(r'Elastic\s+ity', 'Elasticity', cleaned)  # Fix "Elastic ity" -> "Elasticity"
                cleaned = re.sub(r'Strateg\s+ic', 'Strategic', cleaned)  # Fix "Strateg ic" -> "Strategic"
                cleaned = re.sub(r'Target\s+s', 'Targets', cleaned)  # Fix "Target s" -> "Targets"
                cleaned = re.sub(r'method\s+s', 'methods', cleaned)  # Fix "method s" -> "methods"
                return cleaned
            
            # Build a basic survey structure
            survey = {
                "title": clean_text(title_match.group(1)) if title_match else "Survey",
                "description": clean_text(description_match.group(1)) if description_match else "Survey description",
                "sections": [],
                "estimated_time": int(estimated_time_match.group(1)) if estimated_time_match else 10,
                "confidence_score": 0.8,
                "methodologies": ["quantitative"],
                "golden_examples": [],
                "metadata": {
                    "estimated_time": int(estimated_time_match.group(1)) if estimated_time_match else 10,
                    "target_responses": int(target_responses_match.group(1)) if target_responses_match else 100,
                    "methodology_tags": ["survey"],
                    "sections_count": 1
                }
            }
            
            # Try to extract sections if possible
            if sections_match:
                sections_text = sections_match.group(1)
                # Look for section titles
                section_titles = re.findall(r'\"\s*title\s*\"\s*:\s*\"\s*([^\"]*?)\s*\"', sections_text)
                for i, title in enumerate(section_titles[:3]):  # Limit to 3 sections
                    section = {
                        "id": i + 1,
                        "title": clean_text(title),
                        "description": f"Section {i + 1} description",
                        "questions": []
                    }
                    survey["sections"].append(section)
            
            # If no sections found, create a default one
            if not survey["sections"]:
                survey["sections"] = [{
                    "id": 1,
                    "title": "Main Questions",
                    "description": "Survey questions",
                    "questions": []
                }]
            
            logger.info(f"✅ [GenerationService] Content extraction successful! Found {len(survey['sections'])} sections")
            return survey
            
        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Content extraction failed: {e}")
            return None


    # ============================================================================
    # STREAMING GENERATION METHODS (OPTIONAL - DISABLED BY DEFAULT)
    # ============================================================================

    async def _generate_survey_with_streaming(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate survey using reliable sync mode (streaming disabled by default)
        """
        try:
            logger.info(f"🚀 [GenerationService] Starting sync survey generation")
            start_time = time.time()

            # Check if streaming is explicitly enabled via environment variable
            # Set ENABLE_STREAMING_GENERATION=true to enable streaming (not recommended)
            enable_streaming = os.getenv('ENABLE_STREAMING_GENERATION', 'false').lower() == 'true'
            
            if enable_streaming:
                logger.info(f"🔄 [GenerationService] Streaming mode enabled via environment variable")
                # Send initial progress update
                if self.ws_client and self.workflow_id:
                    progress_tracker = get_progress_tracker(self.workflow_id)
                    progress_data = progress_tracker.get_progress_data("llm_processing")
                    await self.ws_client.send_progress_update(self.workflow_id, progress_data)

                # Try streaming first, fallback to sync if it fails
                try:
                    return await self._stream_with_replicate(prompt, start_time)
                except Exception as streaming_error:
                    logger.warning(f"⚠️ [GenerationService] Streaming failed: {streaming_error}")
                    logger.info(f"🔄 [GenerationService] Falling back to sync mode")
                    return await self._generate_with_sync_fallback(prompt)
            else:
                # Use reliable sync mode by default
                logger.info(f"🔄 [GenerationService] Using reliable sync mode (streaming disabled)")
                return await self._generate_with_sync_fallback(prompt)

        except Exception as e:
            logger.error(f"❌ [GenerationService] Generation failed: {str(e)}")
            # Final fallback to original sync method
            return await self._generate_with_sync_fallback(prompt)

    async def _stream_with_replicate(self, prompt: str, start_time: float) -> Dict[str, Any]:
        """Stream content from Replicate with real-time analysis"""

        # Send initial generating_questions progress
        if self.ws_client and self.workflow_id:
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("generating_questions")
            await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        # Create streaming prediction
        prediction = await self.replicate_client.predictions.async_create(
            model=self.model,
            input={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.9
            },
            stream=True
        )

        logger.info(f"📡 [GenerationService] Streaming prediction created: {prediction.id}")

        # Collect streamed content
        accumulated_content = ""
        last_analysis_time = start_time
        event_count = 0
        output_events = 0

        try:
            # Stream the response (Replicate returns a sync generator; iterate synchronously)
            for event in prediction.stream():
                event_count += 1
                
                # Enhanced event type detection with better logging
                event_type = getattr(event, "event", None) or getattr(event, "type", None)
                event_data = getattr(event, "data", "")
                
                # Log event details for debugging
                logger.debug(f"🛈 [GenerationService] Event {event_count}: type='{event_type}', data_length={len(str(event_data))}")
                
                # Handle different event types more robustly
                if event_type == 'output' or event_type == 'data' or (not event_type and event_data):
                    output_events += 1
                    # Add new content
                    new_content = str(event_data)
                    accumulated_content += new_content
                    
                    logger.debug(f"📝 [GenerationService] Output event {output_events}: added {len(new_content)} chars, total: {len(accumulated_content)}")

                    current_time = time.time()
                    elapsed_time = current_time - start_time

                    # Analyze every 2-3 seconds or when significant content is added
                    if (current_time - last_analysis_time >= 2.5 or
                        len(new_content) > 100 or
                        '"text"' in new_content):

                        await self._analyze_streaming_content(accumulated_content, elapsed_time)
                        last_analysis_time = current_time

                elif event_type == 'error':
                    logger.error(f"❌ [GenerationService] Streaming error: {event_data}")
                    raise Exception(f"Streaming error: {event_data}")
                elif event_type == 'done' or event_type == 'completed':
                    logger.info(f"✅ [GenerationService] Streaming completed after {event_count} events, {output_events} output events")
                    break
                else:
                    # Non-output events (e.g., logs) can be safely ignored or logged at debug level
                    logger.debug(f"🛈 [GenerationService] Non-output event: {event_type}")

            # Check if we actually collected any content
            if not accumulated_content.strip():
                logger.warning(f"⚠️ [GenerationService] No content collected from streaming after {event_count} events")
                logger.warning(f"⚠️ [GenerationService] Output events received: {output_events}")
                
                # If no content was collected, this is likely a streaming API issue
                # Fall back to async polling method
                logger.info(f"🔄 [GenerationService] Falling back to async polling due to empty content")
                raise Exception("STREAMING_NO_CONTENT")

        except Exception as e:
            if "STREAMING_NO_CONTENT" in str(e):
                # Re-raise to trigger fallback
                raise e
            else:
                logger.error(f"❌ [GenerationService] Streaming failed: {str(e)}")
                raise e

        # Final analysis
        total_time = time.time() - start_time
        await self._analyze_streaming_content(accumulated_content, total_time)

        # Validate that we have meaningful content
        if not accumulated_content.strip() or len(accumulated_content.strip()) < 50:
            logger.error(f"❌ [GenerationService] Insufficient content collected: {len(accumulated_content)} chars")
            raise Exception("STREAMING_INSUFFICIENT_CONTENT")

        # Parse and return the result
        survey_data = self._extract_survey_json(accumulated_content)

        return {
            "survey": survey_data,
            "generation_metadata": {
                "model": self.model,
                "response_time_ms": int(total_time * 1000),
                "streaming_enabled": True,
                "content_length": len(accumulated_content),
                "event_count": event_count,
                "output_events": output_events,
                "raw_response": accumulated_content
            }
        }

    async def _generate_with_async_polling(self, prompt: str, start_time: float) -> Dict[str, Any]:
        """Generate using async polling with progress updates"""

        # Send initial generating_questions progress
        if self.ws_client and self.workflow_id:
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("generating_questions")
            await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        # Create prediction without streaming
        prediction = await self.replicate_client.predictions.async_create(
            model=self.model,
            input={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.9
            }
        )

        logger.info(f"📡 [GenerationService] Async prediction created: {prediction.id}")

        # Poll with progress updates
        while prediction.status not in ["succeeded", "failed", "canceled"]:
            await asyncio.sleep(2)  # Poll every 2 seconds
            await prediction.async_reload()

            if self.ws_client and self.workflow_id:
                progress_tracker = get_progress_tracker(self.workflow_id)
                progress_data = progress_tracker.get_progress_data("llm_processing", "async_polling")
                progress_data["message"] = f"AI generating survey... {time.time() - start_time:.0f}s elapsed"
                await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        if prediction.status == "failed":
            raise Exception(f"Prediction failed: {prediction.error}")

        # Get final result
        if isinstance(prediction.output, list):
            output_text = "\n".join(str(item) for item in prediction.output)
        else:
            output_text = str(prediction.output)

        survey_data = self._extract_survey_json(output_text)

        total_time = time.time() - start_time
        return {
            "survey": survey_data,
            "generation_metadata": {
                "model": self.model,
                "response_time_ms": int(total_time * 1000),
                "streaming_enabled": False,
                "async_polling": True,
                "raw_response": output_text
            }
        }

    async def _generate_with_sync_fallback(self, prompt: str) -> Dict[str, Any]:
        """Reliable sync method for survey generation"""
        logger.info("🔄 [GenerationService] Using reliable sync generation method")

        # Send initial generating_questions progress
        if self.ws_client and self.workflow_id:
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("generating_questions")
            await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        start_time = time.time()
        
        # Send progress update for LLM processing
        if self.ws_client and self.workflow_id:
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("llm_processing")
            await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        output = await self.replicate_client.async_run(
            self.model,
            input={
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 8000,
                "top_p": 0.9
            }
        )

        if isinstance(output, list):
            output_text = "\n".join(str(item) for item in output)
        else:
            output_text = str(output)

        # Send progress update for parsing
        if self.ws_client and self.workflow_id:
            progress_tracker = get_progress_tracker(self.workflow_id)
            progress_data = progress_tracker.get_progress_data("parsing_output")
            await self.ws_client.send_progress_update(self.workflow_id, progress_data)

        survey_data = self._extract_survey_json(output_text)

        return {
            "survey": survey_data,
            "generation_metadata": {
                "model": self.model,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "streaming_enabled": False,
                "sync_mode": True,
                "raw_response": output_text,
                "content_length": len(output_text)
            }
        }

    # ============================================================================
    # STREAMING ANALYSIS METHODS
    # ============================================================================

    async def _analyze_streaming_content(self, partial_content: str, elapsed_time: float = 0) -> None:
        """
        Analyze partial JSON content and send meaningful progress updates
        """
        try:
            # Extract meaningful data from partial content
            questions = self._extract_questions_from_partial(partial_content)
            sections = self._extract_sections_from_partial(partial_content)
            title = self._extract_title_from_partial(partial_content)

            # Determine current activity
            activity = self._determine_current_activity(partial_content, len(questions), len(sections), elapsed_time)

            # Calculate estimated progress
            estimated_progress = self._calculate_streaming_progress(len(questions), len(sections), elapsed_time)

            # Send detailed WebSocket update
            if self.ws_client and self.workflow_id:
                progress_tracker = get_progress_tracker(self.workflow_id)
                progress_data = progress_tracker.get_progress_data("llm_processing", "streaming")
                await self.ws_client.send_progress_update(self.workflow_id, {
                    "type": "llm_content_update",
                    "step": "llm_processing",
                    "percent": progress_data["percent"],
                    "data": {
                        "questionCount": len(questions),
                        "sectionCount": len(sections),
                        "currentActivity": activity,
                        "latestQuestions": [
                            {
                                "text": q.get("text", ""),
                                "type": q.get("type", "text"),
                                "hasOptions": len(q.get("options", [])) > 0
                            } for q in questions[-3:]  # Last 3 questions
                        ],
                        "currentSections": [
                            {
                                "title": s.get("title", ""),
                                "questionCount": len(s.get("questions", []))
                            } for s in sections
                        ],
                        "surveyTitle": title,
                        "estimatedProgress": estimated_progress,
                        "elapsedTime": elapsed_time
                    },
                    "message": f"Generated {len(questions)} questions across {len(sections)} sections"
                })
                logger.info(f"📊 [GenerationService] Streaming update sent: {len(questions)} questions, {len(sections)} sections")

        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Failed to analyze streaming content: {str(e)}")

    def _extract_questions_from_partial(self, partial_content: str) -> List[Dict[str, Any]]:
        """Extract question objects from partial JSON content"""
        questions = []

        try:
            # Look for complete question objects
            question_pattern = r'\{\s*"id"\s*:\s*"[^"]*"\s*,\s*"text"\s*:\s*"([^"]+)"\s*,\s*"type"\s*:\s*"([^"]*)"[^}]*\}'
            matches = re.finditer(question_pattern, partial_content, re.DOTALL)

            for match in matches:
                question_text = match.group(1)
                question_type = match.group(2)

                # Extract options if present
                question_obj = {
                    "text": question_text,
                    "type": question_type,
                    "options": []
                }

                # Look for options array near this question
                options_pattern = r'"options"\s*:\s*\[([^\]]*)\]'
                options_match = re.search(options_pattern, match.group(0))
                if options_match:
                    options_content = options_match.group(1)
                    options = re.findall(r'"([^"]*)"', options_content)
                    question_obj["options"] = options

                questions.append(question_obj)

        except Exception as e:
            logger.debug(f"Question extraction error: {e}")

        return questions

    def _extract_sections_from_partial(self, partial_content: str) -> List[Dict[str, Any]]:
        """Extract section objects from partial JSON content"""
        sections = []

        try:
            # Look for section objects with title and questions
            section_pattern = r'\{\s*"id"\s*:\s*[^,]*,\s*"title"\s*:\s*"([^"]+)"[^}]*"questions"\s*:\s*\[([^\]]*)\]'
            matches = re.finditer(section_pattern, partial_content, re.DOTALL)

            for match in matches:
                section_title = match.group(1)
                questions_content = match.group(2)

                # Count questions in this section
                question_count = len(re.findall(r'\{[^}]*"text"[^}]*\}', questions_content))

                sections.append({
                    "title": section_title,
                    "questions": [],  # Don't need full questions, just metadata
                    "questionCount": question_count
                })

        except Exception as e:
            logger.debug(f"Section extraction error: {e}")

        return sections

    def _extract_title_from_partial(self, partial_content: str) -> Optional[str]:
        """Extract survey title from partial JSON content"""
        try:
            title_match = re.search(r'"title"\s*:\s*"([^"]+)"', partial_content)
            return title_match.group(1) if title_match else None
        except Exception:
            return None

    def _determine_current_activity(self, content: str, question_count: int, section_count: int, elapsed_time: float) -> str:
        """Determine what the AI is currently working on based on content analysis"""

        # Check recent content (last 500 chars) for activity clues
        recent_content = content[-500:] if len(content) > 500 else content

        # Activity determination logic
        if elapsed_time < 5:
            return "Initializing survey generation..."
        elif '"title"' in content and '"description"' in content and question_count == 0:
            return "Creating survey title and description..."
        elif section_count == 0 and question_count == 0:
            return "Structuring survey framework..."
        elif section_count == 1 and question_count < 3:
            return "Generating opening questions..."
        elif '"options"' in recent_content:
            return "Adding multiple choice options..."
        elif question_count < 8:
            return f"Developing questions for section {section_count}..."
        elif '"type"' in recent_content:
            return "Configuring question types and validation..."
        elif question_count >= 8:
            return "Finalizing survey structure and metadata..."
        else:
            return f"Building comprehensive survey content..."

    def _calculate_streaming_progress(self, question_count: int, section_count: int, elapsed_time: float) -> float:
        """Calculate estimated progress within the LLM processing range using progress tracker"""

        # Import progress tracker
        from .progress_tracker import get_progress_tracker
        tracker = get_progress_tracker(self.workflow_id or "generation")

        # Get the LLM processing range from progress tracker
        llm_range = tracker.PROGRESS_RANGES.get("llm_processing", (35, 60))
        min_progress, max_progress = llm_range
        range_size = max_progress - min_progress

        # Calculate progress within the LLM processing range based on content
        content_factor = 0

        # Question count contribution (0-60% of range)
        if question_count > 0:
            # Assume target of ~15 questions for full survey
            question_factor = min(0.6, question_count / 15.0)
            content_factor += question_factor * 0.6

        # Section count contribution (0-20% of range)
        if section_count > 0:
            # Assume target of ~3-4 sections
            section_factor = min(0.2, section_count / 4.0)
            content_factor += section_factor * 0.2

        # Time-based progress (0-20% of range)
        # Assume typical generation takes 30-60 seconds
        time_factor = min(0.2, elapsed_time / 45.0)
        content_factor += time_factor * 0.2

        # Calculate final progress within the LLM processing range
        progress_within_range = min(1.0, content_factor)
        final_progress = min_progress + (progress_within_range * range_size)

        return min(max_progress, final_progress)