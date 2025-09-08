from typing import Dict, List, Any, Optional
from src.config import settings
from src.services.prompt_service import PromptService
from sqlalchemy.orm import Session
import replicate
import json


class GenerationService:
    def __init__(self, db_session: Optional[Session] = None) -> None:
        replicate.api_token = settings.replicate_api_token  # type: ignore
        self.model = settings.generation_model
        self.prompt_service = PromptService(db_session=db_session)
    
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
            # Build comprehensive prompt with rules and golden examples
            prompt = self.prompt_service.build_golden_enhanced_prompt(
                context=context,
                golden_examples=golden_examples,
                methodology_blocks=methodology_blocks,
                custom_rules=custom_rules
            )
            
            output = await replicate.async_run(
                self.model,
                input={
                    "prompt": prompt,
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "top_p": 0.9
                }
            )
            
            # Handle different output formats from Replicate
            if isinstance(output, list):
                survey_text = "".join(output)
            else:
                survey_text = str(output)
            survey_json = self._extract_survey_json(survey_text)
            
            return survey_json
            
        except Exception as e:
            raise Exception(f"Survey generation failed: {str(e)}")
    
    
    def _extract_survey_json(self, response_text: str) -> Dict[str, Any]:
        """
        Extract and validate survey JSON from response text
        """
        try:
            # Find JSON block in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            survey_json = json.loads(json_text)
            
            # Basic validation
            if not isinstance(survey_json, dict):
                raise ValueError("Survey must be a JSON object")
            
            if "questions" not in survey_json:
                raise ValueError("Survey must contain 'questions' field")
            
            if not isinstance(survey_json["questions"], list):
                raise ValueError("Questions must be a list")
            
            return survey_json
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in survey response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract survey JSON: {str(e)}")