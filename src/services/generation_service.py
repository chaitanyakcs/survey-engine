from typing import Dict, List, Any, Optional
from src.config import settings
from src.services.prompt_service import PromptService
from src.services.pillar_scoring_service import PillarScoringService
import sys
import os

# Add evaluations directory to path for advanced evaluators
current_dir = os.path.dirname(__file__)
project_root = current_dir
while project_root != '/' and project_root != '':
    eval_path = os.path.join(project_root, 'evaluations')
    if os.path.exists(eval_path):
        break
    project_root = os.path.dirname(project_root)

if os.path.exists(eval_path):
    sys.path.insert(0, eval_path)
    try:
        from modules.pillar_based_evaluator import PillarBasedEvaluator
        ADVANCED_EVALUATOR_AVAILABLE = True
    except ImportError as e:
        ADVANCED_EVALUATOR_AVAILABLE = False
        print(f"⚠️ Advanced evaluator not available: {e}")
else:
    ADVANCED_EVALUATOR_AVAILABLE = False
from src.utils.error_messages import UserFriendlyError, get_api_configuration_error
from src.utils.survey_utils import get_questions_count
from sqlalchemy.orm import Session
import replicate
import json
import logging

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, db_session: Optional[Session] = None) -> None:
        self.db_session = db_session  # Store the database session
        self.model = settings.generation_model
        self.prompt_service = PromptService(db_session=db_session)
        self.pillar_scoring_service = PillarScoringService(db_session=db_session)
        if ADVANCED_EVALUATOR_AVAILABLE:
            self.advanced_evaluator = PillarBasedEvaluator(llm_client=None, db_session=db_session)
        else:
            self.advanced_evaluator = None
        
        logger.info(f"🔧 [GenerationService] Initializing with model: {self.model}")
        logger.info(f"🔧 [GenerationService] Advanced evaluator available: {ADVANCED_EVALUATOR_AVAILABLE}")
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
            
            # Store system prompt in audit table
            await self._store_system_prompt_audit(
                survey_id=context.get('survey_id'),
                rfq_id=context.get('rfq_id'),
                system_prompt=prompt,
                generation_context={
                    'golden_examples_count': len(golden_examples) if golden_examples else 0,
                    'methodology_blocks_count': len(methodology_blocks) if methodology_blocks else 0,
                    'custom_rules_count': len(custom_rules.get('rules', [])) if custom_rules else 0,
                    'context_keys': list(context.keys()) if context else []
                }
            )
            
            logger.info("🌐 [GenerationService] Making API call to Replicate...")
            logger.info(f"🌐 [GenerationService] Model: {self.model}")
            logger.info(f"🌐 [GenerationService] API token set: {bool(replicate.api_token)}")
            
            try:
                output = await replicate.async_run(
                    self.model,
                    input={
                        "prompt": prompt,
                        "temperature": 0.7,
                        "max_tokens": 4000,
                        "top_p": 0.9
                    }
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
            
            # Evaluate survey using advanced pillar evaluation
            logger.info("🏛️ [GenerationService] Evaluating survey using advanced chain-of-thought evaluation...")
            pillar_scores = await self._evaluate_with_advanced_system(survey_json, context.get('rfq_text', ''))
            
            final_question_count = get_questions_count(survey_json)
            logger.info(f"🎉 [GenerationService] Successfully generated survey with {final_question_count} questions")
            logger.info(f"🎉 [GenerationService] Survey keys: {list(survey_json.keys())}")
            logger.info(f"🏛️ [GenerationService] Pillar adherence score: {pillar_scores['overall_grade']} ({pillar_scores['weighted_score']:.1%})")

            # Log final extraction summary
            self._log_final_extraction_summary(survey_json, survey_text)
            
            return {
                "survey": survey_json,
                "pillar_scores": {
                    "overall_grade": pillar_scores["overall_grade"],
                    "weighted_score": pillar_scores["weighted_score"],
                    "total_score": pillar_scores["total_score"],
                    "summary": pillar_scores["summary"],
                    "pillar_breakdown": pillar_scores["pillar_breakdown"],
                    "recommendations": pillar_scores["recommendations"]
                }
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

        logger.info("🔍 [GenerationService] === QUESTION EXTRACTION TRACKING ===")

        # Multiple question patterns
        patterns = [
            ("Complete ID+Text objects", r'\{\s*"id"\s*:\s*"([^"]*)"[^}]*"text"\s*:\s*"([^"]*)"[^}]*\}'),
            ("Complete Text+ID objects", r'\{\s*"text"\s*:\s*"([^"]*)"[^}]*"id"\s*:\s*"([^"]*)"[^}]*\}'),
            ("Partial ID+Text patterns", r'"id"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"text"\s*:\s*"([^"]*)"'),
            ("Partial Text+ID patterns", r'"text"\s*:\s*"([^"]*)"[^,}]*,?[^,}]*"id"\s*:\s*"([^"]*)"'),
        ]

        all_matches = []
        questions = []
        dropped_questions = []

        for i, (pattern_name, pattern) in enumerate(patterns):
            matches = list(re.finditer(pattern, text, re.DOTALL))
            logger.info(f"🔍 [GenerationService] Pattern '{pattern_name}': {len(matches)} matches found")

            for match in matches:
                if i < 2:  # First two patterns have different group orders
                    q_id = match.group(1) if i == 0 else match.group(2)
                    q_text = match.group(2) if i == 0 else match.group(1)
                else:
                    q_id = match.group(1) if i == 2 else match.group(2)
                    q_text = match.group(2) if i == 2 else match.group(1)

                # Clean the text
                original_text = q_text
                q_text = re.sub(r'\\n', ' ', q_text)
                q_text = re.sub(r'\s+', ' ', q_text).strip()

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

    def _extract_balanced_json(self, response_text: str) -> Optional[str]:
        """
        Extract JSON using balanced brace counting to find a complete JSON object
        """
        try:
            # Find the first opening brace
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None

            # Count braces to find the matching closing brace
            brace_count = 0
            in_string = False
            escape_next = False

            for i in range(start_idx, len(response_text)):
                char = response_text[i]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\' and in_string:
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

                        if brace_count == 0:
                            # Found the matching closing brace
                            end_idx = i + 1
                            json_text = response_text[start_idx:end_idx]
                            logger.info(f"🔍 [GenerationService] Balanced JSON extraction: {len(json_text)} characters")
                            return json_text

            # If we get here, braces weren't balanced
            logger.warning("⚠️ [GenerationService] Could not find balanced JSON braces")
            return None

        except Exception as e:
            logger.warning(f"⚠️ [GenerationService] Balanced JSON extraction failed: {str(e)}")
            return None

    def _repair_json_simple(self, json_text: str) -> Optional[str]:
        """
        Simple JSON repair focusing on the most common LLM errors
        """
        try:
            import re

            logger.info(f"🔧 [GenerationService] Starting simple JSON repair")
            original_text = json_text

            # 1. Remove any non-printable characters that can break JSON
            json_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', json_text)

            # 2. Fix missing commas between array elements (most common issue)
            # Pattern: "text"\n\s*"text" -> "text",\n\s*"text"
            json_text = re.sub(r'("[^"]*")\s*\n\s*("[^"]*")', r'\1,\n        \2', json_text)

            # 3. Fix missing commas between object properties
            # Pattern: "key": "value"\n\s*"key2" -> "key": "value",\n\s*"key2"
            json_text = re.sub(r'("[^"]*":\s*"[^"]*")\s*\n\s*"', r'\1,\n        "', json_text)

            # 4. Fix missing commas after objects in arrays
            # Pattern: }\n\s*{ -> },\n\s*{
            json_text = re.sub(r'}\s*\n\s*{', '},\n        {', json_text)

            # 5. Fix missing commas after closing brackets/braces
            # Pattern: ]\n\s*"key" -> ],\n\s*"key"
            json_text = re.sub(r']\s*\n\s*"', '],\n        "', json_text)
            json_text = re.sub(r'}\s*\n\s*"', '},\n        "', json_text)

            # 6. Remove trailing commas
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

            if json_text != original_text:
                logger.info(f"🔧 [GenerationService] Applied simple JSON repairs")
                # Test if the repair worked
                try:
                    json.loads(json_text)
                    logger.info(f"✅ [GenerationService] Simple JSON repair successful")
                    return json_text
                except json.JSONDecodeError as test_error:
                    logger.warning(f"⚠️ [GenerationService] Simple repair still invalid: {str(test_error)}")
                    return None
            else:
                logger.warning(f"⚠️ [GenerationService] No simple repairs applied")
                return None

        except Exception as e:
            logger.error(f"❌ [GenerationService] Simple JSON repair failed: {str(e)}")
            return None

    def _repair_json(self, json_text: str) -> str:
        """Attempt to repair common JSON formatting issues from LLM responses"""
        try:
            import re
            
            # Store original for logging
            original_text = json_text
            
            # First, clean control characters that can break JSON parsing
            json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)
            
            # Common repairs for LLM-generated JSON
            
            # 1. Fix missing commas between array elements (most common issue)
            # Look for patterns like: "text"\n\s*"text" and add comma (but not between object keys)
            # Only match when the first quote is a value (after a colon) or in array context
            json_text = re.sub(r'(":\s*"[^"]*")\s*\n\s*"', r'\1,\n            "', json_text)
            
            # 1b. More specific fix for the error we're seeing: missing comma after quoted string
            # Look for patterns like: "text"\n\s*] or "text"\n\s*} (but not after opening braces)
            json_text = re.sub(r'"[^"]*"\s*\n\s*([}\]])', r'",\n          \1', json_text)
            
            # 1c. Fix missing commas in arrays with mixed content
            # Look for patterns like: "text"\n\s*[0-9] or "text"\n\s*{ (but not after opening braces)
            json_text = re.sub(r'"[^"]*"\s*\n\s*([0-9{])', r'",\n            \1', json_text)
            
            # 2. Fix missing commas between object properties
            # Look for patterns like: }\n\s*"property" and add comma  
            json_text = re.sub(r'}\s*\n\s*"', '},\n        "', json_text)
            
            # 3. Fix missing commas between array elements (numbers and strings)
            # Look for patterns like: 5\n\s*"text" and add comma
            json_text = re.sub(r'(\d+)\s*\n\s*"', r'\1,\n            "', json_text)
            
            # 3b. Fix missing commas between string elements in arrays (specific to our error)
            # Look for line breaks in array context: "text"\n followed by whitespace and another "text"
            json_text = re.sub(r'("[^"]*")\s*\n\s*("[^"]*")', r'\1,\n            \2', json_text)
            
            # 4. Fix missing commas after closing arrays/objects
            # Look for patterns like: ]\n\s*"property" and add comma
            json_text = re.sub(r']\s*\n\s*"', '],\n        "', json_text)
            
            # 5. Fix missing commas between object properties in arrays
            # Look for patterns like: }\n\s*{ and add comma
            json_text = re.sub(r'}\s*\n\s*{', '},\n        {', json_text)
            
            # 6. Fix missing commas between array elements with objects
            # Look for patterns like: }\n\s*" and add comma
            json_text = re.sub(r'}\s*\n\s*"', '},\n        "', json_text)
            
            # 7. Fix trailing commas that might break parsing
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # 8. Fix common quote issues
            json_text = re.sub(r'([^"\\])"([^",:}\]\s])', r'\1"\2', json_text)
            
            # 9. Fix missing commas after quoted string values (most specific first)
            # Look for patterns like: "key": "value"\n\s*"key2" (missing comma after string value)
            json_text = re.sub(r'("[^"]*":\s*"[^"]*")\s*\n\s*"', r'\1,\n        "', json_text)
            
            
            # 10. Fix missing commas after boolean/null values
            json_text = re.sub(r'(true|false|null)\s*\n\s*"', r'\1,\n        "', json_text)
            
            logger.debug(f"🔍 [GenerationService] JSON repair check: original_text == json_text: {original_text == json_text}")
            logger.debug(f"🔍 [GenerationService] Original length: {len(original_text)}, Repaired length: {len(json_text)}")
            
            if json_text != original_text:
                logger.info(f"🔧 [GenerationService] Applied JSON repairs")
                logger.debug(f"🔧 [GenerationService] Original: {original_text[:500]}...")
                logger.debug(f"🔧 [GenerationService] Repaired: {json_text[:500]}...")
                
                # Test if the repair worked
                try:
                    json.loads(json_text)
                    logger.info(f"✅ [GenerationService] JSON repair validation successful")
                    return json_text
                except json.JSONDecodeError as test_error:
                    logger.warning(f"⚠️ [GenerationService] Repaired JSON still invalid: {str(test_error)}")
                    logger.debug(f"🔍 [GenerationService] Repair validation error: line {test_error.lineno}, column {test_error.colno}")
                    # Try one more aggressive repair pass
                    return self._aggressive_json_repair(json_text)
            else:
                logger.warning(f"⚠️ [GenerationService] No repairs applied to JSON")
                logger.debug(f"🔍 [GenerationService] Original text: {original_text[:200]}...")
                logger.debug(f"🔍 [GenerationService] Repaired text: {json_text[:200]}...")
                return None
                
        except Exception as repair_error:
            logger.error(f"❌ [GenerationService] JSON repair failed: {str(repair_error)}")
            return None
    
    def _aggressive_json_repair(self, json_text: str) -> str:
        """More aggressive JSON repair for difficult cases"""
        try:
            import re
            
            # Try to find and fix the specific error pattern
            # Look for missing commas in array contexts
            lines = json_text.split('\n')
            repaired_lines = []
            
            for i, line in enumerate(lines):
                repaired_lines.append(line)
                
                # Check if next line starts a new array element or object property
                if i < len(lines) - 1:
                    next_line = lines[i + 1].strip()
                    current_line = line.strip()
                    
                    # If current line ends with quote and next line starts with quote (missing comma)
                    if (current_line.endswith('"') and 
                        next_line.startswith('"') and 
                        not current_line.endswith('",') and
                        not current_line.endswith('":')):
                        # Add comma to current line
                        repaired_lines[-1] = line.rstrip() + ','
                        logger.info(f"🔧 [GenerationService] Added missing comma at line {i+1}")
                    
                    # If current line ends with } and next line starts with " (missing comma)
                    elif (current_line.endswith('}') and 
                          next_line.startswith('"') and 
                          not current_line.endswith('},')):
                        repaired_lines[-1] = line.rstrip() + ','
                        logger.info(f"🔧 [GenerationService] Added missing comma at line {i+1}")
                    
                    # If current line ends with " and next line starts with " (missing comma between properties)
                    elif (current_line.endswith('"') and 
                          next_line.startswith('"') and 
                          not current_line.endswith('",') and
                          not current_line.endswith('":') and
                          ':' in current_line):
                        repaired_lines[-1] = line.rstrip() + ','
                        logger.info(f"🔧 [GenerationService] Added missing comma between properties at line {i+1}")
                    
                    # If current line ends with a value and next line starts with " (missing comma)
                    elif (next_line.startswith('"') and 
                          not current_line.endswith(',') and
                          not current_line.endswith('{') and
                          not current_line.endswith('[') and
                          ':' in current_line):
                        repaired_lines[-1] = line.rstrip() + ','
                        logger.info(f"🔧 [GenerationService] Added missing comma after value at line {i+1}")
            
            repaired_text = '\n'.join(repaired_lines)
            
            # Test the aggressive repair
            try:
                json.loads(repaired_text)
                logger.info(f"🔧 [GenerationService] Aggressive repair successful")
                return repaired_text
            except json.JSONDecodeError:
                logger.warning(f"⚠️ [GenerationService] Aggressive repair also failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ [GenerationService] Aggressive repair failed: {str(e)}")
            return None

    def _extract_partial_survey(self, json_text: str) -> Optional[Dict[str, Any]]:
        """Fallback method to extract partial survey data from malformed JSON"""
        try:
            import re
            
            logger.info(f"🔧 [GenerationService] Attempting fallback partial extraction")
            
            # Try to extract basic survey structure even if JSON is incomplete
            survey = {
                "title": "Generated Survey",
                "description": "AI-generated survey (partial extraction)",
                "sections": []
            }
            
            # Extract title if present
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', json_text)
            if title_match:
                survey["title"] = title_match.group(1)
            
            # Extract description if present
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', json_text)
            if desc_match:
                survey["description"] = desc_match.group(1)
            
            # Check if we have sections format
            sections_match = re.search(r'"sections"\s*:\s*\[', json_text)
            if sections_match:
                # Try to extract sections
                logger.info("🔧 [GenerationService] Attempting to extract sections format")
                survey["sections"] = self._extract_sections_fallback(json_text)
            else:
                # Fall back to legacy questions format
                logger.info("🔧 [GenerationService] Attempting to extract legacy questions format")
                questions = self._extract_questions_fallback(json_text)
                if questions:
                    # Convert to sections format
                    survey["sections"] = [{
                        "id": 1,
                        "title": "Survey Questions",
                        "description": "All survey questions",
                        "questions": questions
                    }]
            
            if len(survey["sections"]) > 0:
                total_questions = sum(len(section.get("questions", [])) for section in survey["sections"])
                logger.info(f"🔧 [GenerationService] Fallback extraction found {len(survey['sections'])} sections with {total_questions} questions")
                return survey
            else:
                logger.warning(f"⚠️ [GenerationService] Fallback extraction found no sections or questions")
                return None
                
        except Exception as e:
            logger.error(f"❌ [GenerationService] Fallback extraction failed: {str(e)}")
            return None
    
    def _extract_sections_fallback(self, json_text: str) -> List[Dict[str, Any]]:
        """Extract sections from malformed JSON"""
        import re
        
        sections = []
        logger.info(f"🔍 [GenerationService] Extracting sections from JSON text (length: {len(json_text)})")
        
        # More flexible pattern to find sections - look for the section structure
        # This pattern looks for: {"id": number, ... "title": "...", ... "questions": [...]}
        section_pattern = r'\{\s*"id"\s*:\s*(\d+).*?"title"\s*:\s*"([^"]*)".*?"questions"\s*:\s*\[(.*?)\](?=\s*[,}])'
        section_matches = re.finditer(section_pattern, json_text, re.DOTALL)
        
        logger.info(f"🔍 [GenerationService] Found {len(list(re.finditer(section_pattern, json_text, re.DOTALL)))} section matches")
        
        for i, match in enumerate(section_matches):
            section_id = int(match.group(1))
            section_title = match.group(2)
            questions_text = match.group(3)
            
            logger.info(f"🔍 [GenerationService] Processing section {i+1}: id={section_id}, title='{section_title}'")
            logger.info(f"🔍 [GenerationService] Questions text length: {len(questions_text)}")
            logger.info(f"🔍 [GenerationService] Questions text preview: {questions_text[:200]}...")
            
            # Extract questions from this section
            questions = self._extract_questions_from_text(questions_text)
            logger.info(f"🔍 [GenerationService] Extracted {len(questions)} questions for section {section_id}")
            
            sections.append({
                "id": section_id,
                "title": section_title,
                "description": f"Section {section_id}",
                "questions": questions
            })
        
        logger.info(f"🔍 [GenerationService] Total sections extracted: {len(sections)}")
        return sections
    
    def _extract_questions_fallback(self, json_text: str) -> List[Dict[str, Any]]:
        """Extract questions from malformed JSON (legacy format)"""
        return self._extract_questions_from_text(json_text)
    
    def _extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract questions from text using regex patterns"""
        import re
        
        questions = []
        logger.info(f"🔍 [GenerationService] Extracting questions from text (length: {len(text)})")
        
        # Try multiple parsing strategies to maximize question extraction
        import json
        
        # Strategy 1: Use a more sophisticated approach to find JSON objects
        logger.info("🔍 [GenerationService] Strategy 1: Looking for JSON objects with question structure...")

        # Try to extract all JSON objects first, then filter for questions
        json_objects = self._extract_all_json_objects(text)
        logger.info(f"🔍 [GenerationService] Found {len(json_objects)} potential JSON objects")

        complete_matches = []
        for i, obj_text in enumerate(json_objects):
            try:
                obj = json.loads(obj_text)
                if isinstance(obj, dict) and 'id' in obj and 'text' in obj:
                    complete_matches.append((obj_text, obj))
                    logger.info(f"🔍 [GenerationService] Valid question object {i+1}: id='{obj.get('id')}', text='{str(obj.get('text'))[:50]}...'")
            except json.JSONDecodeError:
                continue

        logger.info(f"🔍 [GenerationService] Found {len(complete_matches)} valid question objects")

        for i, (match_text, question_json) in enumerate(complete_matches):
            try:
                logger.info(f"🔍 [GenerationService] Processing question {i+1}: {match_text[:100]}...")
                logger.info(f"🔍 [GenerationService] Parsed JSON keys: {list(question_json.keys())}")

                question_id = question_json['id']
                question_text = question_json['text']

                logger.info(f"✅ [GenerationService] Successfully parsed question {i+1}: id='{question_id}', text='{question_text[:50]}...'")

                # Create question object with all available fields
                question_obj = {
                    "id": question_id or f"q{i+1}",
                    "text": question_text,
                    "type": question_json.get("type", "text"),
                    "required": question_json.get("required", True),
                    "order": len(questions) + 1
                }

                # Add other fields if present
                if "options" in question_json:
                    question_obj["options"] = question_json["options"]
                if "scale_labels" in question_json:
                    question_obj["scale_labels"] = question_json["scale_labels"]
                if "category" in question_json:
                    question_obj["category"] = question_json["category"]
                if "methodology" in question_json:
                    question_obj["methodology"] = question_json["methodology"]
                if "ai_rationale" in question_json:
                    question_obj["ai_rationale"] = question_json["ai_rationale"]

                questions.append(question_obj)

            except Exception as e:
                logger.warning(f"⚠️ [GenerationService] Error processing question {i+1}: {e}")
                continue
        
        # Strategy 2: Look for any JSON objects that might contain questions
        if len(questions) == 0:
            logger.info("🔍 [GenerationService] Strategy 2: Looking for any JSON objects...")
            # More flexible pattern - any JSON object
            any_json_pattern = r'\{[^{}]*\}'
            any_matches = list(re.finditer(any_json_pattern, text, re.DOTALL))
            logger.info(f"🔍 [GenerationService] Found {len(any_matches)} potential JSON objects")
            
            for i, match in enumerate(any_matches):
                try:
                    match_text = match.group(0)
                    logger.info(f"🔍 [GenerationService] Processing any JSON {i+1}: {match_text[:100]}...")
                    question_json = json.loads(match_text)
                    logger.info(f"🔍 [GenerationService] Parsed JSON keys: {list(question_json.keys())}")
                    
                    # Check if this looks like a question (has text field)
                    if 'text' in question_json and question_json['text']:
                        question_id = question_json.get('id', f"q{len(questions) + 1}")
                        question_text = question_json['text']
                        
                        logger.info(f"✅ [GenerationService] Successfully parsed question from any JSON {i+1}: id='{question_id}', text='{question_text[:50]}...'")
                        
                        # Create question object
                        question_obj = {
                            "id": question_id,
                            "text": question_text,
                            "type": question_json.get("type", "text"),
                            "required": question_json.get("required", True),
                            "order": len(questions) + 1
                        }
                        
                        # Add other fields if present
                        if "options" in question_json:
                            question_obj["options"] = question_json["options"]
                        if "scale_labels" in question_json:
                            question_obj["scale_labels"] = question_json["scale_labels"]
                        if "category" in question_json:
                            question_obj["category"] = question_json["category"]
                        if "methodology" in question_json:
                            question_obj["methodology"] = question_json["methodology"]
                        if "ai_rationale" in question_json:
                            question_obj["ai_rationale"] = question_json["ai_rationale"]
                        
                        questions.append(question_obj)
                    else:
                        logger.debug(f"🔍 [GenerationService] Any JSON {i+1} doesn't look like a question: {list(question_json.keys())}")
                        
                except json.JSONDecodeError as e:
                    logger.debug(f"🔍 [GenerationService] Any JSON {i+1} not valid JSON: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ [GenerationService] Error processing any JSON {i+1}: {e}")
                    continue
        
        # Strategy 3: Fallback to regex if no questions found
        if len(questions) == 0:
            logger.info("🔍 [GenerationService] Strategy 3: Fallback to regex pattern matching...")
            question_pattern = r'\{\s*"id"\s*:\s*"([^"]*)".*?"text"\s*:\s*"([^"]*)".*?\}'
            question_matches = re.finditer(question_pattern, text, re.DOTALL)
            
            for i, match in enumerate(question_matches):
                question_id = match.group(1)
                question_text = match.group(2)
                
                logger.info(f"✅ [GenerationService] Successfully parsed question via regex {i+1}: id='{question_id}', text='{question_text[:50]}...'")
                
                question_obj = {
                    "id": question_id or f"q{i+1}",
                    "text": question_text,
                    "type": "text",  # Default to text type
                    "required": True,
                    "order": len(questions) + 1
                }
                
                # Try to extract question type if present
                type_match = re.search(r'"type"\s*:\s*"([^"]*)"', match.group(0))
                if type_match:
                    question_obj["type"] = type_match.group(1)
                
                questions.append(question_obj)
        
        logger.info(f"🔍 [GenerationService] Total questions extracted: {len(questions)}")
        
        # Log summary of extracted questions
        if len(questions) > 0:
            logger.info(f"✅ [GenerationService] Successfully extracted questions:")
            for i, q in enumerate(questions):
                logger.info(f"  {i+1}. ID: {q.get('id', 'N/A')}, Text: {q.get('text', 'N/A')[:50]}..., Type: {q.get('type', 'N/A')}")
        else:
            logger.warning("⚠️ [GenerationService] No questions could be extracted from the response")
            logger.warning(f"⚠️ [GenerationService] Response text sample: {text[:500]}...")
        
        return questions

    def _extract_all_json_objects(self, text: str) -> List[str]:
        """
        Extract all potential JSON objects from text using balanced brace counting
        """
        json_objects = []
        i = 0

        while i < len(text):
            # Find the next opening brace
            start_idx = text.find('{', i)
            if start_idx == -1:
                break

            # Count braces to find the matching closing brace
            brace_count = 0
            in_string = False
            escape_next = False

            for j in range(start_idx, len(text)):
                char = text[j]

                if escape_next:
                    escape_next = False
                    continue

                if char == '\\' and in_string:
                    escape_next = True
                    continue

                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1

                        if brace_count == 0:
                            # Found the matching closing brace
                            end_idx = j + 1
                            json_candidate = text[start_idx:end_idx]
                            json_objects.append(json_candidate)
                            i = end_idx
                            break
            else:
                # No matching brace found, move past this opening brace
                i = start_idx + 1

        return json_objects

    def _calculate_pillar_grade(self, score: float) -> str:
        """Calculate letter grade for individual pillar score"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _compile_recommendations(self, pillar_scores) -> List[str]:
        """Compile recommendations from all pillar scores"""
        all_recommendations = []
        for score in pillar_scores:
            all_recommendations.extend(score.recommendations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    async def _evaluate_with_advanced_system(self, survey_data: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """
        Evaluate survey using the advanced chain-of-thought pillar evaluation system
        """
        if not self.advanced_evaluator:
            logger.warning("⚠️ [GenerationService] Advanced evaluator not available, calling pillar-scores API")
            # Call the pillar-scores API to get advanced evaluation
            return await self._call_pillar_scores_api(survey_data, rfq_text)
        
        logger.info("🚀 [GenerationService] Using advanced chain-of-thought evaluation")
        
        try:
            # Run advanced evaluation
            result = await self.advanced_evaluator.evaluate_survey(survey_data, rfq_text)
            
            # Convert advanced results to the format expected by the generation service
            pillar_breakdown = []
            
            # Map pillar scores to the expected format
            pillar_mapping = {
                'content_validity': 'Content Validity',
                'methodological_rigor': 'Methodological Rigor', 
                'clarity_comprehensibility': 'Clarity & Comprehensibility',
                'structural_coherence': 'Structural Coherence',
                'deployment_readiness': 'Deployment Readiness'
            }
            
            weights = self.advanced_evaluator.PILLAR_WEIGHTS
            
            for pillar_name, display_name in pillar_mapping.items():
                score = getattr(result.pillar_scores, pillar_name)
                weight = weights[pillar_name]
                weighted_score = score * weight
                
                # Convert score to criteria format for compatibility
                criteria_met = int(score * 10)  # Scale to 0-10
                total_criteria = 10
                
                # Calculate grade
                if score >= 0.9:
                    grade = "A"
                elif score >= 0.8:
                    grade = "B"
                elif score >= 0.7:
                    grade = "C"
                elif score >= 0.6:
                    grade = "D"
                else:
                    grade = "F"
                
                pillar_breakdown.append({
                    "pillar_name": pillar_name,
                    "display_name": display_name,
                    "score": score,
                    "weighted_score": weighted_score,
                    "weight": weight,
                    "criteria_met": criteria_met,
                    "total_criteria": total_criteria,
                    "grade": grade
                })
            
            # Calculate overall grade
            if result.overall_score >= 0.9:
                overall_grade = "A"
            elif result.overall_score >= 0.8:
                overall_grade = "B"
            elif result.overall_score >= 0.7:
                overall_grade = "C"
            elif result.overall_score >= 0.6:
                overall_grade = "D"
            else:
                overall_grade = "F"
            
            # Create summary with advanced evaluation indicator
            summary = f"Advanced Chain-of-Thought Analysis (v2.0-advanced-chain-of-thought) | Overall Score: {result.overall_score:.1%} (Grade {overall_grade})"
            
            # Return in the expected format
            return {
                "overall_grade": overall_grade,
                "weighted_score": result.overall_score,
                "total_score": result.overall_score,
                "summary": summary,
                "pillar_breakdown": pillar_breakdown,
                "recommendations": result.recommendations or []
            }
            
        except Exception as e:
            logger.error(f"❌ [GenerationService] Advanced evaluation failed: {str(e)}")
            logger.warning("⚠️ [GenerationService] Falling back to pillar-scores API")
            # Call the pillar-scores API as fallback
            return await self._call_pillar_scores_api(survey_data, rfq_text)
    
    async def _call_pillar_scores_api(self, survey_data: Dict[str, Any], rfq_text: str) -> Dict[str, Any]:
        """
        Call the pillar-scores API to get advanced evaluation results
        """
        try:
            # Import the pillar-scores API function directly
            from src.api.pillar_scores import _evaluate_with_advanced_system
            
            # Create a mock DB session from our existing one
            db_session = self.pillar_scoring_service.db_session
            
            # Call the advanced evaluation function
            result = await _evaluate_with_advanced_system(survey_data, rfq_text, db_session)
            
            # Convert the API response to the format expected by generation service
            return {
                "overall_grade": result.overall_grade,
                "weighted_score": result.weighted_score,
                "total_score": result.total_score,
                "summary": result.summary,
                "pillar_breakdown": [
                    {
                        "pillar_name": pillar.pillar_name,
                        "display_name": pillar.display_name,
                        "score": pillar.score,
                        "weighted_score": pillar.weighted_score,
                        "weight": pillar.weight,
                        "criteria_met": pillar.criteria_met,
                        "total_criteria": pillar.total_criteria,
                        "grade": pillar.grade
                    }
                    for pillar in result.pillar_breakdown
                ],
                "recommendations": result.recommendations
            }
            
        except Exception as e:
            logger.error(f"❌ [GenerationService] Failed to call pillar-scores API: {str(e)}")
            logger.warning("⚠️ [GenerationService] Final fallback to legacy evaluation")
            # Final fallback to legacy system
            legacy_result = self.pillar_scoring_service.evaluate_survey_pillars(survey_data)
            return {
                "overall_grade": legacy_result.overall_grade,
                "weighted_score": legacy_result.weighted_score,
                "total_score": legacy_result.total_score,
                "summary": f"Legacy Evaluation - {legacy_result.summary}",
                "pillar_breakdown": [
                    {
                        "pillar_name": score.pillar_name,
                        "display_name": score.pillar_name.replace('_', ' ').title().replace('Comprehensibility', '& Comprehensibility'),
                        "score": score.score,
                        "weighted_score": score.weighted_score,
                        "weight": score.weight,
                        "criteria_met": score.criteria_met,
                        "total_criteria": score.total_criteria,
                        "grade": self._calculate_pillar_grade(score.score)
                    }
                    for score in legacy_result.pillar_scores
                ],
                "recommendations": self._compile_recommendations(legacy_result.pillar_scores)
            }
    
    async def _store_system_prompt_audit(
        self,
        survey_id: Optional[str],
        rfq_id: Optional[str],
        system_prompt: str,
        generation_context: Dict[str, Any]
    ) -> None:
        """
        Store system prompt used for generation in audit table
        """
        try:
            if not self.db_session:
                logger.warning("⚠️ [GenerationService] No database session available for system prompt audit")
                return
            
            from src.database.models import SystemPromptAudit
            from uuid import UUID
            
            # Convert string IDs to UUIDs if they exist
            rfq_uuid = None
            if rfq_id:
                try:
                    rfq_uuid = UUID(rfq_id)
                except ValueError:
                    logger.warning(f"⚠️ [GenerationService] Invalid RFQ ID format: {rfq_id}")
            
            # Create audit record
            audit_record = SystemPromptAudit(
                survey_id=survey_id or "unknown",
                rfq_id=rfq_uuid,
                system_prompt=system_prompt,
                prompt_type="generation",
                model_version=self.model,
                generation_context=generation_context
            )
            
            self.db_session.add(audit_record)
            self.db_session.commit()
            
            logger.info(f"✅ [GenerationService] System prompt audit stored for survey: {survey_id}")
            
        except Exception as e:
            logger.error(f"❌ [GenerationService] Failed to store system prompt audit: {str(e)}")
            # Don't raise exception to avoid breaking generation flow
            if self.db_session:
                self.db_session.rollback()
    
    @staticmethod
    async def store_evaluation_prompt_audit(
        db_session,
        survey_id: str,
        rfq_id: Optional[str],
        system_prompt: str,
        prompt_type: str,
        model_version: str,
        evaluation_context: Dict[str, Any]
    ) -> None:
        """
        Store evaluation prompt used for pillar scoring in audit table
        """
        try:
            if not db_session:
                logger.warning("⚠️ [GenerationService] No database session available for evaluation prompt audit")
                return
            
            from src.database.models import SystemPromptAudit
            from uuid import UUID
            
            # Convert string IDs to UUIDs if they exist
            rfq_uuid = None
            if rfq_id:
                try:
                    rfq_uuid = UUID(rfq_id)
                except ValueError:
                    logger.warning(f"⚠️ [GenerationService] Invalid RFQ ID format: {rfq_id}")
            
            # Create audit record
            audit_record = SystemPromptAudit(
                survey_id=survey_id or "unknown",
                rfq_id=rfq_uuid,
                system_prompt=system_prompt,
                prompt_type=prompt_type,
                model_version=model_version,
                generation_context=evaluation_context
            )
            
            db_session.add(audit_record)
            db_session.commit()
            
            logger.info(f"✅ [GenerationService] Evaluation prompt audit stored for survey: {survey_id}, type: {prompt_type}")
            
        except Exception as e:
            logger.error(f"❌ [GenerationService] Failed to store evaluation prompt audit: {str(e)}")
            # Don't raise exception to avoid breaking evaluation flow
            if db_session:
                db_session.rollback()