"""
Reparse Utility for LLM Audit Records

This module provides utilities to retrieve raw responses from audit records
and rerun parsers. Useful for:
- Debugging parsing failures
- Recovering from transient parsing issues
- Testing new parsing strategies on historical data
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from src.database.models import LLMAudit
from src.database.connection import get_db
from src.utils.json_generation_utils import JSONGenerationUtils, JSONParseStrategy

logger = logging.getLogger(__name__)


async def reparse_from_audit_record(
    audit_record_id: str,
    parser_type: str = "survey",
    db_session: Optional[Session] = None,
    strategies: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Retrieve raw response from audit record and rerun parser.
    
    Args:
        audit_record_id: ID of the audit record to reparse
        parser_type: Type of parser to use ("survey", "document", "field_extraction")
        db_session: Optional database session (will create one if not provided)
        strategies: Optional list of parsing strategies to try
        
    Returns:
        Dictionary with:
        - success: bool
        - data: parsed data if successful
        - error: error message if failed
        - audit_record: original audit record metadata
        - parsing_result: detailed parsing result
    """
    logger.info(f"🔄 [Reparse] Starting reparse for audit record: {audit_record_id}")
    
    # Get database session
    if not db_session:
        db_session = next(get_db())
        close_session = True
    else:
        close_session = False
    
    try:
        # Retrieve audit record
        from src.services.llm_audit_service import LLMAuditService
        audit_service = LLMAuditService(db_session)
        
        audit_record = await audit_service.get_interaction(audit_record_id)
        
        if not audit_record:
            logger.error(f"❌ [Reparse] Audit record not found: {audit_record_id}")
            return {
                "success": False,
                "error": f"Audit record not found: {audit_record_id}",
                "data": None,
                "audit_record": None,
                "parsing_result": None,
            }
        
        # Check if we have raw response
        if not audit_record.raw_response:
            logger.error(f"❌ [Reparse] No raw response in audit record: {audit_record_id}")
            return {
                "success": False,
                "error": "No raw response available in audit record",
                "data": None,
                "audit_record": {
                    "interaction_id": audit_record.interaction_id,
                    "purpose": audit_record.purpose,
                    "model_name": audit_record.model_name,
                    "created_at": audit_record.created_at.isoformat() if audit_record.created_at else None,
                },
                "parsing_result": None,
            }
        
        logger.info(f"✅ [Reparse] Found audit record with raw response (length: {len(audit_record.raw_response)})")
        
        # Determine parsing strategies based on parser type
        if not strategies:
            strategies = _get_default_strategies(parser_type)
        
        # Attempt to reparse
        logger.info(f"🔧 [Reparse] Attempting to parse with {len(strategies)} strategies")
        
        parse_result = JSONGenerationUtils.parse_json_from_response(
            audit_record.raw_response,
            expected_schema=_get_schema_for_parser_type(parser_type),
            strategies=strategies,
        )
        
        if parse_result.success:
            logger.info(f"✅ [Reparse] Successfully reparsed using strategy: {parse_result.strategy_used.value}")
            return {
                "success": True,
                "data": parse_result.data,
                "error": None,
                "audit_record": {
                    "interaction_id": audit_record.interaction_id,
                    "purpose": audit_record.purpose,
                    "sub_purpose": audit_record.sub_purpose,
                    "model_name": audit_record.model_name,
                    "model_provider": audit_record.model_provider,
                    "created_at": audit_record.created_at.isoformat() if audit_record.created_at else None,
                    "success": audit_record.success,
                    "error_message": audit_record.error_message,
                },
                "parsing_result": {
                    "strategy_used": parse_result.strategy_used.value,
                    "original_length": parse_result.original_length,
                    "cleaned_length": parse_result.cleaned_length,
                },
            }
        else:
            logger.error(f"❌ [Reparse] All parsing strategies failed: {parse_result.error}")
            return {
                "success": False,
                "error": f"All parsing strategies failed: {parse_result.error}",
                "data": None,
                "audit_record": {
                    "interaction_id": audit_record.interaction_id,
                    "purpose": audit_record.purpose,
                    "model_name": audit_record.model_name,
                    "created_at": audit_record.created_at.isoformat() if audit_record.created_at else None,
                },
                "parsing_result": {
                    "error": parse_result.error,
                    "original_length": parse_result.original_length,
                },
            }
            
    finally:
        if close_session:
            db_session.close()


async def reparse_failed_interactions(
    purpose: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Attempt to reparse all failed LLM interactions.
    
    Args:
        purpose: Optional purpose filter (survey_generation, document_parsing, etc.)
        start_date: Optional start date filter (ISO format)
        end_date: Optional end date filter (ISO format)
        limit: Maximum number of records to reparse
        db_session: Optional database session
        
    Returns:
        Dictionary with:
        - total_attempted: int
        - successful_reparses: int
        - failed_reparses: int
        - results: list of reparse results
    """
    logger.info(f"🔄 [Reparse] Starting batch reparse (limit: {limit})")
    
    # Get database session
    if not db_session:
        db_session = next(get_db())
        close_session = True
    else:
        close_session = False
    
    try:
        from src.services.llm_audit_service import LLMAuditService
        from datetime import datetime
        
        audit_service = LLMAuditService(db_session)
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get failed interactions
        failed_records, total_count = await audit_service.get_audit_records(
            purpose=purpose,
            success=False,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=0,
        )
        
        logger.info(f"📊 [Reparse] Found {len(failed_records)} failed interactions to reparse")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for record in failed_records:
            # Determine parser type from purpose
            parser_type = _get_parser_type_from_purpose(record.purpose)
            
            # Attempt reparse
            result = await reparse_from_audit_record(
                audit_record_id=record.interaction_id,
                parser_type=parser_type,
                db_session=db_session,
            )
            
            if result["success"]:
                successful_count += 1
                logger.info(f"✅ [Reparse] Successfully reparsed: {record.interaction_id}")
            else:
                failed_count += 1
                logger.warning(f"⚠️ [Reparse] Failed to reparse: {record.interaction_id}")
            
            results.append(result)
        
        logger.info(f"📊 [Reparse] Batch complete: {successful_count} successful, {failed_count} failed")
        
        return {
            "total_attempted": len(failed_records),
            "successful_reparses": successful_count,
            "failed_reparses": failed_count,
            "results": results,
        }
        
    finally:
        if close_session:
            db_session.close()


def _get_default_strategies(parser_type: str) -> list:
    """Get default parsing strategies for a parser type"""
    if parser_type == "survey":
        return [
            JSONParseStrategy.REPLICATE_EXTRACT,
            JSONParseStrategy.DIRECT,
            JSONParseStrategy.MARKDOWN_EXTRACT,
            JSONParseStrategy.BOUNDARY_EXTRACT,
            JSONParseStrategy.SANITIZE_AND_PARSE,
            JSONParseStrategy.AGGRESSIVE_SANITIZE,
            JSONParseStrategy.ESCAPED_JSON_HANDLE,
            JSONParseStrategy.LARGE_JSON_PARSE,
            JSONParseStrategy.PARTIAL_JSON_RECOVERY,
            JSONParseStrategy.BROKEN_JSON_RECOVERY,
        ]
    elif parser_type == "document":
        return [
            JSONParseStrategy.DIRECT,
            JSONParseStrategy.REPLICATE_EXTRACT,
            JSONParseStrategy.MARKDOWN_EXTRACT,
            JSONParseStrategy.SANITIZE_AND_PARSE,
            JSONParseStrategy.BOUNDARY_EXTRACT,
        ]
    elif parser_type == "field_extraction":
        return [
            JSONParseStrategy.DIRECT,
            JSONParseStrategy.REPLICATE_EXTRACT,
            JSONParseStrategy.SANITIZE_AND_PARSE,
        ]
    else:
        # Default: try all strategies
        return [strategy for strategy in JSONParseStrategy]


def _get_schema_for_parser_type(parser_type: str) -> Optional[Dict[str, Any]]:
    """Get expected schema for a parser type"""
    if parser_type == "survey":
        return JSONGenerationUtils.get_survey_generation_schema()
    elif parser_type == "document":
        from src.utils.json_generation_utils import get_rfq_parsing_schema
        return get_rfq_parsing_schema()
    elif parser_type == "field_extraction":
        # Field extraction doesn't have a strict schema
        return None
    else:
        return None


def _get_parser_type_from_purpose(purpose: str) -> str:
    """Determine parser type from audit record purpose"""
    if "survey_generation" in purpose:
        return "survey"
    elif "document_parsing" in purpose:
        return "document"
    elif "field_extraction" in purpose:
        return "field_extraction"
    else:
        return "survey"  # Default fallback

