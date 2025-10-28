"""
LLM Audit Service

This service provides comprehensive auditing for all LLM interactions across the system.
It tracks hyperparameters, prompts, performance metrics, and costs for every LLM call,
regardless of purpose or context.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from src.database.models import LLMAudit, LLMHyperparameterConfig, LLMPromptTemplate
from src.utils.error_messages import UserFriendlyError

logger = logging.getLogger(__name__)


class LLMAuditService:
    """Service for comprehensive LLM interaction auditing"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def _convert_raw_response_to_json(self, raw_response: str) -> str:
        """
        Convert raw response to valid JSON format if it's a Python dictionary string
        """
        if not raw_response:
            return raw_response
        
        try:
            # Try to parse as Python dictionary string
            import ast
            parsed_dict = ast.literal_eval(raw_response)
            
            if isinstance(parsed_dict, dict):
                # Convert to JSON string
                import json
                return json.dumps(parsed_dict, indent=2)
            else:
                # Not a dictionary, return as-is
                return raw_response
        except (ValueError, SyntaxError, TypeError):
            # Not a Python dictionary string, return as-is
            return raw_response

    def _parse_raw_response_to_dict(self, raw_response: str) -> Any:
        """
        Parse raw response string to dictionary for inspection
        """
        if not raw_response:
            return None
        
        try:
            # Try to parse as JSON first
            import json
            return json.loads(raw_response)
        except json.JSONDecodeError:
            try:
                # Try to parse as Python dictionary string
                import ast
                parsed_dict = ast.literal_eval(raw_response)
                if isinstance(parsed_dict, dict):
                    return parsed_dict
                else:
                    return raw_response
            except (ValueError, SyntaxError, TypeError):
                # Not a dictionary, return as-is
                return raw_response

    async def log_llm_interaction(
        self,
        interaction_id: str,
        model_name: str,
        model_provider: str,
        purpose: str,
        input_prompt: str,
        output_content: str = None,
        raw_response: str = None,
        sub_purpose: str = None,
        context_type: str = None,
        parent_workflow_id: str = None,
        parent_survey_id: str = None,
        parent_rfq_id: str = None,
        hyperparameters: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        success: bool = True,
        error_message: str = None
    ) -> str:
        logger.info(f"🚀 [LLMAuditService] Starting log_llm_interaction for {interaction_id}")
        logger.info(f"🔍 [LLMAuditService] db_session available: {self.db_session is not None}")
        logger.info(f"🔍 [LLMAuditService] purpose: {purpose}, parent_survey_id: {parent_survey_id}, parent_rfq_id: {parent_rfq_id}")
        logger.info(f"🔍 [LLMAuditService] parent_survey_id type: {type(parent_survey_id)}, parent_rfq_id type: {type(parent_rfq_id)}")
        """
        Log an LLM interaction to the audit system using an independent database session.
        
        This method always uses an independent database session to ensure audit records
        are persisted even if the parent workflow transaction is rolled back.
        
        Args:
            interaction_id: Unique identifier for this interaction
            model_name: Name of the LLM model used
            model_provider: Provider of the model (openai, replicate, anthropic, etc.)
            purpose: Primary purpose (survey_generation, evaluation, field_extraction, etc.)
            input_prompt: The prompt sent to the LLM
            output_content: The processed response from the LLM
            raw_response: The raw response from the LLM before any processing
            sub_purpose: Specific sub-purpose (content_validity, methodological_rigor, etc.)
            context_type: Type of context (generation, evaluation, validation, analysis)
            parent_workflow_id: Optional parent workflow ID
            parent_survey_id: Optional parent survey ID
            parent_rfq_id: Optional parent RFQ ID
            hyperparameters: Dictionary of hyperparameters used
            performance_metrics: Dictionary of performance metrics
            metadata: Additional context-specific metadata
            tags: List of searchable tags
            success: Whether the interaction was successful
            error_message: Error message if failed
            
        Returns:
            The ID of the created audit record
        """
        # CRITICAL: Always use an independent database session for audit logging
        # This ensures audit records persist even if the parent transaction is rolled back
        audit_session = None
        try:
            from src.database.connection import get_independent_db_session
            # Create an independent session that won't be affected by parent rollbacks
            audit_session = get_independent_db_session()
            logger.info(f"✅ [LLMAuditService] Created independent database session for audit")
        except ImportError as e:
            logger.error(f"❌ [LLMAuditService] Failed to import get_independent_db_session: {e}")
            # Fallback - will try to use existing session or fail gracefully
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to create independent session: {e}")
            import traceback
            logger.error(f"❌ [LLMAuditService] Traceback: {traceback.format_exc()}")
            # Don't fail the operation - will proceed to next try block
        
        try:
            # Create an independent session that won't be affected by parent rollbacks if not already created
            if audit_session is None:
                from src.database.connection import get_independent_db_session
                audit_session = get_independent_db_session()
            
            # Log the parameters being passed for debugging
            logger.info(f"🔍 [LLMAuditService] Logging LLM interaction:")
            logger.info(f"🔍 [LLMAuditService] Interaction ID: {interaction_id}")
            logger.info(f"🔍 [LLMAuditService] Purpose: {purpose}")
            logger.info(f"🔍 [LLMAuditService] Parent Survey ID: {parent_survey_id}")
            logger.info(f"🔍 [LLMAuditService] Parent RFQ ID: {parent_rfq_id}")
            logger.info(f"🔍 [LLMAuditService] Parent Workflow ID: {parent_workflow_id}")
            logger.info(f"🔍 [LLMAuditService] Context Type: {context_type}")
            logger.info(f"🔍 [LLMAuditService] Using independent session: {id(audit_session)}")
            
            # Extract hyperparameters
            hyperparams = hyperparameters or {}
            temperature = hyperparams.get('temperature')
            top_p = hyperparams.get('top_p')
            max_tokens = hyperparams.get('max_tokens')
            frequency_penalty = hyperparams.get('frequency_penalty')
            presence_penalty = hyperparams.get('presence_penalty')
            stop_sequences = hyperparams.get('stop_sequences', [])
            
            # Extract performance metrics
            perf_metrics = performance_metrics or {}
            response_time_ms = perf_metrics.get('response_time_ms')
            cost_usd = perf_metrics.get('cost_usd')
            input_tokens = perf_metrics.get('input_tokens')
            output_tokens = perf_metrics.get('output_tokens')
            
            # Convert parent_survey_id to UUID if needed (defensive handling)
            survey_uuid = None
            if parent_survey_id is not None:
                try:
                    # Handle various input types
                    if isinstance(parent_survey_id, uuid.UUID):
                        survey_uuid = parent_survey_id
                    elif isinstance(parent_survey_id, str) and parent_survey_id.strip():
                        survey_uuid = uuid.UUID(parent_survey_id.strip())
                    elif isinstance(parent_survey_id, (int, float)):
                        # Convert numeric IDs to string first
                        survey_uuid = uuid.UUID(str(int(parent_survey_id)))
                    else:
                        logger.warning(f"Unsupported Survey ID type: {type(parent_survey_id)}")
                        survey_uuid = None
                except (ValueError, AttributeError, TypeError) as e:
                    logger.warning(f"Invalid Survey ID format: {parent_survey_id} ({e})")
                    survey_uuid = None
            
            # Convert parent_rfq_id to UUID if needed (defensive handling)
            rfq_uuid = None
            if parent_rfq_id is not None:
                try:
                    # Handle various input types
                    if isinstance(parent_rfq_id, uuid.UUID):
                        rfq_uuid = parent_rfq_id
                    elif isinstance(parent_rfq_id, str) and parent_rfq_id.strip():
                        rfq_uuid = uuid.UUID(parent_rfq_id.strip())
                    elif isinstance(parent_rfq_id, (int, float)):
                        # Convert numeric IDs to string first
                        rfq_uuid = uuid.UUID(str(int(parent_rfq_id)))
                    else:
                        logger.warning(f"Unsupported RFQ ID type: {type(parent_rfq_id)}")
                        rfq_uuid = None
                except (ValueError, AttributeError, TypeError) as e:
                    logger.warning(f"Invalid RFQ ID format: {parent_rfq_id} ({e})")
                    rfq_uuid = None
            
            # Convert raw_response to JSON format if it's a Python dictionary string
            json_raw_response = self._convert_raw_response_to_json(raw_response)
            
            # Log the input prompt being stored
            logger.info(f"🔍 [LLMAuditService] Storing input_prompt (length: {len(input_prompt)})")
            logger.info(f"🔍 [LLMAuditService] input_prompt preview: {input_prompt[:200]}...")
            
            # Create audit record
            audit_record = LLMAudit(
                interaction_id=interaction_id,
                parent_workflow_id=parent_workflow_id,
                parent_survey_id=survey_uuid,
                parent_rfq_id=rfq_uuid,
                model_name=model_name,
                model_provider=model_provider,
                model_version=hyperparams.get('model_version'),
                purpose=purpose,
                sub_purpose=sub_purpose,
                context_type=context_type,
                input_prompt=input_prompt,
                input_tokens=input_tokens,
                output_content=output_content,
                output_tokens=output_tokens,
                raw_response=json_raw_response,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop_sequences=stop_sequences,
                response_time_ms=response_time_ms,
                cost_usd=cost_usd,
                success=success,
                error_message=error_message,
                interaction_metadata=metadata or {},
                tags=tags or []
            )
            
            # Add and commit using the independent session
            logger.info(f"🔍 [LLMAuditService] Adding audit record to session: {interaction_id}")
            audit_session.add(audit_record)
            logger.info(f"🔍 [LLMAuditService] Committing audit record: {interaction_id}")
            audit_session.commit()
            logger.info(f"🔍 [LLMAuditService] Commit successful: {interaction_id}")
            
            logger.info(f"✅ [LLMAuditService] Logged LLM interaction: {interaction_id} ({purpose})")
            audit_record_id = str(audit_record.id)
            logger.info(f"🔍 [LLMAuditService] Audit record ID: {audit_record_id}")
            
            return audit_record_id
            
        except Exception as e:
            import traceback
            logger.error(f"❌ [LLMAuditService] Failed to log LLM interaction: {str(e)}")
            logger.error(f"❌ [LLMAuditService] Exception type: {type(e).__name__}")
            logger.error(f"❌ [LLMAuditService] Traceback:\n{traceback.format_exc()}")
            if audit_session:
                try:
                    logger.info(f"🔍 [LLMAuditService] Rolling back session")
                    audit_session.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ [LLMAuditService] Rollback failed: {str(rollback_error)}")
            raise
        finally:
            # Always close the independent session
            if audit_session:
                try:
                    audit_session.close()
                    logger.debug(f"🔒 [LLMAuditService] Closed independent audit session: {id(audit_session)}")
                except:
                    pass  # Ignore close errors
    
    async def get_hyperparameter_config(
        self,
        purpose: str,
        sub_purpose: str = None,
        config_name: str = None
    ) -> Optional[LLMHyperparameterConfig]:
        """
        Get hyperparameter configuration for a specific purpose
        
        Args:
            purpose: Primary purpose (survey_generation, evaluation, etc.)
            sub_purpose: Specific sub-purpose (optional)
            config_name: Specific config name (optional)
            
        Returns:
            LLMHyperparameterConfig or None
        """
        try:
            query = self.db_session.query(LLMHyperparameterConfig).filter(
                and_(
                    LLMHyperparameterConfig.purpose == purpose,
                    LLMHyperparameterConfig.is_active == True
                )
            )
            
            if sub_purpose:
                query = query.filter(LLMHyperparameterConfig.sub_purpose == sub_purpose)
            
            if config_name:
                query = query.filter(LLMHyperparameterConfig.config_name == config_name)
            else:
                # Prefer default config if no specific name provided
                query = query.filter(LLMHyperparameterConfig.is_default == True)
            
            return query.first()
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to get hyperparameter config: {str(e)}")
            return None
    
    async def get_prompt_template(
        self,
        purpose: str,
        sub_purpose: str = None,
        template_name: str = None
    ) -> Optional[LLMPromptTemplate]:
        """
        Get prompt template for a specific purpose
        
        Args:
            purpose: Primary purpose (survey_generation, evaluation, etc.)
            sub_purpose: Specific sub-purpose (optional)
            template_name: Specific template name (optional)
            
        Returns:
            LLMPromptTemplate or None
        """
        try:
            query = self.db_session.query(LLMPromptTemplate).filter(
                and_(
                    LLMPromptTemplate.purpose == purpose,
                    LLMPromptTemplate.is_active == True
                )
            )
            
            if sub_purpose:
                query = query.filter(LLMPromptTemplate.sub_purpose == sub_purpose)
            
            if template_name:
                query = query.filter(LLMPromptTemplate.template_name == template_name)
            else:
                # Prefer default template if no specific name provided
                query = query.filter(LLMPromptTemplate.is_default == True)
            
            return query.first()
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to get prompt template: {str(e)}")
            return None
    
    async def get_audit_records(
        self,
        purpose: str = None,
        sub_purpose: str = None,
        model_name: str = None,
        success: bool = None,
        parent_workflow_id: str = None,
        parent_survey_id: str = None,
        parent_rfq_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[LLMAudit], int]:
        """
        Get audit records with filtering options
        
        Returns:
            Tuple of (audit_records, total_count)
        """
        try:
            query = self.db_session.query(LLMAudit)
            
            # Apply filters
            if purpose:
                query = query.filter(LLMAudit.purpose == purpose)
            if sub_purpose:
                query = query.filter(LLMAudit.sub_purpose == sub_purpose)
            if model_name:
                query = query.filter(LLMAudit.model_name == model_name)
            if success is not None:
                query = query.filter(LLMAudit.success == success)
            if parent_workflow_id:
                query = query.filter(LLMAudit.parent_workflow_id == parent_workflow_id)
            if parent_survey_id:
                query = query.filter(LLMAudit.parent_survey_id == parent_survey_id)
            if parent_rfq_id:
                query = query.filter(LLMAudit.parent_rfq_id == parent_rfq_id)
            if start_date:
                query = query.filter(LLMAudit.created_at >= start_date)
            if end_date:
                query = query.filter(LLMAudit.created_at <= end_date)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            audit_records = query.order_by(desc(LLMAudit.created_at)).offset(offset).limit(limit).all()
            
            return audit_records, total_count
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to get audit records: {str(e)}")
            return [], 0
    
    async def get_interaction(self, interaction_id: str) -> Optional[LLMAudit]:
        """
        Get a specific LLM interaction by interaction_id
        
        Args:
            interaction_id: The interaction ID to look up
            
        Returns:
            The LLMAudit record if found, None otherwise
        """
        try:
            logger.info(f"🔍 [LLMAuditService] Looking up interaction: {interaction_id}")
            
            record = self.db_session.query(LLMAudit).filter(
                LLMAudit.interaction_id == interaction_id
            ).first()
            
            if record:
                logger.info(f"✅ [LLMAuditService] Found interaction: {interaction_id}")
            else:
                logger.warning(f"⚠️ [LLMAuditService] Interaction not found: {interaction_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to get interaction {interaction_id}: {str(e)}")
            return None
    
    async def get_cost_summary(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        purpose: str = None,
        model_name: str = None
    ) -> Dict[str, Any]:
        """
        Get cost summary for LLM interactions
        
        Returns:
            Dictionary with cost breakdown
        """
        try:
            query = self.db_session.query(LLMAudit)
            
            # Apply filters
            if start_date:
                query = query.filter(LLMAudit.created_at >= start_date)
            if end_date:
                query = query.filter(LLMAudit.created_at <= end_date)
            if purpose:
                query = query.filter(LLMAudit.purpose == purpose)
            if model_name:
                query = query.filter(LLMAudit.model_name == model_name)
            
            # Calculate totals
            total_cost = query.filter(LLMAudit.cost_usd.isnot(None)).with_entities(
                func.sum(LLMAudit.cost_usd)
            ).scalar() or Decimal('0.0')
            
            total_interactions = query.count()
            successful_interactions = query.filter(LLMAudit.success == True).count()
            
            # Cost by purpose
            cost_by_purpose = query.filter(LLMAudit.cost_usd.isnot(None)).with_entities(
                LLMAudit.purpose,
                func.sum(LLMAudit.cost_usd).label('total_cost'),
                func.count(LLMAudit.id).label('interaction_count')
            ).group_by(LLMAudit.purpose).all()
            
            # Cost by model
            cost_by_model = query.filter(LLMAudit.cost_usd.isnot(None)).with_entities(
                LLMAudit.model_name,
                func.sum(LLMAudit.cost_usd).label('total_cost'),
                func.count(LLMAudit.id).label('interaction_count')
            ).group_by(LLMAudit.model_name).all()
            
            return {
                'total_cost_usd': float(total_cost),
                'total_interactions': total_interactions,
                'successful_interactions': successful_interactions,
                'success_rate': successful_interactions / total_interactions if total_interactions > 0 else 0.0,
                'cost_by_purpose': [
                    {
                        'purpose': row.purpose,
                        'total_cost_usd': float(row.total_cost),
                        'interaction_count': row.interaction_count
                    }
                    for row in cost_by_purpose
                ],
                'cost_by_model': [
                    {
                        'model_name': row.model_name,
                        'total_cost_usd': float(row.total_cost),
                        'interaction_count': row.interaction_count
                    }
                    for row in cost_by_model
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to get cost summary: {str(e)}")
            return {
                'total_cost_usd': 0.0,
                'total_interactions': 0,
                'successful_interactions': 0,
                'success_rate': 0.0,
                'cost_by_purpose': [],
                'cost_by_model': []
            }
    
    async def create_hyperparameter_config(
        self,
        config_name: str,
        purpose: str,
        hyperparameters: Dict[str, Any],
        sub_purpose: str = None,
        preferred_models: List[str] = None,
        fallback_models: List[str] = None,
        description: str = None,
        is_default: bool = False
    ) -> str:
        """
        Create a new hyperparameter configuration
        
        Returns:
            The ID of the created configuration
        """
        try:
            config = LLMHyperparameterConfig(
                config_name=config_name,
                purpose=purpose,
                sub_purpose=sub_purpose,
                temperature=hyperparameters.get('temperature', 0.7),
                top_p=hyperparameters.get('top_p', 0.9),
                max_tokens=hyperparameters.get('max_tokens', 8000),
                frequency_penalty=hyperparameters.get('frequency_penalty', 0.0),
                presence_penalty=hyperparameters.get('presence_penalty', 0.0),
                stop_sequences=hyperparameters.get('stop_sequences', []),
                preferred_models=preferred_models or [],
                fallback_models=fallback_models or [],
                description=description,
                is_default=is_default
            )
            
            self.db_session.add(config)
            self.db_session.commit()
            
            logger.info(f"✅ [LLMAuditService] Created hyperparameter config: {config_name}")
            return str(config.id)
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to create hyperparameter config: {str(e)}")
            self.db_session.rollback()
            raise
    
    async def create_prompt_template(
        self,
        template_name: str,
        purpose: str,
        system_prompt_template: str,
        user_prompt_template: str = None,
        sub_purpose: str = None,
        template_variables: Dict[str, Any] = None,
        description: str = None,
        is_default: bool = False
    ) -> str:
        """
        Create a new prompt template
        
        Returns:
            The ID of the created template
        """
        try:
            template = LLMPromptTemplate(
                template_name=template_name,
                purpose=purpose,
                sub_purpose=sub_purpose,
                system_prompt_template=system_prompt_template,
                user_prompt_template=user_prompt_template,
                template_variables=template_variables or {},
                description=description,
                is_default=is_default
            )
            
            self.db_session.add(template)
            self.db_session.commit()
            
            logger.info(f"✅ [LLMAuditService] Created prompt template: {template_name}")
            return str(template.id)
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to create prompt template: {str(e)}")
            self.db_session.rollback()
            raise


class LLMAuditContext:
    """Context manager for automatic LLM interaction auditing"""
    
    def __init__(
        self,
        audit_service: LLMAuditService,
        interaction_id: str,
        model_name: str,
        model_provider: str,
        purpose: str,
        input_prompt: str,
        sub_purpose: str = None,
        context_type: str = None,
        parent_workflow_id: str = None,
        parent_survey_id: str = None,
        parent_rfq_id: str = None,
        hyperparameters: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ):
        self.audit_service = audit_service
        self.interaction_id = interaction_id
        self.model_name = model_name
        self.model_provider = model_provider
        self.purpose = purpose
        self.input_prompt = input_prompt
        self.sub_purpose = sub_purpose
        self.context_type = context_type
        self.parent_workflow_id = parent_workflow_id
        self.parent_survey_id = parent_survey_id
        self.parent_rfq_id = parent_rfq_id
        self.hyperparameters = hyperparameters or {}
        self.metadata = metadata or {}
        self.tags = tags or []
        
        self.start_time = None
        self.output_content = None
        self.raw_response = None
        self.success = True
        self.error_message = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"🚀 [LLMAuditContext] __aexit__ called for {self.interaction_id}")
        logger.info(f"🔍 [LLMAuditContext] Exception type: {exc_type}")
        logger.info(f"🔍 [LLMAuditContext] parent_survey_id: {self.parent_survey_id}")
        logger.info(f"🔍 [LLMAuditContext] parent_rfq_id: {self.parent_rfq_id}")
        
        # Calculate response time
        response_time_ms = None
        if self.start_time:
            response_time_ms = int((time.time() - self.start_time) * 1000)
        
        # Determine success and error message
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val) if exc_val else str(exc_type)
            logger.warning(f"⚠️ [LLMAuditContext] Exception occurred: {self.error_message}")
        
        # Prepare performance metrics
        performance_metrics = {
            'response_time_ms': response_time_ms,
            'input_tokens': self.metadata.get('input_tokens'),
            'output_tokens': self.metadata.get('output_tokens'),
            'cost_usd': self.metadata.get('cost_usd')
        }
        logger.info(f"🔍 [LLMAuditContext] Performance metrics: {performance_metrics}")
        
        # Log the interaction
        try:
            logger.info(f"🔍 [LLMAuditContext] Calling audit_service.log_llm_interaction for {self.interaction_id}")
            logger.info(f"🔍 [LLMAuditContext] Parameters: purpose={self.purpose}, parent_survey_id={self.parent_survey_id}, parent_rfq_id={self.parent_rfq_id}")
            await self.audit_service.log_llm_interaction(
                interaction_id=self.interaction_id,
                model_name=self.model_name,
                model_provider=self.model_provider,
                purpose=self.purpose,
                input_prompt=self.input_prompt,
                output_content=self.output_content,
                raw_response=self.raw_response,
                sub_purpose=self.sub_purpose,
                context_type=self.context_type,
                parent_workflow_id=self.parent_workflow_id,
                parent_survey_id=self.parent_survey_id,
                parent_rfq_id=self.parent_rfq_id,
                hyperparameters=self.hyperparameters,
                performance_metrics=performance_metrics,
                metadata=self.metadata,
                tags=self.tags,
                success=self.success,
                error_message=self.error_message
            )
            logger.info(f"✅ [LLMAuditContext] Successfully logged interaction {self.interaction_id}")
        except Exception as e:
            import traceback
            logger.error(f"❌ [LLMAuditContext] Failed to log interaction: {str(e)}")
            logger.error(f"❌ [LLMAuditContext] Exception type: {type(e).__name__}")
            logger.error(f"❌ [LLMAuditContext] Traceback:\n{traceback.format_exc()}")
            raise
    
    def set_output(self, output_content: str, input_tokens: int = None, output_tokens: int = None, cost_usd: float = None):
        """Set the processed output content and additional metrics"""
        self.output_content = output_content
        if input_tokens is not None:
            self.metadata['input_tokens'] = input_tokens
        if output_tokens is not None:
            self.metadata['output_tokens'] = output_tokens
        if cost_usd is not None:
            self.metadata['cost_usd'] = cost_usd
    
    def set_raw_response(self, raw_response: str):
        """Set the raw response from the LLM before any processing"""
        self.raw_response = raw_response
    
    async def log_parsing_failure(
        self,
        raw_response: str,
        service_name: str,
        error_message: str,
        interaction_id: Optional[str] = None,
        model_name: Optional[str] = None,
        model_provider: Optional[str] = None,
        purpose: Optional[str] = None,
        input_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Emergency logging for parsing failures.
        Creates independent session even when parent session is None.
        
        Args:
            raw_response: The raw LLM response that failed to parse
            service_name: Name of the service that failed
            error_message: The error message from the failure
            interaction_id: Optional interaction ID for tracking
            model_name: Optional model name
            model_provider: Optional model provider
            purpose: Optional purpose (survey_generation, evaluation, etc.)
            input_prompt: Optional input prompt
            context: Additional context about the failure
            
        Returns:
            The interaction_id (generated if not provided)
        """
        import uuid
        
        if not interaction_id:
            interaction_id = f"parsing_failure_{uuid.uuid4().hex[:8]}"
        
        logger.warning(
            f"⚠️ [LLMAuditService] Logging parsing failure: {service_name} - {error_message}"
        )
        
        try:
            # Use independent session to ensure logging even if parent session fails
            from src.database.connection import get_independent_db_session
            
            audit_session = get_independent_db_session()
            
            try:
                # Create audit record for the failure
                await self.log_llm_interaction(
                    interaction_id=interaction_id,
                    model_name=model_name or "unknown",
                    model_provider=model_provider or "unknown",
                    purpose=purpose or "parsing_failure",
                    input_prompt=input_prompt or "",
                    output_content="",
                    raw_response=raw_response,
                    sub_purpose=f"parsing_failure_{service_name}",
                    context_type="parsing_failure",
                    hyperparameters={},
                    performance_metrics={},
                    metadata={
                        "service_name": service_name,
                        "error_message": error_message,
                        "parsing_failed": True,
                        **(context or {}),
                    },
                    tags=["parsing_failure", service_name],
                    success=False,
                    error_message=error_message,
                )
                
                logger.info(
                    f"✅ [LLMAuditService] Parsing failure logged: {interaction_id}"
                )
                return interaction_id
                
            finally:
                audit_session.close()
                
        except Exception as e:
            logger.error(
                f"❌ [LLMAuditService] Failed to log parsing failure: {str(e)}"
            )
            # Re-raise so emergency_audit can try file logging
            raise
    
    def can_create_golden_pair(self, audit_record: LLMAudit) -> dict:
        """
        Check if an audit record can be used to create a golden pair.
        Returns dict with: {can_create: bool, reason: str, warnings: list}
        """
        if not audit_record.success:
            return {"can_create": False, "reason": "Interaction failed", "warnings": []}
        
        if audit_record.purpose != "document_parsing" or audit_record.sub_purpose != "survey_conversion":
            return {"can_create": False, "reason": "Not a document parsing/survey conversion record", "warnings": []}
        
        warnings = []
        
        # Check for RFQ text
        has_rfq = False
        if audit_record.interaction_metadata:
            has_rfq = bool(audit_record.interaction_metadata.get('document_text') or 
                          audit_record.interaction_metadata.get('rfq_text'))
        
        if not has_rfq and not audit_record.input_prompt:
            return {"can_create": False, "reason": "No RFQ text available", "warnings": []}
        
        # Check for survey JSON
        has_survey = False
        if audit_record.raw_response:
            # Parse raw_response string to dict first
            parsed_response = self._parse_raw_response_to_dict(audit_record.raw_response)
            if isinstance(parsed_response, dict):
                has_survey = bool('final_output' in parsed_response or 
                                'sections' in parsed_response or 
                                'questions' in parsed_response)
        
        if not has_survey:
            return {"can_create": False, "reason": "No survey JSON available", "warnings": []}
        
        # Check quality score
        quality_score = None
        parsed_response = self._parse_raw_response_to_dict(audit_record.raw_response)
        if isinstance(parsed_response, dict):
            final_output = parsed_response.get('final_output', parsed_response)
            if isinstance(final_output, dict):
                metadata = final_output.get('metadata', {})
                if isinstance(metadata, dict):
                    quality_score = metadata.get('quality_score')
        
        if quality_score is None:
            warnings.append("No quality score found in survey metadata")
        elif quality_score < 0.7:
            warnings.append(f"Low quality score: {quality_score}")
        
        return {"can_create": True, "reason": "", "warnings": warnings}