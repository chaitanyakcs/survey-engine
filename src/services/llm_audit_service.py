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
    
    async def log_llm_interaction(
        self,
        interaction_id: str,
        model_name: str,
        model_provider: str,
        purpose: str,
        input_prompt: str,
        output_content: str = None,
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
        """
        Log an LLM interaction to the audit system
        
        Args:
            interaction_id: Unique identifier for this interaction
            model_name: Name of the LLM model used
            model_provider: Provider of the model (openai, replicate, anthropic, etc.)
            purpose: Primary purpose (survey_generation, evaluation, field_extraction, etc.)
            input_prompt: The prompt sent to the LLM
            output_content: The response from the LLM
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
        try:
            # Log the parameters being passed for debugging
            logger.info(f"🔍 [LLMAuditService] Logging LLM interaction:")
            logger.info(f"🔍 [LLMAuditService] Interaction ID: {interaction_id}")
            logger.info(f"🔍 [LLMAuditService] Purpose: {purpose}")
            logger.info(f"🔍 [LLMAuditService] Parent Survey ID: {parent_survey_id}")
            logger.info(f"🔍 [LLMAuditService] Parent RFQ ID: {parent_rfq_id}")
            logger.info(f"🔍 [LLMAuditService] Parent Workflow ID: {parent_workflow_id}")
            logger.info(f"🔍 [LLMAuditService] Context Type: {context_type}")
            
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
            
            # Convert parent_rfq_id to UUID if provided
            rfq_uuid = None
            if parent_rfq_id:
                try:
                    rfq_uuid = uuid.UUID(parent_rfq_id)
                except ValueError:
                    logger.warning(f"Invalid RFQ ID format: {parent_rfq_id}")
            
            # Create audit record
            audit_record = LLMAudit(
                interaction_id=interaction_id,
                parent_workflow_id=parent_workflow_id,
                parent_survey_id=parent_survey_id,
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
            
            self.db_session.add(audit_record)
            
            # Commit the audit record to ensure it's persisted
            try:
                self.db_session.commit()
                logger.info(f"✅ [LLMAuditService] Logged LLM interaction: {interaction_id} ({purpose})")
                return str(audit_record.id)
            except Exception as commit_error:
                logger.warning(f"⚠️ [LLMAuditService] Failed to commit audit record, rolling back: {str(commit_error)}")
                self.db_session.rollback()
                # Try to create a new session for audit logging
                try:
                    from src.database.connection import get_db
                    audit_session = next(get_db())
                    audit_session.add(audit_record)
                    audit_session.commit()
                    logger.info(f"✅ [LLMAuditService] Logged LLM interaction with new session: {interaction_id} ({purpose})")
                    return str(audit_record.id)
                except Exception as retry_error:
                    logger.error(f"❌ [LLMAuditService] Failed to log with new session: {str(retry_error)}")
                    raise
            
        except Exception as e:
            logger.error(f"❌ [LLMAuditService] Failed to log LLM interaction: {str(e)}")
            try:
                self.db_session.rollback()
            except:
                pass  # Ignore rollback errors
            raise
    
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
                max_tokens=hyperparameters.get('max_tokens', 4000),
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
        self.success = True
        self.error_message = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Calculate response time
        response_time_ms = None
        if self.start_time:
            response_time_ms = int((time.time() - self.start_time) * 1000)
        
        # Determine success and error message
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val) if exc_val else str(exc_type)
        
        # Prepare performance metrics
        performance_metrics = {
            'response_time_ms': response_time_ms,
            'input_tokens': self.metadata.get('input_tokens'),
            'output_tokens': self.metadata.get('output_tokens'),
            'cost_usd': self.metadata.get('cost_usd')
        }
        
        # Log the interaction
        try:
            await self.audit_service.log_llm_interaction(
                interaction_id=self.interaction_id,
                model_name=self.model_name,
                model_provider=self.model_provider,
                purpose=self.purpose,
                input_prompt=self.input_prompt,
                output_content=self.output_content,
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
        except Exception as e:
            logger.error(f"❌ [LLMAuditContext] Failed to log interaction: {str(e)}")
    
    def set_output(self, output_content: str, input_tokens: int = None, output_tokens: int = None, cost_usd: float = None):
        """Set the output content and additional metrics"""
        self.output_content = output_content
        if input_tokens is not None:
            self.metadata['input_tokens'] = input_tokens
        if output_tokens is not None:
            self.metadata['output_tokens'] = output_tokens
        if cost_usd is not None:
            self.metadata['cost_usd'] = cost_usd
