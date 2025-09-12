from typing import Dict, Any
from sqlalchemy.orm import Session
from .state import SurveyGenerationState
from src.services.embedding_service import EmbeddingService
from src.services.retrieval_service import RetrievalService
from src.services.generation_service import GenerationService
from src.services.validation_service import ValidationService
from src.utils.error_messages import UserFriendlyError


class RFQNode:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Parse RFQ, extract research goals and methodologies, generate embedding
        """
        try:
            # Generate embedding for the RFQ text
            embedding = await self.embedding_service.get_embedding(state.rfq_text)
            
            # TODO: Extract research goals and methodologies using NLP
            # Placeholder implementation
            extracted_goal = state.research_goal or "General market research"
            
            return {
                "rfq_embedding": embedding,
                "research_goal": extracted_goal,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"RFQ processing failed: {str(e)}"
            }


class GoldenRetrieverNode:
    def __init__(self, db: Session):
        self.db = db
        self.retrieval_service = RetrievalService(db)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Multi-tier retrieval (golden pairs → methodology blocks → templates)
        """
        try:
            # Tier 1: Exact golden RFQ-survey pairs
            if state.rfq_embedding is None:
                golden_examples = []
            else:
                golden_examples = await self.retrieval_service.retrieve_golden_pairs(
                    embedding=state.rfq_embedding,
                    methodology_tags=None,  # TODO: Extract from RFQ
                    limit=3
                )
            
            # Tier 2: Methodology blocks
            methodology_blocks = await self.retrieval_service.retrieve_methodology_blocks(
                research_goal=state.research_goal,
                limit=5
            )
            
            # Tier 3: Template questions (fallback)
            template_questions = await self.retrieval_service.retrieve_template_questions(
                category=state.product_category,
                limit=10
            )
            
            return {
                "golden_examples": golden_examples,
                "methodology_blocks": methodology_blocks,
                "template_questions": template_questions,
                "used_golden_examples": [ex["id"] for ex in golden_examples],
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"Golden retrieval failed: {str(e)}"
            }


class ContextBuilderNode:
    def __init__(self, db: Session):
        self.db = db
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Assemble hierarchical context with golden examples as few-shot prompts
        """
        try:
            context = {
                "rfq_details": {
                    "text": state.rfq_text,
                    "title": state.rfq_title,
                    "category": state.product_category,
                    "segment": state.target_segment,
                    "goal": state.research_goal
                },
                "golden_examples": state.golden_examples,
                "methodology_guidance": state.methodology_blocks,
                "template_fallbacks": state.template_questions
            }
            
            return {
                "context": context,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"Context building failed: {str(e)}"
            }


class GeneratorAgent:
    def __init__(self, db: Session):
        self.db = db
        self.generation_service = GenerationService(db_session=db)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        GPT-4/5 generation with golden-enhanced prompts
        """
        try:
            # Load custom rules from database
            from src.database.models import SurveyRule
            custom_rules_query = self.db.query(SurveyRule).filter(
                SurveyRule.rule_type == 'custom',
                SurveyRule.is_active == True
            ).all()
            
            custom_rules = {
                "rules": [rule.rule_description for rule in custom_rules_query if rule.rule_description]
            }
            
            generated_survey = await self.generation_service.generate_survey(
                context=state.context,
                golden_examples=state.golden_examples,
                methodology_blocks=state.methodology_blocks,
                custom_rules=custom_rules
            )
            
            return {
                "raw_survey": generated_survey,
                "generated_survey": generated_survey,
                "error_message": None
            }
            
        except UserFriendlyError as e:
            return {
                "error_message": f"AI Service Configuration Required: {e.message}",
                "user_friendly_error": True,
                "action_required": e.action_required
            }
        except Exception as e:
            return {
                "error_message": f"Survey generation failed: {str(e)}"
            }


class GoldenValidatorNode:
    def __init__(self, db: Session):
        self.db = db
        self.validation_service = ValidationService(db)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Validate against schema, methodology rules, and golden similarity
        """
        try:
            if state.generated_survey is None:
                validation_results = {"schema_valid": False, "methodology_compliant": False}
                similarity_score = 0.0
            else:
                validation_results = await self.validation_service.validate_survey(
                    survey=state.generated_survey,
                    golden_examples=state.golden_examples,
                    rfq_text=state.rfq_text
                )
                
                # Calculate golden similarity score
                similarity_score = await self.validation_service.calculate_golden_similarity(
                    survey=state.generated_survey,
                    golden_examples=state.golden_examples
                )
            
            quality_gate_passed = (
                validation_results.get("schema_valid", False) and
                validation_results.get("methodology_compliant", False) and
                similarity_score >= 0.75  # TODO: Use config threshold
            )
            
            # Increment retry count if validation fails
            updated_retry_count = state.retry_count
            if not quality_gate_passed:
                updated_retry_count += 1
            
            return {
                "validation_results": validation_results,
                "golden_similarity_score": similarity_score,
                "quality_gate_passed": quality_gate_passed,
                "retry_count": updated_retry_count,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"Validation failed: {str(e)}"
            }


class ResearcherNode:
    def __init__(self, db: Session):
        self.db = db
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Human review interface with golden benchmarks displayed
        """
        try:
            # TODO: Implement human review interface
            # For now, just mark as ready for human review
            
            review_data = {
                "survey": state.generated_survey,
                "validation_results": state.validation_results,
                "golden_similarity": state.golden_similarity_score,
                "golden_benchmarks": state.golden_examples,
                "status": "ready_for_review"
            }
            
            return {
                "review_data": review_data,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"Human review setup failed: {str(e)}"
            }