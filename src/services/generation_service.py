from typing import Dict, List, Any, Optional
from src.config import settings
from src.services.prompt_service import PromptService
from src.services.pillar_scoring_service import PillarScoringService
from src.utils.error_messages import UserFriendlyError, get_api_configuration_error
from sqlalchemy.orm import Session
import replicate
import json
import logging

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self, db_session: Optional[Session] = None) -> None:
        self.model = settings.generation_model
        self.prompt_service = PromptService(db_session=db_session)
        self.pillar_scoring_service = PillarScoringService(db_session=db_session)
        
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
            logger.info(f"📝 [GenerationService] Prompt preview (first 200 chars): {prompt[:200]}...")
            
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
            
            # Check if response is empty or too short
            if not survey_text or len(survey_text.strip()) < 10:
                logger.error("❌ [GenerationService] Empty or very short response from API")
                logger.error(f"❌ [GenerationService] Response content: '{survey_text}'")
                raise Exception("API returned empty or invalid response. Please check your API configuration and try again.")
            
            logger.info("🔍 [GenerationService] Extracting survey JSON...")
            survey_json = self._extract_survey_json(survey_text)
            
            # Evaluate survey against pillar rules
            logger.info("🏛️ [GenerationService] Evaluating survey against pillar rules...")
            pillar_scores = self.pillar_scoring_service.evaluate_survey_pillars(survey_json)
            
            logger.info(f"🎉 [GenerationService] Successfully generated survey with {len(survey_json.get('questions', []))} questions")
            logger.info(f"🎉 [GenerationService] Survey keys: {list(survey_json.keys())}")
            logger.info(f"🏛️ [GenerationService] Pillar adherence score: {pillar_scores.overall_grade} ({pillar_scores.weighted_score:.1%})")
            
            return {
                "survey": survey_json,
                "pillar_scores": {
                    "overall_grade": pillar_scores.overall_grade,
                    "weighted_score": pillar_scores.weighted_score,
                    "total_score": pillar_scores.total_score,
                    "summary": pillar_scores.summary,
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
                        for score in pillar_scores.pillar_scores
                    ],
                    "recommendations": self._compile_recommendations(pillar_scores.pillar_scores)
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
        Extract and validate survey JSON from response text
        """
        try:
            logger.info(f"🔍 [GenerationService] Extracting JSON from response (length: {len(response_text)})")
            logger.info(f"🔍 [GenerationService] Response preview: {response_text[:300]}...")
            
            # Find JSON block in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("❌ [GenerationService] No JSON found in response")
                logger.error(f"❌ [GenerationService] Full response: {response_text}")
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            logger.info(f"🔍 [GenerationService] Extracted JSON text: {json_text[:200]}...")
            
            survey_json = json.loads(json_text)
            logger.info(f"✅ [GenerationService] Successfully parsed JSON with keys: {list(survey_json.keys())}")
            
            # Basic validation
            if not isinstance(survey_json, dict):
                raise ValueError("Survey must be a JSON object")
            
            if "questions" not in survey_json:
                logger.warning("⚠️ [GenerationService] No 'questions' field found, creating empty questions list")
                survey_json["questions"] = []
            
            if not isinstance(survey_json["questions"], list):
                raise ValueError("Questions must be a list")
            
            # Ensure we have at least some basic structure
            if not survey_json.get("title"):
                survey_json["title"] = "Generated Survey"
            if not survey_json.get("description"):
                survey_json["description"] = "AI-generated survey"
            
            logger.info(f"✅ [GenerationService] Final survey has {len(survey_json.get('questions', []))} questions")
            return survey_json
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [GenerationService] JSON decode error: {str(e)}")
            logger.error(f"❌ [GenerationService] Problematic JSON: {json_text if 'json_text' in locals() else 'N/A'}")
            raise ValueError(f"Invalid JSON in survey response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract survey JSON: {str(e)}")
    
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