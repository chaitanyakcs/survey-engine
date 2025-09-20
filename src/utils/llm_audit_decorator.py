"""
LLM Audit Decorator

This module provides decorators and utilities for automatic LLM interaction auditing.
It can be used to wrap LLM calls and automatically track them in the audit system.
"""

import uuid
import time
import asyncio
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable, Union
from sqlalchemy.orm import Session

from src.services.llm_audit_service import LLMAuditService, LLMAuditContext
from src.database import get_db

logger = logging.getLogger(__name__)


def audit_llm_call(
    purpose: str,
    sub_purpose: str = None,
    context_type: str = None,
    model_name: str = None,
    model_provider: str = None,
    hyperparameters: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None,
    tags: list = None,
    parent_workflow_id: str = None,
    parent_survey_id: str = None,
    parent_rfq_id: str = None
):
    """
    Decorator for automatically auditing LLM calls
    
    Args:
        purpose: Primary purpose (survey_generation, evaluation, field_extraction, etc.)
        sub_purpose: Specific sub-purpose (content_validity, methodological_rigor, etc.)
        context_type: Type of context (generation, evaluation, validation, analysis)
        model_name: Name of the LLM model (can be overridden at runtime)
        model_provider: Provider of the model (can be overridden at runtime)
        hyperparameters: Default hyperparameters (can be overridden at runtime)
        metadata: Default metadata (can be overridden at runtime)
        tags: Default tags (can be overridden at runtime)
        parent_workflow_id: Parent workflow ID (can be overridden at runtime)
        parent_survey_id: Parent survey ID (can be overridden at runtime)
        parent_rfq_id: Parent RFQ ID (can be overridden at runtime)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate unique interaction ID
            interaction_id = f"{purpose}_{uuid.uuid4().hex[:8]}"
            
            # Extract parameters from function call
            prompt = kwargs.get('prompt') or kwargs.get('input_prompt') or str(args[0] if args else "")
            
            # Get database session
            db = next(get_db())
            audit_service = LLMAuditService(db)
            
            # Merge default and runtime parameters
            runtime_hyperparameters = kwargs.get('hyperparameters', {})
            final_hyperparameters = {**(hyperparameters or {}), **runtime_hyperparameters}
            
            runtime_metadata = kwargs.get('metadata', {})
            final_metadata = {**(metadata or {}), **runtime_metadata}
            
            runtime_tags = kwargs.get('tags', [])
            final_tags = (tags or []) + runtime_tags
            
            # Get model info from kwargs or use defaults
            final_model_name = kwargs.get('model_name') or model_name or "unknown"
            final_model_provider = kwargs.get('model_provider') or model_provider or "unknown"
            
            # Get parent IDs from kwargs or use defaults
            final_parent_workflow_id = kwargs.get('parent_workflow_id') or parent_workflow_id
            final_parent_survey_id = kwargs.get('parent_survey_id') or parent_survey_id
            final_parent_rfq_id = kwargs.get('parent_rfq_id') or parent_rfq_id
            
            # Create audit context
            async with LLMAuditContext(
                audit_service=audit_service,
                interaction_id=interaction_id,
                model_name=final_model_name,
                model_provider=final_model_provider,
                purpose=purpose,
                input_prompt=prompt,
                sub_purpose=sub_purpose,
                context_type=context_type,
                parent_workflow_id=final_parent_workflow_id,
                parent_survey_id=final_parent_survey_id,
                parent_rfq_id=final_parent_rfq_id,
                hyperparameters=final_hyperparameters,
                metadata=final_metadata,
                tags=final_tags
            ) as audit_context:
                try:
                    # Call the original function
                    result = await func(*args, **kwargs)
                    
                    # Extract output content and metrics from result
                    if isinstance(result, dict):
                        output_content = result.get('content') or result.get('response') or str(result)
                        input_tokens = result.get('input_tokens')
                        output_tokens = result.get('output_tokens')
                        cost_usd = result.get('cost_usd')
                        
                        audit_context.set_output(
                            output_content=output_content,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            cost_usd=cost_usd
                        )
                    else:
                        audit_context.set_output(output_content=str(result))
                    
                    return result
                    
                except Exception as e:
                    # The audit context will handle logging the error
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, run in async context
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LLMAuditWrapper:
    """Wrapper class for LLM clients to automatically audit all calls"""
    
    def __init__(
        self,
        llm_client,
        purpose: str,
        sub_purpose: str = None,
        context_type: str = None,
        model_name: str = None,
        model_provider: str = None,
        default_hyperparameters: Dict[str, Any] = None,
        default_metadata: Dict[str, Any] = None,
        default_tags: list = None
    ):
        self.llm_client = llm_client
        self.purpose = purpose
        self.sub_purpose = sub_purpose
        self.context_type = context_type
        self.model_name = model_name or getattr(llm_client, 'model', 'unknown')
        self.model_provider = model_provider or getattr(llm_client, 'provider', 'unknown')
        self.default_hyperparameters = default_hyperparameters or {}
        self.default_metadata = default_metadata or {}
        self.default_tags = default_tags or []
    
    async def generate(
        self,
        prompt: str,
        hyperparameters: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        tags: list = None,
        parent_workflow_id: str = None,
        parent_survey_id: str = None,
        parent_rfq_id: str = None,
        **kwargs
    ):
        """Generate text with automatic auditing"""
        interaction_id = f"{self.purpose}_{uuid.uuid4().hex[:8]}"
        
        # Get database session
        db = next(get_db())
        audit_service = LLMAuditService(db)
        
        # Merge hyperparameters
        final_hyperparameters = {**self.default_hyperparameters, **(hyperparameters or {})}
        
        # Merge metadata
        final_metadata = {**self.default_metadata, **(metadata or {})}
        
        # Merge tags
        final_tags = self.default_tags + (tags or [])
        
        # Create audit context
        async with LLMAuditContext(
            audit_service=audit_service,
            interaction_id=interaction_id,
            model_name=self.model_name,
            model_provider=self.model_provider,
            purpose=self.purpose,
            input_prompt=prompt,
            sub_purpose=self.sub_purpose,
            context_type=self.context_type,
            parent_workflow_id=parent_workflow_id,
            parent_survey_id=parent_survey_id,
            parent_rfq_id=parent_rfq_id,
            hyperparameters=final_hyperparameters,
            metadata=final_metadata,
            tags=final_tags
        ) as audit_context:
            try:
                # Call the underlying LLM client
                result = await self.llm_client.generate(prompt, **final_hyperparameters, **kwargs)
                
                # Extract metrics from result
                if isinstance(result, dict):
                    output_content = result.get('content') or result.get('response') or str(result)
                    input_tokens = result.get('input_tokens')
                    output_tokens = result.get('output_tokens')
                    cost_usd = result.get('cost_usd')
                    
                    audit_context.set_output(
                        output_content=output_content,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_usd=cost_usd
                    )
                else:
                    audit_context.set_output(output_content=str(result))
                
                return result
                
            except Exception as e:
                # The audit context will handle logging the error
                raise
    
    def __getattr__(self, name):
        """Delegate other attributes to the wrapped LLM client"""
        return getattr(self.llm_client, name)


def create_audited_llm_client(
    llm_client,
    purpose: str,
    sub_purpose: str = None,
    context_type: str = None,
    model_name: str = None,
    model_provider: str = None,
    default_hyperparameters: Dict[str, Any] = None,
    default_metadata: Dict[str, Any] = None,
    default_tags: list = None
) -> LLMAuditWrapper:
    """
    Create an audited wrapper around an LLM client
    
    Args:
        llm_client: The underlying LLM client to wrap
        purpose: Primary purpose for auditing
        sub_purpose: Specific sub-purpose for auditing
        context_type: Type of context for auditing
        model_name: Name of the model (if not available from client)
        model_provider: Provider of the model (if not available from client)
        default_hyperparameters: Default hyperparameters to use
        default_metadata: Default metadata to include
        default_tags: Default tags to include
        
    Returns:
        LLMAuditWrapper instance
    """
    return LLMAuditWrapper(
        llm_client=llm_client,
        purpose=purpose,
        sub_purpose=sub_purpose,
        context_type=context_type,
        model_name=model_name,
        model_provider=model_provider,
        default_hyperparameters=default_hyperparameters,
        default_metadata=default_metadata,
        default_tags=default_tags
    )


# Convenience functions for common LLM audit patterns

def audit_survey_generation(func: Callable):
    """Convenience decorator for survey generation LLM calls"""
    return audit_llm_call(
        purpose="survey_generation",
        context_type="generation",
        tags=["survey", "generation"]
    )(func)


def audit_evaluation(func: Callable):
    """Convenience decorator for evaluation LLM calls"""
    return audit_llm_call(
        purpose="evaluation",
        context_type="evaluation",
        tags=["evaluation", "quality"]
    )(func)


def audit_field_extraction(func: Callable):
    """Convenience decorator for field extraction LLM calls"""
    return audit_llm_call(
        purpose="field_extraction",
        context_type="analysis",
        tags=["extraction", "parsing"]
    )(func)


def audit_document_parsing(func: Callable):
    """Convenience decorator for document parsing LLM calls"""
    return audit_llm_call(
        purpose="document_parsing",
        context_type="analysis",
        tags=["document", "parsing"]
    )(func)
