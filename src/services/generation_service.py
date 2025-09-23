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

from src.utils.llm_audit_decorator import audit_llm_call, LLMAuditContext
from src.services.llm_audit_service import LLMAuditService

logger = logging.getLogger(__name__)


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

        replicate.api_token = settings.replicate_api_token  # type: ignore

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

            # Log the context details for debugging
            logger.info(f"🔍 [GenerationService] Context received:")
            logger.info(f"🔍 [GenerationService] Context type: {type(context)}")
            logger.info(f"🔍 [GenerationService] Context keys: {list(context.keys()) if context else 'None'}")
            logger.info(f"🔍 [GenerationService] Context survey_id: {context.get('survey_id') if context else 'None'}")
            logger.info(f"🔍 [GenerationService] Context rfq_id: {context.get('rfq_id') if context else 'None'}")
            logger.info(f"🔍 [GenerationService] Context workflow_id: {context.get('workflow_id') if context else 'None'}")

            async with LLMAuditContext(
                audit_service=audit_service,
                interaction_id=interaction_id,
                model_name=self.model,
                model_provider="replicate",
                purpose="survey_generation",
                input_prompt=prompt,
                context_type="generation",
                parent_workflow_id=context.get('workflow_id'),
                parent_survey_id=context.get('survey_id'),
                parent_rfq_id=context.get('rfq_id'),
                hyperparameters={
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                },
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
                    start_time = time.time()
                    output = await replicate.async_run(
                        self.model,
                        input={
                            "prompt": prompt,
                            "temperature": 0.7,
                            "max_tokens": 4000,
                            "top_p": 0.9
                        }
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Set output and metrics in audit context
                    if isinstance(output, list):
                        output_text = "\n".join(str(item) for item in output)
                    else:
                        output_text = str(output)

                    audit_context.set_output(
                        output_content=output_text,
                        input_tokens=len(prompt.split()) if prompt else 0,
                        output_tokens=len(output_text.split()) if output_text else 0
                    )

                    logger.info(f"✅ [GenerationService] Survey generation completed in {response_time_ms}ms")
                    logger.info(f"📊 [GenerationService] Output length: {len(output_text)} characters")

                    # Parse the generated survey
                    survey_data = self._extract_survey_json(output_text)

                    return {
                        "survey": survey_data,
                        "generation_metadata": {
                            "model": self.model,
                            "response_time_ms": response_time_ms,
                            "custom_prompt_used": bool(system_prompt),
                            "prompt_length": len(prompt)
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
            logger.info(f"🌐 [GenerationService] API token set: {bool(replicate.api_token)}")

            # Create audit context for this LLM interaction
            interaction_id = f"survey_generation_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session)

            logger.info(f"🔍 [GenerationService] Context received: {context}")
            logger.info(f"🔍 [GenerationService] Survey ID from context: {context.get('survey_id')}")
            logger.info(f"🔍 [GenerationService] Workflow ID from context: {context.get('workflow_id')}")
            logger.info(f"🔍 [GenerationService] RFQ ID from context: {context.get('rfq_id')}")

            async with LLMAuditContext(
                audit_service=audit_service,
                interaction_id=interaction_id,
                model_name=self.model,
                model_provider="replicate",
                purpose="survey_generation",
                input_prompt=prompt,
                context_type="generation",
                parent_workflow_id=context.get('workflow_id'),
                parent_survey_id=context.get('survey_id'),
                parent_rfq_id=context.get('rfq_id'),
                hyperparameters={
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                },
                metadata={
                    'golden_examples_count': len(golden_examples) if golden_examples else 0,
                    'methodology_blocks_count': len(methodology_blocks) if methodology_blocks else 0,
                    'custom_rules_count': len(custom_rules.get('rules', [])) if custom_rules else 0,
                    'context_keys': list(context.keys()) if context else []
                },
                tags=["survey", "generation", "replicate"]
            ) as audit_context:
                try:
                    start_time = time.time()
                    output = await replicate.async_run(
                        self.model,
                        input={
                            "prompt": prompt,
                            "temperature": 0.7,
                            "max_tokens": 4000,
                            "top_p": 0.9
                        }
                    )
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Set output and metrics in audit context
                    if isinstance(output, list):
                        output_content = "".join(output)
                    else:
                        output_content = str(output)

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

                logger.info(f"✅ [GenerationService] Received response from {self.model}")
                logger.info(f"📊 [GenerationService] Response type: {type(output)}")
                logger.info(f"📊 [GenerationService] Response content: {str(output)[:200]}...")

                # Handle different output formats from Replicate
                if isinstance(output, list):
                    survey_text = "".join(output)
                    logger.info(f"📝 [GenerationService] Joined list response, length: {len(survey_text)}")
                else:
                    survey_text = str(output)
                    logger.info(f"📝 [GenerationService] String response, length: {len(survey_text)}")

                logger.info(f"📊 [GenerationService] Final response length: {len(survey_text)} characters")
                logger.info(f"📊 [GenerationService] Response preview: {survey_text[:500]}...")

                # Log detailed JSON object count for debugging
                opening_braces = survey_text.count('{')
                closing_braces = survey_text.count('}')
                logger.info(f"🔍 [GenerationService] JSON structure analysis:")
                logger.info(f"🔍 [GenerationService] - Opening braces {{ : {opening_braces}")
                logger.info(f"🔍 [GenerationService] - Closing braces }} : {closing_braces}")
                logger.info(f"🔍 [GenerationService] - Brace balance: {opening_braces - closing_braces}")

                # Count potential question objects
                import re
                id_text_pairs = len([m for m in re.finditer(r'"id"[^}]*"text"', survey_text)])
                text_id_pairs = len([m for m in re.finditer(r'"text"[^}]*"id"', survey_text)])
                logger.info(f"🔍 [GenerationService] - Potential question patterns: {id_text_pairs + text_id_pairs}")

                # Track question extraction metrics
                self._log_question_extraction_metrics(survey_text)

                # Log the full response for debugging (but truncate if too long)
                if len(survey_text) > 2000:
                    logger.info(f"🔍 [GenerationService] Full LLM response (truncated): {survey_text[:2000]}...")
                    logger.info(f"🔍 [GenerationService] Response end: ...{survey_text[-500:]}")
                else:
                    logger.info(f"🔍 [GenerationService] Full LLM response: {survey_text}")

                # Check if response is empty or too short
                if not survey_text or len(survey_text.strip()) < 10:
                    logger.error("❌ [GenerationService] Empty or very short response from API")
                    logger.error(f"❌ [GenerationService] Response content: '{survey_text}'")
                    raise Exception("API returned empty or invalid response. Please check your API configuration and try again.")

                logger.info("🔍 [GenerationService] Extracting survey JSON...")
                survey_json = self._extract_survey_json(survey_text)

                final_question_count = get_questions_count(survey_json)
                logger.info(f"🎉 [GenerationService] Successfully generated survey with {final_question_count} questions")
                logger.info(f"🎉 [GenerationService] Survey keys: {list(survey_json.keys())}")

                # Log final extraction summary
                self._log_final_extraction_summary(survey_json, survey_text)

                return {
                    "survey": survey_json
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


    def _extract_survey_json(self, response_text: str) -> Dict[str, Any]:
        """
        Bulletproof JSON extraction with multiple fallback strategies
        """
        logger.info(f"🔍 [GenerationService] Starting bulletproof JSON extraction (length: {len(response_text)})")

        # Strategy 1: Clean JSON extraction with progressive fallbacks
        strategies = [
            ("Balanced JSON extraction", self._extract_balanced_json_robust),
            ("Cleaned balanced extraction", self._extract_cleaned_json),
            ("Progressive JSON repair", self._extract_with_progressive_repair),
            ("Force rebuild from parts", self._force_rebuild_survey_json)
        ]

        for strategy_name, extraction_func in strategies:
            try:
                logger.info(f"🔧 [GenerationService] Trying {strategy_name}...")
                result = extraction_func(response_text)
                if result:
                    logger.info(f"✅ [GenerationService] {strategy_name} succeeded!")
                    self._validate_and_fix_survey_structure(result)
                    return result
                else:
                    logger.warning(f"⚠️ [GenerationService] {strategy_name} returned None")
            except Exception as e:
                logger.warning(f"⚠️ [GenerationService] {strategy_name} failed: {str(e)}")
                continue

        # If all strategies fail, create a minimal valid survey
        logger.error("❌ [GenerationService] All JSON extraction strategies failed")
        return self._create_minimal_survey(response_text)

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

    def _extract_cleaned_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON after aggressive cleaning
        """
        try:
            import re

            # Remove common LLM artifacts
            cleaned = re.sub(r'^.*?```json\s*', '', response_text, flags=re.DOTALL)
            cleaned = re.sub(r'```.*$', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'^[^{]*', '', cleaned)
            cleaned = re.sub(r'[^}]*$', '}', cleaned)

            # Remove control characters
            cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)

            # Try to parse
            return json.loads(cleaned)
        except Exception:
            return None

    def _extract_with_progressive_repair(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Progressive repair approach - fix one issue at a time
        """
        try:
            import re

            # Extract potential JSON block
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx == -1 or end_idx <= start_idx:
                return None

            json_text = response_text[start_idx:end_idx]

            # Progressive repair steps
            repairs = [
                # Remove control characters
                lambda t: re.sub(r'[\x00-\x1f\x7f-\x9f]', '', t),
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

    def _force_rebuild_survey_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Force rebuild survey from extractable parts
        """
        try:
            import re

            logger.info("🔧 [GenerationService] Force rebuilding survey from parts")

            # Extract basic fields
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', response_text)
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', response_text)

            survey = {
                "title": title_match.group(1) if title_match else "Generated Survey",
                "description": desc_match.group(1) if desc_match else "AI-generated survey",
                "sections": []
            }

            # Try to extract sections or questions
            sections = self._extract_sections_by_force(response_text)
            if sections:
                survey["sections"] = sections
            else:
                # Fall back to extracting individual questions
                questions = self._extract_questions_by_force(response_text)
                if questions:
                    # Group questions intelligently instead of one big section
                    grouped_sections = self._group_questions_into_sections(questions)
                    survey["sections"] = grouped_sections

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
                section_id = int(match.group(1))
                section_title = match.group(2)
                questions_text = match.group(3)

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
        ]

        all_matches = []
        questions = []
        dropped_questions = []

        for i, (pattern_name, pattern) in enumerate(patterns):
            # Check timeout
            if time.time() - start_time > max_processing_time:
                logger.warning(f"⚠️ [GenerationService] Timeout reached after {max_processing_time}s, stopping question extraction")
                break

            matches = list(re.finditer(pattern, text, re.DOTALL))
            logger.info(f"🔍 [GenerationService] Pattern '{pattern_name}': {len(matches)} matches found")

            for match in matches:
                # Check timeout in inner loop too
                if time.time() - start_time > max_processing_time:
                    logger.warning(f"⚠️ [GenerationService] Timeout reached during pattern processing, stopping")
                    break
                if i < 2:  # First two patterns have different group orders
                    q_id = match.group(1) if i == 0 else match.group(2)
                    q_text = match.group(2) if i == 0 else match.group(1)
                else:
                    q_id = match.group(1) if i == 2 else match.group(2)
                    q_text = match.group(2) if i == 2 else match.group(1)

                # Clean the text - handle excessive newlines and formatting issues
                original_text = q_text
                # Remove escaped newlines and excessive whitespace
                q_text = re.sub(r'\\n', ' ', q_text)
                # Remove actual newlines and excessive whitespace
                q_text = re.sub(r'\n+', ' ', q_text)
                # Normalize all whitespace to single spaces
                q_text = re.sub(r'\s+', ' ', q_text).strip()
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
                    question = {
                        "id": q_id or f"q{len(questions) + 1}",
                        "text": q_text,
                        "type": "text",
                        "required": True,
                        "category": "general"
                    }
                    questions.append(question)

        logger.info(f"🔍 [GenerationService] Total matches found: {len(all_matches)}")
        logger.info(f"🔍 [GenerationService] Valid questions before dedup: {len(questions)}")
        logger.info(f"🔍 [GenerationService] Questions dropped (validation): {len(dropped_questions)}")

        # Remove duplicates based on text similarity
        unique_questions = []
        duplicate_count = 0

        for q in questions:
            is_duplicate = False
            for uq in unique_questions:
                if self._texts_similar(q["text"], uq["text"]):
                    is_duplicate = True
                    duplicate_count += 1
                    logger.info(f"🔍 [GenerationService] Duplicate found: '{q['id']}' similar to '{uq['id']}'")
                    break
            if not is_duplicate:
                unique_questions.append(q)

        logger.info(f"🔍 [GenerationService] Questions dropped (duplicates): {duplicate_count}")
        logger.info(f"✅ [GenerationService] Final unique questions: {len(unique_questions)}")

        # Log samples of dropped questions
        if dropped_questions:
            logger.info("❌ [GenerationService] Sample dropped questions:")
            for dropped in dropped_questions[:5]:  # Show first 5
                logger.info(f"❌ [GenerationService] - '{dropped['id']}': {dropped['reason']} | Text: '{dropped['text']}'")

        logger.info("🔍 [GenerationService] =====================================")

        return unique_questions

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
            "general": []
        }

        # Keywords to identify question types
        topic_keywords = {
            "demographics": ["age", "gender", "location", "education", "income", "occupation", "demographic"],
            "experience": ["experience", "how long", "previous", "background", "history", "used"],
            "satisfaction": ["satisfied", "happy", "pleased", "rating", "rate", "score", "scale"],
            "preferences": ["prefer", "favorite", "choose", "select", "like", "want", "desire"],
            "feedback": ["improve", "suggest", "feedback", "recommend", "opinion", "thoughts", "comment"]
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

        # Create sections from groups, but enforce minimum 2 questions per section
        sections = []
        section_id = 1
        leftover_questions = []

        title_map = {
            "demographics": "Demographics",
            "experience": "Background & Experience",
            "satisfaction": "Satisfaction & Rating",
            "preferences": "Preferences & Choices",
            "feedback": "Feedback & Suggestions",
            "general": "General Questions"
        }

        # Only create sections for groups with 2+ questions
        for topic, group_questions in topic_groups.items():
            if len(group_questions) >= 2:
                sections.append({
                    "id": section_id,
                    "title": title_map[topic],
                    "description": f"{title_map[topic].lower()} questions",
                    "questions": group_questions
                })
                section_id += 1
            else:
                # Add single questions to leftover pile
                leftover_questions.extend(group_questions)

        # If we have leftover questions, group them logically
        if leftover_questions:
            if len(sections) == 0:
                # No sections created yet, put all questions in one section
                sections.append({
                    "id": 1,
                    "title": "Survey Questions",
                    "description": "All survey questions",
                    "questions": leftover_questions
                })
            elif len(leftover_questions) >= 3:
                # Many leftovers, create a general section
                sections.append({
                    "id": section_id,
                    "title": "Additional Questions",
                    "description": "Additional survey questions",
                    "questions": leftover_questions
                })
            else:
                # Few leftovers, distribute to existing sections
                for i, question in enumerate(leftover_questions):
                    section_index = i % len(sections)
                    sections[section_index]["questions"].append(question)

        logger.info(f"🔧 [GenerationService] Grouped {len(questions)} questions into {len(sections)} logical sections")

        # Log section breakdown
        for section in sections:
            logger.info(f"🔧 [GenerationService] - {section['title']}: {len(section['questions'])} questions")

        return sections

    def _create_minimal_survey(self, response_text: str) -> Dict[str, Any]:
        """
        Create a minimal valid survey as absolute fallback
        """
        logger.warning("🔧 [GenerationService] Creating minimal survey as fallback")

        # Try one last time to extract any text that looks like questions
        import re
        question_texts = re.findall(r'"([^"]{20,200})"', response_text)

        questions = []
        for i, text in enumerate(question_texts[:10]):  # Max 10 questions
            if any(word in text.lower() for word in ['what', 'how', 'why', 'when', 'where', 'which', 'would', 'do', 'are', 'is']):
                questions.append({
                    "id": f"q{i+1}",
                    "text": text,
                    "type": "text",
                    "required": True,
                    "category": "general"
                })

        return {
            "title": "Generated Survey",
            "description": "Survey generated from response",
            "sections": [{
                "id": 1,
                "title": "Questions",
                "description": "Extracted questions",
                "questions": questions
            }] if questions else [],
            "estimated_time": 5,
            "confidence_score": 0.5,
            "methodologies": ["survey"],
            "golden_examples": [],
            "metadata": {"target_responses": 100, "methodology": ["survey"]}
        }