from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from .state import SurveyGenerationState
from src.utils.error_messages import UserFriendlyError
from src.utils.survey_utils import get_questions_count
import logging

logger = logging.getLogger(__name__)

# Allow tests to patch these without importing heavy service packages at import time
RetrievalService = None  # patched in tests; fallback import used at runtime
ValidationService = None  # optional; fallback import used at runtime


def get_db():
    """Lazy proxy to database session generator; safe to patch in tests.
    Returns the original generator when called, without importing settings at module import time.
    """
    from src.database import get_db as _get_db
    return _get_db()


class RFQNode:
    def __init__(self, db: Session):
        self.db = db
        # Lazy import to avoid heavy settings init during tests
        from src.services.embedding_service import EmbeddingService
        self.embedding_service = EmbeddingService()
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Parse RFQ, extract research goals and methodologies, generate embedding
        Load enhanced RFQ data from database if available
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Skip embedding generation during regeneration (RFQ hasn't changed)
            if state.regeneration_mode and state.rfq_embedding:
                logger.info("⚡ [RFQNode] Regeneration mode - reusing existing embedding (skipping generation)")
                embedding = state.rfq_embedding
            else:
                # Generate embedding for the RFQ text
                logger.info("🔄 [RFQNode] Starting embedding generation...")
                embedding = await self.embedding_service.get_embedding(state.rfq_text)
                logger.info("✅ [RFQNode] Embedding generation completed")
            
            # Load enhanced RFQ data from database if RFQ ID is available
            enhanced_rfq_data = None
            unmapped_context = ""
            if state.rfq_id:
                try:
                    from src.database.models import RFQ
                    rfq = self.db.query(RFQ).filter(RFQ.id == state.rfq_id).first()
                    if rfq and rfq.enhanced_rfq_data:
                        enhanced_rfq_data = rfq.enhanced_rfq_data
                        logger.info(f"✅ [RFQNode] Loaded enhanced RFQ data with {len(enhanced_rfq_data)} keys")
                        if 'survey_structure' in enhanced_rfq_data:
                            text_requirements = enhanced_rfq_data['survey_structure'].get('text_requirements', [])
                            logger.info(f"📋 [RFQNode] Text requirements found: {text_requirements}")
                        
                        # Extract unmapped_context for survey generation
                        unmapped_context = enhanced_rfq_data.get('unmapped_context', '')
                        if unmapped_context:
                            logger.info(f"📝 [RFQNode] Found unmapped_context: {len(unmapped_context)} characters")
                        else:
                            logger.info("ℹ️ [RFQNode] No unmapped_context found in enhanced RFQ data")
                    else:
                        logger.info("ℹ️ [RFQNode] No enhanced RFQ data found in database")
                except Exception as e:
                    logger.warning(f"⚠️ [RFQNode] Failed to load enhanced RFQ data: {str(e)}")
            
            # TODO: Extract research goals and methodologies using NLP
            # Placeholder implementation
            extracted_goal = state.research_goal or "General market research"
            
            return {
                "rfq_embedding": embedding,
                "research_goal": extracted_goal,
                "enhanced_rfq_data": enhanced_rfq_data,
                "unmapped_context": unmapped_context,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"RFQ processing failed: {str(e)}"
            }


class GoldenRetrieverNode:
    def __init__(self, db: Session):
        self.db = db
        # Defer service import/creation to call-site to avoid heavy imports during tests
        self.retrieval_service = None
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Multi-tier retrieval (golden pairs → methodology blocks → templates)
        """
        try:
            # Get a fresh database session to avoid transaction issues
            fresh_db = None
            try:
                fresh_db = next(get_db())
            except Exception:
                # In test mode without DB, proceed with empty results
                pass
            fresh_retrieval_service = None
            
            try:
                # Tier 1: Exact golden RFQ-survey pairs
                if state.rfq_embedding is None:
                    golden_examples = []
                    golden_sections = []
                    golden_questions = []
                    feedback_digest = None
                else:
                    # Lazy create retrieval service only when we actually need it
                    if fresh_retrieval_service is None:
                        ServiceClass = RetrievalService
                        if ServiceClass is None:
                            from src.services.retrieval_service import RetrievalService as ServiceClass
                        fresh_retrieval_service = ServiceClass(fresh_db)
                    # Extract industry from enhanced RFQ data if available
                    industry = None
                    if state.enhanced_rfq_data and 'industry_category' in state.enhanced_rfq_data:
                        industry = state.enhanced_rfq_data['industry_category']
                    
                    golden_examples = await fresh_retrieval_service.retrieve_golden_pairs(
                        embedding=state.rfq_embedding,
                        methodology_tags=None,  # TODO: Extract from RFQ
                        industry=industry,
                        limit=3
                    )
                    # New: retrieve sections and questions (default ON)
                    golden_sections = await fresh_retrieval_service.retrieve_golden_sections(
                        embedding=state.rfq_embedding,
                        methodology_tags=None,
                        industry=industry,
                        limit=5
                    )
                    
                    # Retrieve golden questions by similarity only (no label filtering)
                    # The LLM will use the QNR taxonomy reference to decide which questions to generate
                    golden_questions = await fresh_retrieval_service.retrieve_golden_questions(
                        embedding=state.rfq_embedding,
                        methodology_tags=None,
                        industry=industry,
                        limit=8  # Increased limit since we're not filtering by labels
                    )
                    logger.info(f"✅ [GoldenRetriever] Retrieved {len(golden_questions)} golden questions by similarity")
                    
                    # Retrieve feedback digest - different logic for regeneration mode
                    feedback_digest = None
                    if state.regeneration_mode and state.rfq_id:
                        # Regeneration mode: Collect feedback from all previous versions
                        try:
                            from src.services.annotation_feedback_service import AnnotationFeedbackService
                            annotation_service = AnnotationFeedbackService(fresh_db)
                            
                            # Build feedback digest from all previous versions
                            annotation_feedback = await annotation_service.build_feedback_digest(
                                rfq_id=state.rfq_id,
                                section_ids=state.target_sections,
                                prioritize_annotated=state.focus_on_annotated_areas
                            )
                            
                            # Also get general feedback digest from golden questions
                            general_feedback = await fresh_retrieval_service.get_feedback_digest(
                                methodology_tags=None,
                                industry=industry,
                                limit=50
                            )
                            
                            # Merge annotation feedback with general feedback
                            if general_feedback:
                                # Combine the digests
                                combined_digest = f"{annotation_feedback.get('combined_digest', '')}\n\nGeneral Feedback:\n{general_feedback.get('feedback_digest', '')}"
                                
                                feedback_digest = {
                                    'feedback_digest': combined_digest,
                                    'questions_with_feedback': annotation_feedback.get('question_feedback', {}).get('questions_with_feedback', []),
                                    'total_feedback_count': annotation_feedback.get('question_feedback', {}).get('total_count', 0),
                                    'annotation_feedback': annotation_feedback,  # Store full annotation feedback
                                    'general_feedback': general_feedback  # Store general feedback for reference
                                }
                            else:
                                # Use only annotation feedback if no general feedback
                                feedback_digest = {
                                    'feedback_digest': annotation_feedback.get('combined_digest', ''),
                                    'questions_with_feedback': annotation_feedback.get('question_feedback', {}).get('questions_with_feedback', []),
                                    'total_feedback_count': annotation_feedback.get('question_feedback', {}).get('total_count', 0),
                                    'annotation_feedback': annotation_feedback
                                }
                            
                            logger.info(f"✅ [GoldenRetriever] Generated regeneration feedback digest from {annotation_feedback.get('question_feedback', {}).get('total_count', 0)} questions with comments from all previous versions")
                        except Exception as e:
                            logger.warning(f"⚠️ [GoldenRetriever] Failed to generate regeneration feedback digest: {str(e)}")
                            # Fallback to general feedback digest
                            try:
                                feedback_digest = await fresh_retrieval_service.get_feedback_digest(
                                    methodology_tags=None,
                                    industry=industry,
                                    limit=50
                                )
                            except Exception as fallback_error:
                                logger.warning(f"⚠️ [GoldenRetriever] Failed to generate fallback feedback digest: {str(fallback_error)}")
                                feedback_digest = None
                    else:
                        # Regular generation: Use general feedback digest from golden questions
                        try:
                            feedback_digest = await fresh_retrieval_service.get_feedback_digest(
                                methodology_tags=None,
                                industry=industry,  # Use industry extracted above
                                limit=50
                            )
                            logger.info(f"✅ [GoldenRetriever] Generated feedback digest from {feedback_digest.get('total_feedback_count', 0)} questions with comments")
                        except Exception as e:
                            logger.warning(f"⚠️ [GoldenRetriever] Failed to generate feedback digest: {str(e)}")
                            feedback_digest = None
                
                # Tier 2: Methodology blocks
                methodology_blocks = []
                if fresh_db is not None:
                    # Ensure retrieval service is initialized even if embedding was None above
                    if fresh_retrieval_service is None:
                        ServiceClass = RetrievalService
                        if ServiceClass is None:
                            from src.services.retrieval_service import RetrievalService as ServiceClass
                        fresh_retrieval_service = ServiceClass(fresh_db)

                    methodology_blocks = await fresh_retrieval_service.retrieve_methodology_blocks(
                        research_goal=state.research_goal,
                        limit=5
                    )
                
                # Tier 3: Template questions (fallback)
                template_questions = []
                if fresh_db is not None:
                    template_questions = await fresh_retrieval_service.retrieve_template_questions(
                        category=state.product_category,
                        limit=10
                    )
            finally:
                if fresh_db is not None:
                    fresh_db.close()
            
            # Extract question IDs from feedback digest for tracking
            feedback_question_ids = []
            if feedback_digest and feedback_digest.get('question_ids'):
                feedback_question_ids = [UUID(qid) for qid in feedback_digest['question_ids']]
            
            # Update the state with the retrieved data
            state.golden_examples = golden_examples
            # Store multi-level retrieval in state/context
            state.golden_sections = golden_sections
            state.golden_questions = golden_questions
            state.methodology_blocks = methodology_blocks
            state.template_questions = template_questions
            state.feedback_digest = feedback_digest
            state.used_golden_examples = [UUID(ex["id"]) for ex in golden_examples if "id" in ex]
            state.used_golden_questions = [UUID(q["id"]) for q in golden_questions if "id" in q]
            state.used_golden_sections = [UUID(s["id"]) for s in golden_sections if "id" in s]
            state.used_feedback_questions = feedback_question_ids  # Track questions from feedback digest
            
            return {
                "golden_examples": golden_examples,
                "golden_sections": golden_sections,
                "golden_questions": golden_questions,
                "methodology_blocks": methodology_blocks,
                "template_questions": template_questions,
                "feedback_digest": feedback_digest,
                "used_golden_examples": [ex["id"] for ex in golden_examples],
                "used_golden_questions": [str(q["id"]) for q in golden_questions if "id" in q],
                "used_golden_sections": [str(s["id"]) for s in golden_sections if "id" in s],
                "used_feedback_questions": [str(qid) for qid in feedback_question_ids],  # Track feedback questions
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
            logger.info(f"🔍 [ContextBuilderNode] Building context with survey_id: {state.survey_id}")
            logger.info(f"🔍 [ContextBuilderNode] Survey ID type: {type(state.survey_id)}")
            logger.info(f"🔍 [ContextBuilderNode] RFQ ID: {state.rfq_id}")
            
            # Fetch concept files for this RFQ if rfq_id is available
            concept_files = []
            if state.rfq_id:
                try:
                    from src.database.models import ConceptFile
                    from uuid import UUID
                    rfq_uuid = UUID(str(state.rfq_id)) if not isinstance(state.rfq_id, UUID) else state.rfq_id
                    concept_files_query = self.db.query(ConceptFile).filter(
                        ConceptFile.rfq_id == rfq_uuid
                    ).order_by(ConceptFile.display_order, ConceptFile.created_at).all()
                    
                    concept_files = [
                        {
                            "id": str(cf.id),
                            "filename": cf.filename,
                            "original_filename": cf.original_filename or cf.filename,
                            "content_type": cf.content_type,
                            "file_size": cf.file_size,
                            "concept_stimulus_id": cf.concept_stimulus_id,
                            "display_order": cf.display_order,
                            "file_url": f"/api/v1/rfq/concept/{cf.id}"  # URL for accessing the file
                        }
                        for cf in concept_files_query
                    ]
                    logger.info(f"📎 [ContextBuilderNode] Found {len(concept_files)} concept files for RFQ {state.rfq_id}")
                except Exception as e:
                    logger.warning(f"⚠️ [ContextBuilderNode] Failed to fetch concept files: {str(e)}")
                    concept_files = []
            
            # Extract generation_config from enhanced_rfq_data if available
            generation_config = {}
            if state.enhanced_rfq_data and isinstance(state.enhanced_rfq_data, dict):
                generation_config = state.enhanced_rfq_data.get("generation_config", {})
                if generation_config:
                    logger.info(f"⚙️ [ContextBuilderNode] Found generation_config: {generation_config}")
            
            context = {
                # Note: survey_id is used only for audit tracking, not content generation
                "audit_survey_id": str(state.survey_id) if state.survey_id else None,
                "workflow_id": str(state.workflow_id) if state.workflow_id else None,
                "rfq_id": str(state.rfq_id) if state.rfq_id else None,
                # Include feedback digest from questions with comments
                "feedback_digest": state.feedback_digest,
                "rfq_details": {
                    "text": state.rfq_text,
                    "title": state.rfq_title,
                    "category": state.product_category,
                    "segment": state.target_segment,
                    "goal": state.research_goal
                },
                "golden_examples": state.golden_examples,
                "golden_sections": getattr(state, 'golden_sections', []),
                "golden_questions": getattr(state, 'golden_questions', []),
                "methodology_guidance": state.methodology_blocks,
                "template_fallbacks": state.template_questions,
                # Enhanced RFQ data for text requirements and enriched context
                "enhanced_rfq_data": state.enhanced_rfq_data,
                # Unmapped context from RFQ parsing for additional survey generation context
                "unmapped_context": state.unmapped_context or "",
                # Generation configuration for prompt optimization
                "generation_config": generation_config,
                # Concept files for inclusion in Section 4 (Concept Exposure)
                "concept_files": concept_files,
                # Regeneration mode context
                "regeneration_mode": state.regeneration_mode,
                "previous_survey_encoded": state.previous_survey_encoded,
                "previous_survey_json": state.previous_survey_json,  # Original survey JSON for question text extraction
                "annotation_feedback_summary": state.annotation_feedback_summary,
                "focus_on_annotated_areas": state.focus_on_annotated_areas
            }
            
            logger.info(f"🔍 [ContextBuilderNode] Final context audit_survey_id: {context.get('audit_survey_id')}")
            logger.info(f"🔍 [ContextBuilderNode] Context keys: {list(context.keys())}")
            logger.info(f"🔍 [ContextBuilderNode] Enhanced RFQ data available: {bool(state.enhanced_rfq_data)}")
            if state.enhanced_rfq_data:
                logger.info(f"🔍 [ContextBuilderNode] Enhanced RFQ sections: {list(state.enhanced_rfq_data.keys())}")

            # Update the state with the context
            state.context = context

            # Log the context details for debugging
            logger.info(f"🔍 [ContextBuilderNode] Context built successfully")
            logger.info(f"🔍 [ContextBuilderNode] Audit Survey ID in context: {context.get('audit_survey_id')}")
            logger.info(f"🔍 [ContextBuilderNode] Workflow ID in context: {context.get('workflow_id')}")
            logger.info(f"🔍 [ContextBuilderNode] Context keys: {list(context.keys())}")
            logger.info(f"🔍 [ContextBuilderNode] State survey_id: {state.survey_id}")
            logger.info(f"🔍 [ContextBuilderNode] State context keys: {list(state.context.keys()) if state.context else 'None'}")
            
            return {
                "context": context,
                "error_message": None
            }
            
        except Exception as e:
            return {
                "error_message": f"Context building failed: {str(e)}"
            }


class GeneratorAgent:
    def __init__(self, db: Session, connection_manager=None):
        self.db = db
        self.connection_manager = connection_manager
        # Defer heavy imports/initialization until first call
        self.generation_service = None
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        GPT-4/5 generation with golden-enhanced prompts
        """
        try:
            self.logger.info("🤖 [GeneratorAgent] Starting survey generation...")
            self.logger.info(f"📊 [GeneratorAgent] State context keys: {list(state.context.keys()) if state.context else 'None'}")
            self.logger.info(f"📊 [GeneratorAgent] Golden examples count: {len(state.golden_examples) if state.golden_examples else 0}")
            self.logger.info(f"📊 [GeneratorAgent] Methodology blocks count: {len(state.methodology_blocks) if state.methodology_blocks else 0}")
            
            # Initialize generation service on first use to avoid import-time side effects
            if self.generation_service is None:
                from src.services.generation_service import GenerationService
                self.generation_service = GenerationService(db_session=self.db)

            # Get a fresh database session to avoid transaction issues
            fresh_db = None
            try:
                fresh_db = next(get_db())
                # Load custom rules from database using fresh session
                from src.database.models import SurveyRule
                custom_rules_query = fresh_db.query(SurveyRule).filter(
                    SurveyRule.rule_type == 'custom',
                    SurveyRule.is_active == True
                ).all()
                
                # Update the existing generation service with fresh database session and workflow info
                self.generation_service.db_session = fresh_db
                self.generation_service.workflow_id = state.workflow_id
                self.generation_service.connection_manager = self.connection_manager

                # Initialize WebSocket client if available
                if self.connection_manager and state.workflow_id:
                    from src.services.websocket_client import WebSocketNotificationService
                    self.generation_service.ws_client = WebSocketNotificationService(self.connection_manager)
                else:
                    self.generation_service.ws_client = None
                
            except Exception as db_error:
                self.logger.warning(f"⚠️ [GeneratorAgent] Failed to load custom rules: {str(db_error)}")
                custom_rules_query = []
            
            custom_rules = {
                "rules": [rule.rule_description for rule in custom_rules_query if rule.rule_description]
            }
            
            self.logger.info(f"📋 [GeneratorAgent] Custom rules loaded: {len(custom_rules['rules'])} rules")
            self.logger.info(f"🔧 [GeneratorAgent] Generation service model: {self.generation_service.model}")
            
            # Check API token configuration (optional during tests)
            try:
                from src.config import settings
                token_preview = settings.replicate_api_token[:8] if settings.replicate_api_token else None
                self.logger.info(f"🔧 [GeneratorAgent] Replicate API token configured: {bool(settings.replicate_api_token)}")
                if token_preview:
                    self.logger.info(f"🔧 [GeneratorAgent] Replicate API token preview: {token_preview}...")
            except Exception:
                self.logger.info("🔧 [GeneratorAgent] Settings unavailable in test mode; skipping token check")
            
            # Log the context being passed to generation service
            self.logger.info(f"🔍 [GeneratorAgent] About to call generation service with context:")
            self.logger.info(f"🔍 [GeneratorAgent] Context type: {type(state.context)}")
            self.logger.info(f"🔍 [GeneratorAgent] Context keys: {list(state.context.keys()) if state.context else 'None'}")
            self.logger.info(f"🔍 [GeneratorAgent] Context audit_survey_id: {state.context.get('audit_survey_id') if state.context else 'None'}")
            self.logger.info(f"🔍 [GeneratorAgent] Context rfq_id: {state.context.get('rfq_id') if state.context else 'None'}")
            self.logger.info(f"🔍 [GeneratorAgent] Context workflow_id: {state.context.get('workflow_id') if state.context else 'None'}")
            
            # Check if we have a custom system prompt from human review
            if state.system_prompt:
                self.logger.info(f"📝 [GeneratorAgent] Using custom system prompt from user edit (length: {len(state.system_prompt)} chars)")
                self.logger.info(f"🔍 [GeneratorAgent] Custom prompt preview: {state.system_prompt[:200]}...")
                # Use the edited system prompt instead of generating a new one
                generation_result = await self.generation_service.generate_survey_with_custom_prompt(
                    context=state.context,
                    golden_examples=state.golden_examples,
                    methodology_blocks=state.methodology_blocks,
                    custom_rules=custom_rules,
                    system_prompt=state.system_prompt
                )
            else:
                self.logger.info("🚀 [GeneratorAgent] Using default prompt generation...")
                generation_result = await self.generation_service.generate_survey(
                    context=state.context,
                    golden_examples=state.golden_examples,
                    methodology_blocks=state.methodology_blocks,
                    custom_rules=custom_rules
                )
            
            # Extract survey from generation result
            generated_survey = generation_result.get("survey", {})

            self.logger.info(f"✅ [GeneratorAgent] Generation completed. Survey keys: {list(generated_survey.keys()) if generated_survey else 'None'}")

            if generated_survey:
                question_count = get_questions_count(generated_survey)
                self.logger.info(f"📝 [GeneratorAgent] Generated {question_count} questions")
                if question_count == 0:
                    self.logger.error("❌ [GeneratorAgent] CRITICAL: No questions found in generated survey - this is a generation failure")
                    # Log detailed structure for debugging
                    sections = generated_survey.get("sections", [])
                    self.logger.error(f"❌ [GeneratorAgent] Survey structure: {len(sections)} sections")
                    for i, section in enumerate(sections):
                        section_questions = len(section.get("questions", []))
                        self.logger.error(f"❌ [GeneratorAgent] Section {i+1} ({section.get('title', 'No title')}): {section_questions} questions")
                    # Raise error to prevent empty survey from being saved
                    raise ValueError("Generated survey is empty - no questions found. This indicates a generation failure. Please check the LLM response and prompt.")
            else:
                self.logger.error("❌ [GeneratorAgent] CRITICAL: No survey data generated at all")
                raise ValueError("Survey generation failed - no survey data was returned. Please check the LLM response and prompt.")

            # Update the state with the generated data
            state.raw_survey = generated_survey
            state.generated_survey = generated_survey
            
            # Log the context details for debugging (truncated)
            logger.info(f"🔍 [GeneratorAgent] Context received from state")
            logger.info(f"🔍 [GeneratorAgent] State survey_id: {state.survey_id}")
            logger.debug(f"🔍 [GeneratorAgent] State context: {str(state.context)[:200]}...")
            logger.info(f"🔍 [GeneratorAgent] Context audit_survey_id: {state.context.get('audit_survey_id') if state.context else 'None'}")
            logger.info(f"🔍 [GeneratorAgent] Context keys: {list(state.context.keys()) if state.context else 'None'}")
            
            result = {
                "raw_survey": generated_survey,
                "generated_survey": generated_survey,
                "error_message": None
            }
            
            # Close the fresh database session
            if fresh_db is not None:
                try:
                    fresh_db.close()
                except Exception as e:
                    self.logger.warning(f"⚠️ [GeneratorAgent] Failed to close fresh database session: {e}")
            
            return result
            
        except UserFriendlyError as e:
            self.logger.error(f"❌ [GeneratorAgent] UserFriendlyError: {e.message}")
            return {
                "error_message": f"AI Service Configuration Required: {e.message}",
                "user_friendly_error": True,
                "action_required": e.action_required
            }
        except Exception as e:
            self.logger.error(f"❌ [GeneratorAgent] Exception during generation: {str(e)}", exc_info=True)
            
            # CRITICAL: Try to extract raw_response from exception chain
            from src.services.generation_service import SurveyGenerationError
            raw_response = None
            
            # Traverse exception chain to find SurveyGenerationError with raw_response
            current_exception = e
            depth = 0
            max_depth = 5  # Prevent infinite loops
            
            while current_exception and depth < max_depth:
                # Check if current exception has raw_response
                if isinstance(current_exception, SurveyGenerationError) and current_exception.raw_response:
                    raw_response = current_exception.raw_response
                    self.logger.info(f"🔍 [GeneratorAgent] Captured raw response from SurveyGenerationError at depth {depth} (length: {len(raw_response)})")
                    break
                elif hasattr(current_exception, 'raw_response') and current_exception.raw_response:
                    raw_response = current_exception.raw_response
                    self.logger.info(f"🔍 [GeneratorAgent] Captured raw response from exception at depth {depth} (length: {len(raw_response)})")
                    break
                
                # Move to next level in exception chain
                if hasattr(current_exception, '__cause__') and current_exception.__cause__:
                    current_exception = current_exception.__cause__
                elif hasattr(current_exception, '__context__') and current_exception.__context__:
                    current_exception = current_exception.__context__
                else:
                    break
                depth += 1
            
            if not raw_response:
                self.logger.warning(f"⚠️ [GeneratorAgent] Could not extract raw_response from exception chain (checked {depth} levels)")
            
            result = {
                "error_message": f"Survey generation failed: {str(e)}"
            }
            
            # Include raw_response in result so it can be saved even when generation fails
            if raw_response:
                result["generation_metadata"] = {
                    "raw_response": raw_response,
                    "error": True
                }
                self.logger.info(f"💾 [GeneratorAgent] Included raw response in error result (length: {len(raw_response)})")
            
            return result


class GoldenValidatorNode:
    def __init__(self, db: Session):
        self.db = db
        # Lazy import to avoid heavy settings init during tests
        from src.services.validation_service import ValidationService as _ValidationService
        self.validation_service = _ValidationService(db)
        # Import structure validator
        from src.services.survey_structure_validator import SurveyStructureValidator
        self.structure_validator = SurveyStructureValidator(db)
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Validate against schema, methodology rules, golden similarity, and structure
        """
        try:
            if state.generated_survey is None:
                validation_results = {"schema_valid": False, "methodology_compliant": False}
                similarity_score = 0.0
                structure_validation = None
            else:
                # Get a fresh database session to avoid transaction issues
                from src.database import get_db as _get_db
                fresh_db = next(_get_db())
                VClass = ValidationService
                if VClass is None:
                    from src.services.validation_service import ValidationService as VClass
                fresh_validation_service = VClass(fresh_db)
                
                try:
                    validation_results = await fresh_validation_service.validate_survey(
                        survey=state.generated_survey,
                        golden_examples=state.golden_examples,
                        rfq_text=state.rfq_text
                    )
                    
                    # Calculate golden similarity score
                    similarity_score = await fresh_validation_service.calculate_golden_similarity(
                        survey=state.generated_survey,
                        golden_examples=state.golden_examples
                    )
                    
                    # NEW: Structure validation (non-blocking)
                    try:
                        structure_validation = await self.structure_validator.validate_structure(
                            survey_json=state.generated_survey,
                            rfq_context={
                                'methodology_tags': getattr(state, 'methodology_tags', []) or [],
                                'industry': getattr(state, 'industry_category', None),
                                'respondent_type': getattr(state, 'respondent_type', None)
                            }
                        )
                        self.logger.info(f"🔍 [GoldenValidatorNode] Structure validation completed: {structure_validation.get_summary()}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ [GoldenValidatorNode] Structure validation failed: {e}")
                        structure_validation = None
                        
                finally:
                    fresh_db.close()
            
            quality_gate_passed = (
                validation_results.get("schema_valid", False) and
                validation_results.get("methodology_compliant", False) and
                similarity_score >= 0.75  # TODO: Use config threshold
            )
            
            # Structure validation NEVER blocks generation
            # It only provides quality scoring and flagging
            
            # Retries disabled - keep retry count unchanged
            updated_retry_count = state.retry_count
            
            # Prepare response
            response = {
                "validation_results": validation_results,
                "golden_similarity_score": similarity_score,
                "quality_gate_passed": quality_gate_passed,
                "retry_count": updated_retry_count,
                # Don't clear error_message if it was set by a previous node
                "error_message": state.error_message if state.error_message else None
            }
            
            # Add structure validation results if available
            if structure_validation:
                response["structure_validation"] = structure_validation.to_dict()
                
                # Flag for review if critical issues (but don't block)
                if structure_validation.has_critical_issues():
                    response["flagged_for_review"] = True
                    response["flag_reason"] = structure_validation.get_critical_issues_summary()
                    self.logger.warning(f"🚩 [GoldenValidatorNode] Survey flagged for review: {response['flag_reason']}")
            
            return response
            
        except Exception as e:
            return {
                "error_message": f"Validation failed: {str(e)}"
            }


class HumanPromptReviewNode:
    def __init__(self, db: Session):
        self.db = db
        import logging
        self.logger = logging.getLogger(__name__)

    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Handle human prompt review workflow with robust error handling and resource management
        """
        # Set strict timeout for the entire operation
        import asyncio
        from contextlib import asynccontextmanager

        async def _execute_with_timeout():
            try:
                # Import here to avoid circular imports
                from src.services.prompt_service import PromptService
                from src.database.models import HumanReview

                self.logger.info("🔍 [HumanPromptReviewNode] Starting human prompt review...")

                # Get settings from the settings API
                enable_prompt_review = False
                prompt_review_mode = 'disabled'

                try:
                    # Get settings from database
                    from src.services.settings_service import SettingsService
                    from src.database import get_db as _get_db
                    
                    # Get a fresh database connection
                    fresh_db = next(_get_db())
                    settings_service = SettingsService(fresh_db)
                    settings = settings_service.get_evaluation_settings()
                    
                    enable_prompt_review = settings.get('enable_prompt_review', False)
                    prompt_review_mode = settings.get('prompt_review_mode', 'disabled')
                    self.logger.info(f"🔍 [HumanPromptReviewNode] Settings: enable={enable_prompt_review}, mode={prompt_review_mode}")
                    
                    # Close the database connection
                    fresh_db.close()

                except Exception as e:
                    self.logger.warning(f"⚠️ [HumanPromptReviewNode] Settings fetch failed: {e}, using defaults")
                    enable_prompt_review = False
                    prompt_review_mode = 'disabled'

                # Fast path: if human review is disabled, return immediately
                if not enable_prompt_review or prompt_review_mode == 'disabled':
                    self.logger.info("🔄 [HumanPromptReviewNode] Human review disabled, skipping...")
                    return {
                        "prompt_approved": True,
                        "pending_human_review": False,
                        "error_message": None
                    }

                # Human review is enabled - proceed with review logic
                self.logger.info("🔍 [HumanPromptReviewNode] Human review enabled, creating review...")

                # Check if we already have a custom system prompt (from user edit)
                if state.system_prompt:
                    self.logger.info("🎨 [HumanPromptReviewNode] Using custom system prompt from user edit")
                    system_prompt = state.system_prompt
                else:
                    # Generate the system prompt with timeout protection
                    try:
                        prompt_service = PromptService()
                        system_prompt = await prompt_service.create_survey_generation_prompt(
                            rfq_text=state.rfq_text,
                            context=state.context or {},
                            golden_examples=state.golden_examples or [],
                            methodology_blocks=state.methodology_blocks or []
                        )
                    except Exception as e:
                        self.logger.error(f"❌ [HumanPromptReviewNode] Prompt generation failed: {e}")
                        # Fail open - continue without review
                        return {
                            "prompt_approved": True,
                            "pending_human_review": False,
                            "error_message": f"Prompt generation failed: {str(e)}"
                        }

                # Check existing reviews with fresh DB connection
                review_db = None
                try:
                    from src.database import get_db as _get_db
                    review_db = next(_get_db())
                    existing_review = review_db.query(HumanReview).filter(
                        HumanReview.workflow_id == state.workflow_id
                    ).first()

                    if existing_review:
                        self.logger.info(f"📋 [HumanPromptReviewNode] Found existing review: {existing_review.review_status}")

                        if existing_review.review_status == 'approved':
                            return {
                                "prompt_approved": True,
                                "pending_human_review": False,
                                "review_id": existing_review.id,
                                "error_message": None
                            }
                        elif existing_review.review_status == 'rejected':
                            return {
                                "prompt_approved": False,
                                "pending_human_review": False,
                                "review_id": existing_review.id,
                                "error_message": "System prompt was rejected by human reviewer"
                            }
                        elif existing_review.review_status in ['pending', 'in_review']:
                            if prompt_review_mode == 'blocking':
                                return {
                                    "prompt_approved": False,
                                    "pending_human_review": True,
                                    "review_id": existing_review.id,
                                    "workflow_paused": True,
                                    "error_message": None
                                }
                            else:
                                return {
                                    "prompt_approved": True,
                                    "pending_human_review": False,
                                    "review_id": existing_review.id,
                                    "error_message": None
                                }

                    # Create new review with proper transaction management
                    review = HumanReview(
                        workflow_id=state.workflow_id,
                        survey_id=str(state.survey_id) if state.survey_id else None,
                        prompt_data=system_prompt[:10000],  # Truncate to avoid memory issues
                        original_rfq=state.rfq_text[:5000] if state.rfq_text else "",  # Truncate
                        review_status='pending'
                    )

                    review_db.add(review)
                    review_db.commit()
                    review_db.refresh(review)

                    self.logger.info(f"✅ [HumanPromptReviewNode] Review created with ID: {review.id}")

                    # Return based on review mode
                    if prompt_review_mode == 'blocking':
                        result = {
                            "prompt_approved": False,
                            "pending_human_review": True,
                            "review_id": review.id,
                            "workflow_paused": True,
                            "error_message": None
                        }
                        self.logger.info(f"🔍 [HumanPromptReviewNode] BLOCKING mode - returning: {result}")
                        return result
                    else:
                        result = {
                            "prompt_approved": True,
                            "pending_human_review": False,
                            "review_id": review.id,
                            "error_message": None
                        }
                        self.logger.info(f"🔍 [HumanPromptReviewNode] NON-BLOCKING mode - returning: {result}")
                        return result

                except Exception as e:
                    self.logger.error(f"❌ [HumanPromptReviewNode] Review creation failed: {e}")
                    # Always rollback on error
                    if review_db:
                        try:
                            review_db.rollback()
                        except:
                            pass
                    # Fail open
                    return {
                        "prompt_approved": True,
                        "pending_human_review": False,
                        "error_message": f"Review creation failed: {str(e)}"
                    }
                finally:
                    # Always clean up
                    if review_db:
                        try:
                            review_db.close()
                        except Exception as e:
                            self.logger.warning(f"⚠️ [HumanPromptReviewNode] Failed to close review DB: {e}")

            except Exception as e:
                self.logger.error(f"❌ [HumanPromptReviewNode] Unexpected error: {str(e)}", exc_info=True)
                # Always fail open to prevent blocking
                return {
                    "prompt_approved": True,
                    "pending_human_review": False,
                    "error_message": f"Unexpected error: {str(e)}"
                }

        # Execute with strict timeout
        try:
            return await asyncio.wait_for(_execute_with_timeout(), timeout=10.0)
        except asyncio.TimeoutError:
            self.logger.error("❌ [HumanPromptReviewNode] Operation timed out after 10 seconds")
            # Fail open on timeout
            return {
                "prompt_approved": True,
                "pending_human_review": False,
                "error_message": "Human review node timed out"
            }
        except Exception as e:
            self.logger.error(f"❌ [HumanPromptReviewNode] Critical error: {str(e)}", exc_info=True)
            # Always fail open
            return {
                "prompt_approved": True,
                "pending_human_review": False,
                "error_message": f"Critical error: {str(e)}"
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


class LabelDetectionNode:
    def __init__(self, db: Session, connection_manager=None):
        self.db = db
        self.connection_manager = connection_manager
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize label detection services
        from src.services.question_label_detector import QuestionLabelDetector
        from src.database.models import QuestionAnnotation
        from datetime import datetime
        
        self.detector = QuestionLabelDetector()
        self.QuestionAnnotation = QuestionAnnotation
        self.datetime = datetime
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Automatically detect and assign labels to generated questions.
        Creates question annotations in the database instead of writing to question.labels.
        
        During surgical regeneration, only detects labels for regenerated sections.
        """
        try:
            self.logger.info("🏷️ [LabelDetectionNode] Starting automatic label detection...")
            
            if not state.generated_survey:
                self.logger.warning("⚠️ [LabelDetectionNode] No generated survey found, skipping label detection")
                return {
                    "labels_assigned": False,
                    "error_message": "No survey available for label detection"
                }
            
            if not state.survey_id:
                self.logger.error("❌ [LabelDetectionNode] No survey_id in state, cannot create annotations")
                return {
                    "labels_assigned": False,
                    "error_message": "No survey_id available for annotation creation"
                }
            
            # Determine which sections to process
            sections_to_process = state.generated_survey.get('sections', [])
            
            # SURGICAL/TARGETED MODE: Only detect labels for regenerated sections
            from src.workflows.state import RegenerationMode
            if state.regeneration_mode and state.regeneration_mode_type in (RegenerationMode.SURGICAL, RegenerationMode.TARGETED):
                if state.surgical_analysis and 'sections_to_regenerate' in state.surgical_analysis:
                    regenerated_section_ids = state.surgical_analysis['sections_to_regenerate']
                    sections_to_process = [s for s in sections_to_process if s.get('id') in regenerated_section_ids]
                    self.logger.info(f"⚡ [LabelDetectionNode] Surgical mode - only processing {len(sections_to_process)} regenerated sections (skipping {len(state.generated_survey.get('sections', [])) - len(sections_to_process)} preserved sections)")
                else:
                    self.logger.info("🏷️ [LabelDetectionNode] Surgical mode but no surgical_analysis - processing all sections")
            else:
                self.logger.info(f"🏷️ [LabelDetectionNode] Full mode - processing all {len(sections_to_process)} sections")
            
            # Detect labels for the sections we're processing
            detected_labels = self.detector.detect_labels_in_survey({'sections': sections_to_process})
            self.logger.info(f"🏷️ [LabelDetectionNode] Detected labels: {detected_labels}")
            
            # Create annotations in database
            annotations_created = 0
            labels_assigned = 0
            
            for section in sections_to_process:
                section_id = section.get('id')
                section_labels = detected_labels.get(section_id, set())
                
                # Add labels to section metadata (backward compatibility)
                if 'metadata' not in section:
                    section['metadata'] = {}
                section['metadata']['detected_labels'] = list(section_labels)
                
                # Assign labels to individual questions
                for question in section.get('questions', []):
                    question_id = question.get('id') or question.get('question_id')
                    if not question_id:
                        self.logger.warning(f"⚠️ [LabelDetectionNode] Question missing id: {question.get('text', '')[:50]}")
                        continue
                    
                    # Make question_id unique by prefixing with survey_id
                    unique_question_id = f"{state.survey_id}_{question_id}"
                    question_labels = self.detector.detect_labels_in_question(question)
                    
                    # Check if annotation already exists
                    existing_annotation = self.db.query(self.QuestionAnnotation).filter(
                        self.QuestionAnnotation.question_id == unique_question_id,
                        self.QuestionAnnotation.survey_id == state.survey_id
                    ).first()
                    
                    if existing_annotation:
                        # Update existing annotation with detected labels (merge, don't override)
                        existing_labels = existing_annotation.labels or []
                        existing_labels_set = set(existing_labels) if isinstance(existing_labels, list) else set()
                        new_labels_set = set(question_labels) if isinstance(question_labels, list) else set()
                        
                        # Merge labels (add new ones)
                        merged_labels = list(existing_labels_set | new_labels_set)
                        existing_annotation.labels = merged_labels
                        existing_annotation.updated_at = self.datetime.now()
                        
                        self.logger.debug(f"🔄 [LabelDetectionNode] Updated annotation for question {unique_question_id}")
                    else:
                        # Create new annotation
                        annotation = self.QuestionAnnotation(
                            question_id=unique_question_id,
                            survey_id=state.survey_id,
                            required=True,
                            quality=3,  # Default value
                            relevant=3,  # Default value
                            methodological_rigor=3,
                            content_validity=3,
                            respondent_experience=3,
                            analytical_value=3,
                            business_impact=3,
                            comment="",
                            labels=question_labels,
                            removed_labels=[],
                            annotator_id="auto_detector",
                            ai_generated=False,
                            human_verified=False,
                            created_at=self.datetime.now(),
                            updated_at=self.datetime.now()
                        )
                        self.db.add(annotation)
                        annotations_created += 1
                        self.logger.debug(f"✅ [LabelDetectionNode] Created annotation for question {unique_question_id} with labels: {question_labels}")
                    
                    # Add labels to question object for backward compatibility (DEPRECATED)
                    if 'metadata' not in question:
                        question['metadata'] = {}
                    question['metadata']['labels'] = question_labels
                    question['labels'] = question_labels  # DEPRECATED: kept for backward compatibility
                    
                    labels_assigned += len(question_labels)
            
            # Commit annotations to database
            try:
                self.db.commit()
                self.logger.info(f"✅ [LabelDetectionNode] Created {annotations_created} new annotations, assigned {labels_assigned} labels across {len(state.generated_survey.get('sections', []))} sections")
            except Exception as e:
                self.db.rollback()
                self.logger.error(f"❌ [LabelDetectionNode] Failed to commit annotations: {str(e)}", exc_info=True)
                raise
            
            # Update the state with the modified survey
            state.generated_survey = state.generated_survey
            
            return {
                "labels_assigned": True,
                "total_labels_assigned": labels_assigned,
                "annotations_created": annotations_created,
                "detected_labels": {str(k): list(v) for k, v in detected_labels.items()},
                "error_message": None
            }
            
        except Exception as e:
            self.logger.error(f"❌ [LabelDetectionNode] Label detection failed: {str(e)}", exc_info=True)
            if self.db:
                self.db.rollback()
            return {
                "labels_assigned": False,
                "error_message": f"Label detection failed: {str(e)}"
            }


class ValidatorAgent:
    def __init__(self, db: Session, connection_manager=None):
        self.db = db
        self.connection_manager = connection_manager
        import logging
        self.logger = logging.getLogger(__name__)

    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Run basic validation (schema, methodology) without AI evaluation.
        AI evaluation is now user-triggered from SurveyPreview.
        """
        try:
            self.logger.info("🔍 [ValidatorAgent] Starting basic validation (no AI evaluation)...")

            # Check if we have a generated survey
            if not state.generated_survey:
                self.logger.error("❌ [ValidatorAgent] No generated survey found in state")
                return {
                    "error_message": "No survey available for validation",
                    "validation_results": {"schema_valid": False, "methodology_compliant": False},
                    "workflow_should_continue": True
                }

            # Get a fresh database session
            from src.database import get_db
            fresh_db = next(get_db())

            try:
                # Run basic validation (schema, methodology, golden similarity) for informational purposes only
                validation_results = {"schema_valid": True, "methodology_compliant": True, "schema_warnings": []}
                golden_similarity_score = 0.0
                
                if state.generated_survey:
                    try:
                        from src.services.validation_service import ValidationService
                        validation_service = ValidationService(fresh_db)
                        validation_results = await validation_service.validate_survey(
                            survey=state.generated_survey,
                            golden_examples=state.golden_examples,
                            rfq_text=state.rfq_text
                        )
                        
                        # Calculate golden similarity score
                        golden_similarity_score = await validation_service.calculate_golden_similarity(
                            survey=state.generated_survey,
                            golden_examples=state.golden_examples
                        )
                        self.logger.info(f"📊 [ValidatorAgent] Golden similarity score: {golden_similarity_score:.3f}")

                        # Log validation results but don't block workflow
                        if validation_results.get('schema_valid'):
                            self.logger.info(f"📋 [ValidatorAgent] Schema validation: PASSED")
                        else:
                            self.logger.info(f"⚠️ [ValidatorAgent] Schema validation: FAILED (non-blocking - survey will proceed)")
                            validation_results["schema_warnings"] = ["Survey JSON structure may need manual review"]

                        if validation_results.get('methodology_compliant'):
                            self.logger.info(f"📋 [ValidatorAgent] Methodology validation: PASSED")
                        else:
                            self.logger.info(f"⚠️ [ValidatorAgent] Methodology validation: FAILED (non-blocking - survey will proceed)")

                        if validation_results.get('text_requirements_valid'):
                            self.logger.info(f"📋 [ValidatorAgent] Text requirements validation: PASSED")
                        else:
                            self.logger.info(f"⚠️ [ValidatorAgent] Text requirements validation: FAILED (non-blocking - survey will proceed)")

                    except Exception as validation_error:
                        self.logger.warning(f"⚠️ [ValidatorAgent] Basic validation failed (non-blocking): {validation_error}")
                        validation_results["schema_warnings"] = [f"Validation error: {str(validation_error)}"]

                # Always continue workflow regardless of validation results
                result = {
                    "validation_results": validation_results,
                    "golden_similarity_score": golden_similarity_score,
                    "retry_count": state.retry_count,
                    "workflow_should_continue": True,
                    # Don't clear error_message if it was set by a previous node
                    "error_message": state.error_message if state.error_message else None
                }

                self.logger.info(f"✅ [ValidatorAgent] Basic validation completed, workflow continuing")

            finally:
                # Close the fresh database session
                try:
                    fresh_db.close()
                except Exception as e:
                    self.logger.warning(f"⚠️ [ValidatorAgent] Failed to close fresh database session: {e}")

            return result

        except Exception as e:
            self.logger.error(f"❌ [ValidatorAgent] Exception during validation: {str(e)}", exc_info=True)
            return {
                "error_message": f"Survey validation failed: {str(e)}",
                "validation_results": {"schema_valid": False, "methodology_compliant": False},
                "workflow_should_continue": True
            }

    async def _run_basic_validation(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Run basic structural validation without LLM calls when LLM evaluation is disabled
        """
        try:
            self.logger.info("🔧 [ValidatorAgent] Running basic structural validation...")
            
            survey = state.generated_survey
            sections = survey.get('sections', [])
            total_questions = 0
            
            # Basic structural checks
            validation_results = {
                "schema_valid": True,
                "methodology_compliant": True,
                "basic_checks_passed": True
            }
            
            # Check if survey has sections
            if not sections:
                self.logger.warning("⚠️ [ValidatorAgent] No sections found in survey")
                validation_results["schema_valid"] = False
                validation_results["basic_checks_passed"] = False
            
            # Count questions and check basic structure
            for section in sections:
                questions = section.get('questions', [])
                total_questions += len(questions)
                
                # Check if section has questions
                if not questions:
                    self.logger.warning(f"⚠️ [ValidatorAgent] Section '{section.get('id', 'unknown')}' has no questions")
                    validation_results["basic_checks_passed"] = False
                
                # Basic question structure validation
                for question in questions:
                    if not question.get('text'):
                        self.logger.warning("⚠️ [ValidatorAgent] Question missing text")
                        validation_results["basic_checks_passed"] = False
                    
                    if not question.get('type'):
                        self.logger.warning("⚠️ [ValidatorAgent] Question missing type")
                        validation_results["basic_checks_passed"] = False
            
            # Check minimum question count
            if total_questions < 1:
                self.logger.warning("⚠️ [ValidatorAgent] Survey has no questions")
                validation_results["basic_checks_passed"] = False
            
            # Create minimal pillar scores for basic validation
            pillar_scores = {
                "content_validity": 0.8 if validation_results["basic_checks_passed"] else 0.3,
                "methodological_rigor": 0.7 if validation_results["basic_checks_passed"] else 0.3,
                "respondent_experience": 0.8 if validation_results["basic_checks_passed"] else 0.3,
                "analytical_value": 0.7 if validation_results["basic_checks_passed"] else 0.3,
                "business_impact": 0.7 if validation_results["basic_checks_passed"] else 0.3,
                "weighted_score": 0.74 if validation_results["basic_checks_passed"] else 0.3
            }
            
            # Quality gate: basic validation passes if structural checks pass
            quality_gate_passed = validation_results["basic_checks_passed"]
            
            self.logger.info(f"✅ [ValidatorAgent] Basic validation completed - Quality gate: {'PASSED' if quality_gate_passed else 'FAILED'}")
            self.logger.info(f"📊 [ValidatorAgent] Survey has {total_questions} questions across {len(sections)} sections")
            
            return {
                "pillar_scores": pillar_scores,
                "quality_gate_passed": quality_gate_passed,
                "validation_results": validation_results,
                "retry_count": state.retry_count,
                "workflow_should_continue": True,
                # Don't clear error_message if it was set by a previous node
                "error_message": state.error_message if state.error_message else None,
                "evaluation_mode": "basic"
            }
            
        except Exception as e:
            self.logger.error(f"❌ [ValidatorAgent] Basic validation failed: {str(e)}", exc_info=True)
            return {
                "error_message": f"Basic validation failed: {str(e)}",
                "pillar_scores": {},
                "quality_gate_passed": False,
                "validation_results": {"schema_valid": False, "methodology_compliant": False},
                "retry_count": state.retry_count,
                "workflow_should_continue": True,
                "evaluation_mode": "basic"
            }


class SurgicalMergerNode:
    """Merges regenerated sections with preserved sections from previous survey"""
    
    def __init__(self, db: Session):
        self.db = db
        import logging
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, state: SurveyGenerationState) -> Dict[str, Any]:
        """
        Merge regenerated sections with preserved sections in surgical mode
        For non-surgical modes, return generated survey as-is
        """
        try:
            from src.workflows.state import RegenerationMode
            
            # Check if we're in surgical or targeted mode
            if state.regeneration_mode_type not in (RegenerationMode.SURGICAL, RegenerationMode.TARGETED):
                self.logger.info("🔬 [SurgicalMerger] Not in surgical/targeted mode, skipping merge")
                return {"generated_survey": state.generated_survey}
            
            if not state.surgical_analysis:
                self.logger.warning("⚠️ [SurgicalMerger] Surgical mode but no analysis available, skipping merge")
                return {"generated_survey": state.generated_survey}
            
            self.logger.info("🔬 [SurgicalMerger] Starting surgical merge...")
            self.logger.info(f"  - Sections to regenerate: {state.surgical_analysis['sections_to_regenerate']}")
            self.logger.info(f"  - Sections to preserve: {state.surgical_analysis['sections_to_preserve']}")
            
            # Get previous survey
            from src.database.models import Survey
            from uuid import UUID
            
            parent_survey = self.db.query(Survey).filter(
                Survey.id == state.parent_survey_id
            ).first()
            
            if not parent_survey or not parent_survey.final_output:
                self.logger.error("❌ [SurgicalMerger] Parent survey not found or has no final_output")
                return {
                    "generated_survey": state.generated_survey,
                    "error_message": "Parent survey not found for surgical merge"
                }
            
            # Merge regenerated sections with preserved sections
            from src.services.survey_merger_service import SurveyMergerService
            
            merger = SurveyMergerService()
            
            # Extract only regenerated sections from the generated survey
            regenerated_sections = []
            if state.generated_survey and 'sections' in state.generated_survey:
                for section in state.generated_survey['sections']:
                    section_id = section.get('id')
                    if section_id in state.surgical_analysis['sections_to_regenerate']:
                        regenerated_sections.append(section)
                        self.logger.info(f"  - Including regenerated section {section_id}: {section.get('title')}")
            
            if not regenerated_sections:
                self.logger.warning("⚠️ [SurgicalMerger] No regenerated sections found in generated survey")
                # If no sections were regenerated, use all sections from generated survey (if available)
                if state.generated_survey:
                    regenerated_sections = state.generated_survey.get('sections', [])
                else:
                    self.logger.error("❌ [SurgicalMerger] No generated survey available - generation must have failed")
                    return {
                        "generated_survey": None,
                        "error_message": "Survey generation failed - no survey data available for merging"
                    }
            
            # Perform merge
            merged_survey = merger.merge_surveys(
                previous_survey=parent_survey.final_output,
                regenerated_sections=regenerated_sections,
                preserve_section_ids=state.surgical_analysis['sections_to_preserve']
            )
            
            # Validate merged survey
            validation_result = merger.validate_merged_survey(merged_survey)
            
            if not validation_result['valid']:
                self.logger.error(f"❌ [SurgicalMerger] Merged survey validation failed: {validation_result['errors']}")
                return {
                    "generated_survey": state.generated_survey,  # Return unmerged survey
                    "error_message": f"Surgical merge validation failed: {', '.join(validation_result['errors'])}"
                }
            
            if validation_result['warnings']:
                self.logger.warning(f"⚠️ [SurgicalMerger] Merge warnings: {validation_result['warnings']}")
            
            self.logger.info("✅ [SurgicalMerger] Surgical merge completed successfully")
            self.logger.info(f"  - Total sections in merged survey: {len(merged_survey.get('sections', []))}")
            self.logger.info(f"  - Total questions: {merged_survey.get('metadata', {}).get('total_questions', 0)}")
            
            return {
                "generated_survey": merged_survey,
                "error_message": None
            }
            
        except Exception as e:
            self.logger.error(f"❌ [SurgicalMerger] Surgical merge failed: {str(e)}", exc_info=True)
            # On error, return the generated survey without merge
            return {
                "generated_survey": state.generated_survey,
                "error_message": f"Surgical merge failed: {str(e)}"
            }