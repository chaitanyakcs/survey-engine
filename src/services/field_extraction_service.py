"""AI-powered field extraction service for auto-populating golden example fields."""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

import replicate

from ..config.settings import settings
from ..services.logging_utils import log_service_configuration
from ..services.llm_audit_service import LLMAuditService
from ..utils.error_messages import UserFriendlyError, get_api_configuration_error
from ..utils.json_generation_utils import (
    get_json_optimized_hyperparameters,
    parse_llm_json_response,
)
from ..utils.llm_audit_decorator import LLMAuditContext

logger = logging.getLogger(__name__)

class FieldExtractionService:
    """Service for extracting and auto-populating golden example fields from RFQ and Survey content."""
    
    def __init__(self, db_session: Optional[Any] = None):
        log_service_configuration(
            logger,
            "FieldExtractionService",
            event="init",
            details={
                "has_db_session": bool(db_session),
                "configured_model": settings.generation_model,
                "replicate_token_configured": bool(settings.replicate_api_token),
            },
        )

        self.db_session = db_session
        
        # Initialize LLM provider
        self.provider_name = self._get_llm_provider()
        from src.services.llm_provider import create_llm_provider
        try:
            self.llm_provider = create_llm_provider(
                provider=self.provider_name,
                model=None  # Will use model from settings
            )
            logger.info(f"✅ [FieldExtractionService] Initialized {self.provider_name} provider")
        except Exception as e:
            logger.error(f"❌ [FieldExtractionService] Failed to initialize {self.provider_name} provider: {e}")
            error_info = get_api_configuration_error()
            raise UserFriendlyError(
                message=error_info["message"],
                technical_details=str(e),
                action_required="Configure AI service provider (Replicate or OpenAI)"
            )

    def _get_llm_provider(self) -> str:
        """Get LLM provider - default to replicate for field extraction"""
        try:
            if self.db_session:
                from src.services.settings_service import SettingsService
                settings_service = SettingsService(self.db_session)
                evaluation_settings = settings_service.get_evaluation_settings()
                
                if evaluation_settings and 'llm_provider' in evaluation_settings:
                    provider = evaluation_settings['llm_provider']
                    logger.debug(f"FieldExtractionService provider loaded from settings: {provider}")
                    return provider
            
            return settings.llm_provider
        except Exception as e:
            logger.warning(f"⚠️ [FieldExtractionService] Failed to get provider from settings: {e}, using default")
            return settings.llm_provider

        self.model = self._get_generation_model()

        logger.info(
            "FieldExtractionService ready",
            extra={"model": self.model, "has_db_session": bool(db_session)},
        )

        log_service_configuration(
            logger,
            "FieldExtractionService",
            event="ready",
            details={"model": self.model},
        )

    def _get_generation_model(self) -> str:
        """Get generation model from database settings or fallback to config"""
        try:
            log_service_configuration(
                logger,
                "FieldExtractionService",
                event="model_selection",
                details={
                    "has_db_session": bool(self.db_session),
                    "default_model": settings.generation_model,
                },
            )

            if self.db_session:
                from src.services.settings_service import SettingsService

                settings_service = SettingsService(self.db_session)
                evaluation_settings = settings_service.get_evaluation_settings()

                if evaluation_settings and 'generation_model' in evaluation_settings:
                    model = evaluation_settings['generation_model']
                    logger.info(
                        "FieldExtractionService model loaded from evaluation settings",
                        extra={"model": model},
                    )
                    return model
                logger.debug(
                    "FieldExtractionService falling back to configured model",
                    extra={"reason": "missing_db_setting"},
                )
                return settings.generation_model

            logger.debug(
                "FieldExtractionService using configured model",
                extra={"reason": "no_db_session"},
            )
            return settings.generation_model
        except Exception as e:
            logger.warning(
                f"⚠️ [FieldExtractionService] Failed to get model from database settings: {e}, using config default"
            )
            return settings.generation_model

    def create_field_extraction_prompt(self, rfq_text: str, survey_json: Dict[str, Any]) -> str:
        """Create prompt for extracting golden example fields."""
        
        # Convert survey JSON to readable format
        survey_summary = self._summarize_survey(survey_json)
        
        prompt = f"""You are an expert survey methodologist. Analyze the RFQ text and Survey JSON to extract and suggest appropriate values for golden example fields.

RFQ TEXT:
{rfq_text}

SURVEY SUMMARY:
{survey_summary}

EXTRACT THE FOLLOWING FIELDS:

1. **Methodology Tags**: Extract relevant methodology tags from the survey content. Look for:
   - Van Westendorp pricing studies
   - Gabor Granger pricing studies  
   - Conjoint analysis
   - MaxDiff (Maximum Difference Scaling)
   - Brand tracking studies
   - NPS (Net Promoter Score) studies
   - Customer satisfaction surveys
   - Market research studies
   - Feature prioritization studies
   - Product testing studies

2. **Industry Classification**: Extract the industry type as free text from RFQ content. Look for:
   - Company background and product context
   - Industry mentions and sector descriptions
   - Business vertical and market context
   - Examples: "Technology", "Healthcare", "Financial Services", "Retail", "Automotive", "Education"

3. **Respondent Classification**: Extract the target respondent type as free text from RFQ content. Look for:
   - Research audience descriptions
   - Demographics and target market
   - Participant type mentions
   - Examples: "B2C Consumers", "B2B Professionals", "Healthcare Workers", "Students", "General Public"

5. **Industry Category**: Determine the industry from RFQ and survey content. Choose from:

6. **Research Goal**: Identify the primary research objective. Choose from:
   - pricing_research
   - feature_research
   - satisfaction_research
   - brand_research
   - market_sizing
   - product_development
   - competitive_analysis
   - customer_segmentation
   - other

7. **Quality Score**: Assess the overall quality of the survey (0.0-1.0) based on:
   - Question clarity and structure
   - Methodology appropriateness
   - Survey completeness
   - Professional presentation

8. **Suggested Title**: Create a concise, descriptive title for this golden example

9. **Confidence Level**: Rate your confidence in the extracted values (0.0-1.0)

Return ONLY a JSON object with this exact structure:
{{
  "methodology_tags": ["tag1", "tag2", "tag3"],
  "industry_classification": "Technology",
  "respondent_classification": "B2C Consumers",
  "industry_category": "electronics",
  "research_goal": "pricing_research", 
  "quality_score": 0.85,
  "suggested_title": "Customer Satisfaction Survey for Electronics",
  "confidence_level": 0.9,
  "reasoning": {{
    "methodology_tags": "Explanation for methodology tag choices",
    "industry_classification": "Explanation for industry classification extraction",
    "respondent_classification": "Explanation for respondent type extraction",
    "industry_category": "Explanation for industry category classification",
    "research_goal": "Explanation for research goal identification",
    "quality_score": "Explanation for quality assessment"
  }}
}}"""
        
        return prompt
    
    def _summarize_survey(self, survey_json: Dict[str, Any]) -> str:
        """Create a readable summary of the survey JSON."""
        summary_parts = []
        
        # Basic info
        if survey_json.get('title'):
            summary_parts.append(f"Title: {survey_json['title']}")
        if survey_json.get('description'):
            summary_parts.append(f"Description: {survey_json['description']}")
        
        # Questions summary
        questions = survey_json.get('questions', [])
        if questions:
            summary_parts.append(f"Number of Questions: {len(questions)}")
            
            # Question types
            question_types = {}
            for q in questions:
                q_type = q.get('type', 'unknown')
                question_types[q_type] = question_types.get(q_type, 0) + 1
            
            type_summary = ", ".join([f"{qtype}: {count}" for qtype, count in question_types.items()])
            summary_parts.append(f"Question Types: {type_summary}")
            
            # Sample questions
            summary_parts.append("Sample Questions:")
            for i, q in enumerate(questions[:3]):  # First 3 questions
                question_text = q.get('text', 'No text')
                text_preview = question_text[:100] if question_text is not None else '<null>'
                summary_parts.append(f"  {i+1}. {text_preview}...")
        
        # Methodologies
        methodologies = survey_json.get('methodologies', [])
        if methodologies:
            summary_parts.append(f"Methodologies: {', '.join(methodologies)}")
        
        return "\n".join(summary_parts)
    
    async def extract_fields(self, rfq_text: str, survey_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract golden example fields from RFQ and Survey content."""
        logger.info(
            "Starting field extraction",
            extra={
                "rfq_length": len(rfq_text),
                "survey_keys": list(survey_json.keys()) if isinstance(survey_json, dict) else [],
            },
        )

        try:
            prompt = self.create_field_extraction_prompt(rfq_text, survey_json)
            logger.debug(
                "Field extraction prompt prepared",
                extra={"prompt_length": len(prompt)},
            )

            interaction_id = f"field_extraction_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if self.db_session else None

            if audit_service:
                async with LLMAuditContext(
                    audit_service=audit_service,
                    interaction_id=interaction_id,
                    model_name=self.model,
                    model_provider=self.provider_name,
                    purpose="field_extraction",
                    input_prompt=prompt,
                    sub_purpose="golden_example_fields",
                    context_type="survey_data",
                    hyperparameters={
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                    metadata={
                        "rfq_length": len(rfq_text),
                        "survey_keys": list(survey_json.keys()) if isinstance(survey_json, dict) else [],
                        "prompt_length": len(prompt),
                    },
                    tags=["field_extraction", "golden_examples"],
                ) as audit_context:
                    logger.debug("Calling LLM for field extraction", extra={"audited": True})
                    start_time = time.time()
                    system_prompt_text = "Extract fields from RFQ/Survey. Return ONLY valid JSON.\n\nExtract:\n- methodology_tags: [\"van_westendorp\", \"conjoint\", \"maxdiff\", \"nps\", \"satisfaction\"]\n- industry_category: \"electronics|healthcare|financial|retail|automotive\"\n- research_goal: \"pricing_research|feature_research|satisfaction_research|brand_research|market_sizing\"\n- quality_score: 0.0-1.0\n- suggested_title: \"[descriptive title]\"\n\nMethodology Detection:\n- Van Westendorp: \"too cheap\", \"too expensive\" questions\n- Conjoint: Choice scenarios with attributes\n- MaxDiff: \"Most/Least important\" selections\n- NPS: \"How likely to recommend\""
                    
                    # Prepare response format based on provider
                    response_format = None
                    if self.provider_name == "openai":
                        from src.utils.json_generation_utils import JSONGenerationUtils
                        schema = JSONGenerationUtils.get_rfq_parsing_schema()
                        response_format = {"json_schema": schema}
                    else:
                        response_format = {"type": "json_object"}
                    
                    result = await self.llm_provider.generate(
                        prompt=prompt,
                        system_prompt=system_prompt_text,
                        model=self.model,
                        temperature=0.1,
                        max_tokens=1000,
                        response_format=response_format
                    )
                    
                    output = result["output"]
                    response_time_ms = int((time.time() - start_time) * 1000)

                    raw_response = output

                    processed_output = raw_response.strip()

                    audit_context.set_raw_response(raw_response)
                    audit_context.set_output(
                        output_content=processed_output,
                        response_time_ms=response_time_ms,
                    )
            else:
                logger.debug("Calling LLM for field extraction", extra={"audited": False})
                system_prompt_text = "Extract fields from RFQ/Survey. Return ONLY valid JSON.\n\nExtract:\n- methodology_tags: [\"van_westendorp\", \"conjoint\", \"maxdiff\", \"nps\", \"satisfaction\"]\n- industry_category: \"electronics|healthcare|financial|retail|automotive\"\n- research_goal: \"pricing_research|feature_research|satisfaction_research|brand_research|market_sizing\"\n- quality_score: 0.0-1.0\n- suggested_title: \"[descriptive title]\"\n\nMethodology Detection:\n- Van Westendorp: \"too cheap\", \"too expensive\" questions\n- Conjoint: Choice scenarios with attributes\n- MaxDiff: \"Most/Least important\" selections\n- NPS: \"How likely to recommend\""
                
                hyperparams = get_json_optimized_hyperparameters("rfq_parsing")
                
                # Prepare response format based on provider
                response_format = None
                if self.provider_name == "openai":
                    from src.utils.json_generation_utils import JSONGenerationUtils
                    schema = JSONGenerationUtils.get_rfq_parsing_schema()
                    response_format = {"json_schema": schema}
                else:
                    response_format = {"type": "json_object"}
                
                result = await self.llm_provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt_text,
                    model=self.model,
                    temperature=hyperparams.get("temperature", 0.1),
                    max_tokens=hyperparams.get("max_tokens", 1000),
                    response_format=response_format
                )
                
                output = result["output"]

            logger.debug("Processing LLM response")
            json_content = str(output).strip()

            logger.debug(
                "Parsing JSON response",
                extra={"response_length": len(json_content)},
            )
            extracted_fields = parse_llm_json_response(
                json_content, service_name="FieldExtraction"
            )

            if extracted_fields is None:
                logger.error("❌ [Field Extraction] JSON parsing failed")
                logger.error(f"❌ [Field Extraction] Raw response (first 1000 chars): {json_content[:1000]}")
                
                # Emergency audit logging - ensure raw response is captured
                try:
                    from src.utils.emergency_audit import emergency_log_llm_failure
                    await emergency_log_llm_failure(
                        raw_response=json_content,
                        service_name="FieldExtractionService",
                        error_message="JSON parsing failed for field extraction",
                        context={
                            "rfq_length": len(rfq_text),
                            "survey_keys": list(survey_json.keys()) if isinstance(survey_json, dict) else [],
                            "json_content_length": len(json_content),
                        },
                        model_name=self.model,
                        model_provider=self.provider_name,
                        purpose="field_extraction",
                        input_prompt=prompt[:1000] if len(prompt) > 1000 else prompt,
                    )
                except Exception as emergency_error:
                    logger.error(f"❌ [Field Extraction] Emergency logging failed: {str(emergency_error)}")
                
                raise UserFriendlyError(
                    message="Failed to extract fields from survey content",
                    technical_details="LLM response was not valid JSON",
                    action_required="Please try again or manually fill the fields",
                    raw_response=json_content
                )

            cleaned_fields = self._clean_extracted_fields(extracted_fields)
            logger.info(
                "Field extraction completed",
                extra={"fields": list(cleaned_fields.keys())},
            )

            return cleaned_fields

        except json.JSONDecodeError as e:
            logger.error(f"❌ [Field Extraction] JSON parsing failed: {str(e)}")
            logger.error(f"❌ [Field Extraction] Raw response: {json_content}")
            raise UserFriendlyError(
                message="Failed to extract fields from survey content",
                technical_details=f"LLM response was not valid JSON: {str(e)}",
                action_required="Please try again or manually fill the fields",
            )
        except Exception as e:
            logger.error(f"❌ [Field Extraction] Field extraction failed: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to extract fields from survey content",
                technical_details=str(e),
                action_required="Please try again or manually fill the fields",
            )

    def _clean_extracted_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted fields."""
        cleaned = {}
        
        # Methodology tags
        methodology_tags = fields.get('methodology_tags', [])
        if isinstance(methodology_tags, list):
            cleaned['methodology_tags'] = [tag.strip().lower() for tag in methodology_tags if tag.strip()]
        else:
            cleaned['methodology_tags'] = []
        
        # Industry classification (free text)
        industry_classification = fields.get('industry_classification', '').strip()
        cleaned['industry_classification'] = industry_classification if industry_classification else ''
        
        # Respondent classification (free text)
        respondent_classification = fields.get('respondent_classification', '').strip()
        cleaned['respondent_classification'] = respondent_classification if respondent_classification else ''
        
        # Industry category
        industry_category = fields.get('industry_category', '').strip().lower()
        valid_industries = [
            'electronics', 'appliances', 'healthcare_technology', 'enterprise_software',
            'automotive', 'financial_services', 'hospitality', 'retail', 'education',
            'manufacturing', 'other'
        ]
        if industry_category in valid_industries:
            cleaned['industry_category'] = industry_category
        else:
            cleaned['industry_category'] = 'other'
        
        # Research goal
        research_goal = fields.get('research_goal', '').strip().lower()
        valid_goals = [
            'pricing_research', 'feature_research', 'satisfaction_research',
            'brand_research', 'market_sizing', 'product_development',
            'competitive_analysis', 'customer_segmentation', 'other'
        ]
        if research_goal in valid_goals:
            cleaned['research_goal'] = research_goal
        else:
            cleaned['research_goal'] = 'other'
        
        # Quality score
        quality_score = fields.get('quality_score', 0.5)
        try:
            quality_score = float(quality_score)
            cleaned['quality_score'] = max(0.0, min(1.0, quality_score))  # Clamp to 0-1
        except (ValueError, TypeError):
            cleaned['quality_score'] = 0.5
        
        # Suggested title
        suggested_title = fields.get('suggested_title', '').strip()
        cleaned['suggested_title'] = suggested_title if suggested_title else 'Generated Survey'
        
        # Confidence level
        confidence_level = fields.get('confidence_level', 0.5)
        try:
            confidence_level = float(confidence_level)
            cleaned['confidence_level'] = max(0.0, min(1.0, confidence_level))  # Clamp to 0-1
        except (ValueError, TypeError):
            cleaned['confidence_level'] = 0.5
        
        # Reasoning
        reasoning = fields.get('reasoning', {})
        cleaned['reasoning'] = reasoning if isinstance(reasoning, dict) else {}
        
        return cleaned

# Global instance
field_extraction_service = FieldExtractionService()

