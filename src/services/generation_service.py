from typing import Dict, List, Any
from src.config import settings
import replicate
import json


class GenerationService:
    def __init__(self) -> None:
        replicate.api_token = settings.replicate_api_token  # type: ignore
        self.model = settings.generation_model
    
    async def generate_survey(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate survey using GPT with golden-enhanced prompts
        """
        try:
            # Build enhanced prompt with golden examples
            prompt = self._build_golden_enhanced_prompt(
                context=context,
                golden_examples=golden_examples,
                methodology_blocks=methodology_blocks
            )
            
            # Generate survey using Replicate GPT-5
            system_prompt = "You are an expert survey designer. Generate high-quality, researcher-ready surveys based on RFQs and golden standard examples."
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            output = await replicate.async_run(
                self.model,
                input={
                    "prompt": full_prompt,
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
    
    def _build_golden_enhanced_prompt(
        self,
        context: Dict[str, Any],
        golden_examples: List[Dict[str, Any]],
        methodology_blocks: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt with golden examples and methodology guidance
        """
        rfq_details = context.get("rfq_details", {})
        
        prompt_parts = [
            "GOLDEN STANDARD EXAMPLES:",
            ""
        ]
        
        # Add golden examples as few-shot prompts
        for i, example in enumerate(golden_examples[:settings.max_golden_examples], 1):
            prompt_parts.extend([
                f"Example {i}:",
                f"RFQ: {example['rfq_text'][:500]}...",
                f"Survey Structure: {json.dumps(example['survey_json'], indent=2)[:800]}...",
                f"Key Principles: Quality Score {example.get('quality_score', 'N/A')}, Methodology: {example.get('methodology_tags', [])}",
                ""
            ])
        
        # Add methodology guidance
        if methodology_blocks:
            prompt_parts.extend([
                "METHODOLOGY GUIDANCE:",
                ""
            ])
            for block in methodology_blocks:
                prompt_parts.extend([
                    f"- {block['methodology']}: {block['example_structure']}",
                    ""
                ])
        
        # Add current RFQ
        prompt_parts.extend([
            "CURRENT RFQ:",
            f"Title: {rfq_details.get('title', 'N/A')}",
            f"Description: {rfq_details.get('text', '')}",
            f"Category: {rfq_details.get('category', 'N/A')}",
            f"Target Segment: {rfq_details.get('segment', 'N/A')}",
            f"Research Goal: {rfq_details.get('goal', 'N/A')}",
            "",
            "REQUIREMENTS:",
            "- Generate a complete survey following golden quality standards",
            "- Include proper question types, flow, and methodology compliance",
            "- Return valid JSON with the following structure:",
            json.dumps({
                "title": "Survey Title",
                "description": "Survey Description", 
                "questions": [
                    {
                        "id": "q1",
                        "text": "Question text",
                        "type": "multiple_choice|text|scale|ranking",
                        "options": ["Option 1", "Option 2"],
                        "required": True,
                        "methodology": "screening|core|demographic"
                    }
                ],
                "metadata": {
                    "estimated_time": 10,
                    "methodology_tags": ["tag1", "tag2"],
                    "target_responses": 100
                }
            }, indent=2),
            "",
            "Generate the survey JSON now:"
        ])
        
        return "\n".join(prompt_parts)
    
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