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
            
            logger.info(f"🎉 [GenerationService] Successfully generated survey with {get_questions_count(survey_json)} questions")
            logger.info(f"🎉 [GenerationService] Survey keys: {list(survey_json.keys())}")
            logger.info(f"🏛️ [GenerationService] Pillar adherence score: {pillar_scores['overall_grade']} ({pillar_scores['weighted_score']:.1%})")
            
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
        Extract and validate survey JSON from response text
        """
        try:
            logger.info(f"🔍 [GenerationService] Extracting JSON from response (length: {len(response_text)})")
            logger.info(f"🔍 [GenerationService] Response preview: {response_text[:500]}...")
            
            # Find JSON block in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("❌ [GenerationService] No JSON found in response")
                logger.error(f"❌ [GenerationService] Full response: {response_text}")
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            logger.info(f"🔍 [GenerationService] Extracted JSON text length: {len(json_text)}")
            logger.info(f"🔍 [GenerationService] Extracted JSON preview: {json_text[:500]}...")
            
            # Check if we can see sections in the JSON
            if '"sections"' in json_text:
                logger.info("✅ [GenerationService] Found 'sections' in JSON text")
                # Count sections
                sections_count = json_text.count('"id"')
                logger.info(f"🔍 [GenerationService] Found {sections_count} potential sections (by 'id' count)")
            else:
                logger.warning("⚠️ [GenerationService] No 'sections' found in JSON text")
            
            # Try to repair common JSON issues before parsing
            try:
                survey_json = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [GenerationService] Initial JSON parse failed, attempting repair: {str(e)}")
                logger.debug(f"🔍 [GenerationService] JSON error details: line {e.lineno}, column {e.colno}, position {e.pos}")
                
                # Try multiple repair strategies
                repaired_json = self._repair_json(json_text)
                if repaired_json:
                    try:
                        logger.info(f"🔧 [GenerationService] JSON repaired successfully")
                        survey_json = json.loads(repaired_json)
                    except json.JSONDecodeError as repair_error:
                        logger.error(f"❌ [GenerationService] Repaired JSON still invalid: {str(repair_error)}")
                        logger.debug(f"🔍 [GenerationService] Repair error details: line {repair_error.lineno}, column {repair_error.colno}")
                        # Try fallback extraction
                        survey_json = self._extract_partial_survey(json_text)
                        if survey_json:
                            logger.info(f"🔧 [GenerationService] Fallback extraction succeeded")
                        else:
                            logger.error(f"❌ [GenerationService] All JSON repair strategies failed")
                            raise e
                else:
                    # Try fallback extraction
                    survey_json = self._extract_partial_survey(json_text)
                    if survey_json:
                        logger.info(f"🔧 [GenerationService] Fallback extraction succeeded")
                    else:
                        logger.error(f"❌ [GenerationService] All JSON repair strategies failed")
                        raise e
            logger.info(f"✅ [GenerationService] Successfully parsed JSON with keys: {list(survey_json.keys())}")
            
            # Basic validation
            if not isinstance(survey_json, dict):
                raise ValueError("Survey must be a JSON object")
            
            # Check for sections format (preferred) or questions format (legacy)
            has_sections = "sections" in survey_json
            has_questions = "questions" in survey_json
            
            if has_sections and has_questions:
                logger.warning("⚠️ [GenerationService] Survey has both 'sections' and 'questions' fields, using sections format")
                # Remove questions field to avoid confusion
                del survey_json["questions"]
            elif has_sections:
                logger.info("✅ [GenerationService] Survey uses sections format")
                # Validate sections structure
                if not isinstance(survey_json["sections"], list):
                    raise ValueError("Sections must be a list")
            elif has_questions:
                logger.info("⚠️ [GenerationService] Survey uses legacy questions format")
                if not isinstance(survey_json["questions"], list):
                    raise ValueError("Questions must be a list")
            else:
                logger.warning("⚠️ [GenerationService] No 'sections' or 'questions' field found, creating empty sections list")
                survey_json["sections"] = []
            
            # Ensure we have at least some basic structure
            if not survey_json.get("title"):
                survey_json["title"] = "Generated Survey"
            if not survey_json.get("description"):
                survey_json["description"] = "AI-generated survey"
            
            logger.info(f"✅ [GenerationService] Final survey has {get_questions_count(survey_json)} questions")
            return survey_json
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [GenerationService] JSON decode error: {str(e)}")
            logger.error(f"❌ [GenerationService] Problematic JSON: {json_text if 'json_text' in locals() else 'N/A'}")
            raise ValueError(f"Invalid JSON in survey response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract survey JSON: {str(e)}")
    
    def _repair_json(self, json_text: str) -> str:
        """Attempt to repair common JSON formatting issues from LLM responses"""
        try:
            import re
            
            # Store original for logging
            original_text = json_text
            
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
        
        # Strategy 1: Look for complete question objects with both id and text
        logger.info("🔍 [GenerationService] Strategy 1: Looking for complete question objects...")
        complete_pattern = r'\{[^{}]*"id"[^{}]*"text"[^{}]*\}|\{[^{}]*"text"[^{}]*"id"[^{}]*\}'
        complete_matches = list(re.finditer(complete_pattern, text, re.DOTALL))
        logger.info(f"🔍 [GenerationService] Found {len(complete_matches)} complete question objects")
        
        for i, match in enumerate(complete_matches):
            try:
                match_text = match.group(0)
                logger.info(f"🔍 [GenerationService] Processing complete match {i+1}: {match_text[:100]}...")
                question_json = json.loads(match_text)
                logger.info(f"🔍 [GenerationService] Parsed JSON keys: {list(question_json.keys())}")
                
                if 'id' in question_json and 'text' in question_json:
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
                else:
                    logger.warning(f"⚠️ [GenerationService] Complete match {i+1} missing required fields: {list(question_json.keys())}")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [GenerationService] Failed to parse complete match {i+1}: {e}")
                continue
            except Exception as e:
                logger.warning(f"⚠️ [GenerationService] Error processing complete match {i+1}: {e}")
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