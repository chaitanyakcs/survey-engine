"""AI-powered field extraction service for auto-populating golden example fields."""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import replicate
import uuid
import time
from ..config.settings import settings
from ..utils.error_messages import UserFriendlyError, get_api_configuration_error
from ..utils.llm_audit_decorator import LLMAuditContext
from ..services.llm_audit_service import LLMAuditService

logger = logging.getLogger(__name__)

class FieldExtractionService:
    """Service for extracting and auto-populating golden example fields from RFQ and Survey content."""
    
    def __init__(self, db_session: Optional[Any] = None):
        logger.info(f"🚀 [FieldExtractionService] Starting initialization...")
        logger.info(f"🚀 [FieldExtractionService] Database session provided: {bool(db_session)}")
        logger.info(f"🚀 [FieldExtractionService] Config generation_model: {settings.generation_model}")
        
        if not settings.replicate_api_token:
            error_info = get_api_configuration_error()
            raise UserFriendlyError(
                message=error_info["message"],
                technical_details="REPLICATE_API_TOKEN environment variable is not set",
                action_required="Configure AI service provider (Replicate or OpenAI)"
            )
        replicate.api_token = settings.replicate_api_token
        self.db_session = db_session  # Set db_session BEFORE calling _get_generation_model
        self.model = self._get_generation_model()
        
        logger.info(f"🔧 [FieldExtractionService] Model selected: {self.model}")
        logger.info(f"🔧 [FieldExtractionService] Model type: {type(self.model)}")
    
    def _get_generation_model(self) -> str:
        """Get generation model from database settings or fallback to config"""
        try:
            logger.info(f"🔍 [FieldExtractionService] Starting model selection process...")
            logger.info(f"🔍 [FieldExtractionService] Database session available: {bool(self.db_session)}")
            logger.info(f"🔍 [FieldExtractionService] Config default model: {settings.generation_model}")
            
            if self.db_session:
                from src.services.settings_service import SettingsService
                settings_service = SettingsService(self.db_session)
                evaluation_settings = settings_service.get_evaluation_settings()
                
                logger.info(f"🔍 [FieldExtractionService] Database evaluation settings: {evaluation_settings}")
                
                if evaluation_settings and 'generation_model' in evaluation_settings:
                    model = evaluation_settings['generation_model']
                    logger.info(f"🔧 [FieldExtractionService] Using model from database settings: {model}")
                    logger.info(f"🔧 [FieldExtractionService] Model source: DATABASE")
                    return model
                else:
                    logger.info(f"🔧 [FieldExtractionService] No database settings found, using config default: {settings.generation_model}")
                    logger.info(f"🔧 [FieldExtractionService] Model source: CONFIG_FALLBACK")
                    return settings.generation_model
            else:
                logger.info(f"🔧 [FieldExtractionService] No database session, using config default: {settings.generation_model}")
                logger.info(f"🔧 [FieldExtractionService] Model source: CONFIG_NO_DB")
                return settings.generation_model
        except Exception as e:
            logger.warning(f"⚠️ [FieldExtractionService] Failed to get model from database settings: {e}, using config default")
            logger.info(f"🔧 [FieldExtractionService] Model source: CONFIG_EXCEPTION")
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

2. **Industry Category**: Determine the industry from RFQ and survey content. Choose from:
   - electronics
   - appliances
   - healthcare_technology
   - enterprise_software
   - automotive
   - financial_services
   - hospitality
   - retail
   - education
   - manufacturing
   - other

3. **Research Goal**: Identify the primary research objective. Choose from:
   - pricing_research
   - feature_research
   - satisfaction_research
   - brand_research
   - market_sizing
   - product_development
   - competitive_analysis
   - customer_segmentation
   - other

4. **Quality Score**: Assess the overall quality of the survey (0.0-1.0) based on:
   - Question clarity and structure
   - Methodology appropriateness
   - Survey completeness
   - Professional presentation

5. **Suggested Title**: Create a concise, descriptive title for this golden example

6. **Confidence Level**: Rate your confidence in the extracted values (0.0-1.0)

Return ONLY a JSON object with this exact structure:
{{
  "methodology_tags": ["tag1", "tag2", "tag3"],
  "industry_category": "electronics",
  "research_goal": "pricing_research", 
  "quality_score": 0.85,
  "suggested_title": "Customer Satisfaction Survey for Electronics",
  "confidence_level": 0.9,
  "reasoning": {{
    "methodology_tags": "Explanation for methodology tag choices",
    "industry_category": "Explanation for industry classification",
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
                summary_parts.append(f"  {i+1}. {q.get('text', 'No text')[:100]}...")
        
        # Methodologies
        methodologies = survey_json.get('methodologies', [])
        if methodologies:
            summary_parts.append(f"Methodologies: {', '.join(methodologies)}")
        
        return "\n".join(summary_parts)
    
    async def extract_fields(self, rfq_text: str, survey_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract golden example fields from RFQ and Survey content."""
        logger.info(f"🔍 [Field Extraction] Starting field extraction")
        logger.info(f"📝 [Field Extraction] RFQ length: {len(rfq_text)} chars")
        logger.info(f"📊 [Field Extraction] Survey keys: {list(survey_json.keys()) if isinstance(survey_json, dict) else 'Not a dict'}")
        
        try:
            # Create extraction prompt
            logger.info(f"📝 [Field Extraction] Creating extraction prompt")
            prompt = self.create_field_extraction_prompt(rfq_text, survey_json)
            logger.info(f"✅ [Field Extraction] Prompt created, length: {len(prompt)} chars")
            
            # Create audit context for this LLM interaction
            interaction_id = f"field_extraction_{uuid.uuid4().hex[:8]}"
            audit_service = LLMAuditService(self.db_session) if self.db_session else None
            
            if audit_service:
                async with LLMAuditContext(
                    audit_service=audit_service,
                    interaction_id=interaction_id,
                    model_name=self.model,
                    model_provider="replicate",
                    purpose="field_extraction",
                    input_prompt=prompt,
                    sub_purpose="golden_example_fields",
                    context_type="survey_data",
                    hyperparameters={
                        "temperature": 0.1,
                        "max_tokens": 2000
                    },
                    metadata={
                        "rfq_length": len(rfq_text),
                        "survey_keys": list(survey_json.keys()) if isinstance(survey_json, dict) else [],
                        "prompt_length": len(prompt)
                    },
                    tags=["field_extraction", "golden_examples"]
                ) as audit_context:
                    logger.info(f"🤖 [Field Extraction] Calling LLM for field extraction with auditing")
                    start_time = time.time()
                    output = await replicate.async_run(
                        self.model,
                        input={
                            "prompt": prompt,
                            "temperature": 0.1,
                            "max_tokens": 2000,
                            "system_prompt": "You are a survey methodology expert. Extract the requested fields from the provided RFQ and Survey content. Return ONLY valid JSON in the exact format specified."
                        }
                    )
                    
                    # Process the output and set audit context
                    response_time_ms = int((time.time() - start_time) * 1000)
                    audit_context.set_output(
                        output_content=str(output),
                        response_time_ms=response_time_ms
                    )
            else:
                # Fallback without auditing
                logger.info(f"🤖 [Field Extraction] Calling LLM for field extraction without auditing")
                output = await replicate.async_run(
                    self.model,
                    input={
                        "prompt": prompt,
                        "temperature": 0.1,
                        "max_tokens": 2000,
                        "system_prompt": "You are a survey methodology expert. Extract the requested fields from the provided RFQ and Survey content. Return ONLY valid JSON in the exact format specified."
                    }
                )
            
            # Process LLM response
            logger.info(f"📥 [Field Extraction] Processing LLM response")
            if hasattr(output, '__iter__') and not isinstance(output, str):
                json_content = "".join(str(chunk) for chunk in output).strip()
            else:
                json_content = str(output).strip()
            
            logger.info(f"✅ [Field Extraction] LLM response received, length: {len(json_content)} chars")
            logger.info(f"📄 [Field Extraction] Response preview: {json_content[:300]}...")
            
            # Parse JSON response
            logger.info(f"🔍 [Field Extraction] Parsing JSON response")
            extracted_fields = json.loads(json_content)
            logger.info(f"✅ [Field Extraction] JSON parsing successful")
            logger.info(f"📊 [Field Extraction] Extracted fields: {extracted_fields}")
            
            # Validate and clean extracted fields
            cleaned_fields = self._clean_extracted_fields(extracted_fields)
            logger.info(f"🧹 [Field Extraction] Cleaned fields: {cleaned_fields}")
            
            logger.info(f"🎉 [Field Extraction] Field extraction completed successfully")
            return cleaned_fields
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [Field Extraction] JSON parsing failed: {str(e)}")
            logger.error(f"❌ [Field Extraction] Raw response: {json_content}")
            raise UserFriendlyError(
                message="Failed to extract fields from survey content",
                technical_details=f"LLM response was not valid JSON: {str(e)}",
                action_required="Please try again or manually fill the fields"
            )
        except Exception as e:
            logger.error(f"❌ [Field Extraction] Field extraction failed: {str(e)}", exc_info=True)
            raise UserFriendlyError(
                message="Failed to extract fields from survey content",
                technical_details=str(e),
                action_required="Please try again or manually fill the fields"
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

