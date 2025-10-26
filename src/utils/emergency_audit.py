"""
Emergency Audit Logging for LLM Failures

This module provides emergency logging capabilities when normal audit context fails.
It ensures raw LLM responses are ALWAYS captured, even when:
- Database session is unavailable
- Audit context initialization fails
- JSON parsing fails before audit logging

Fallback strategy:
1. Try independent database session
2. Fall back to file logging (/tmp/llm_failures/)
3. Ultimate fallback to stderr logging
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Emergency log directory
EMERGENCY_LOG_DIR = Path("/tmp/llm_failures")


async def emergency_log_llm_failure(
    raw_response: str,
    service_name: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    interaction_id: Optional[str] = None,
    model_name: Optional[str] = None,
    model_provider: Optional[str] = None,
    purpose: Optional[str] = None,
    input_prompt: Optional[str] = None,
) -> str:
    """
    Emergency logging when audit context fails.
    Tries: 1) Independent DB session, 2) File logging, 3) stderr
    
    Args:
        raw_response: The raw LLM response that failed to parse
        service_name: Name of the service that failed
        error_message: The error message from the failure
        context: Additional context about the failure
        interaction_id: Optional interaction ID for tracking
        model_name: Optional model name
        model_provider: Optional model provider
        purpose: Optional purpose (survey_generation, evaluation, etc.)
        input_prompt: Optional input prompt
        
    Returns:
        The interaction_id (generated if not provided)
    """
    if not interaction_id:
        interaction_id = f"emergency_{uuid.uuid4().hex[:8]}"
    
    context = context or {}
    
    logger.error(
        f"🚨 [EmergencyAudit] LLM failure in {service_name}: {error_message}"
    )
    logger.error(
        f"🚨 [EmergencyAudit] Interaction ID: {interaction_id}"
    )
    logger.error(
        f"🚨 [EmergencyAudit] Raw response length: {len(raw_response)}"
    )
    
    # Strategy 1: Try independent database session
    try:
        success = await _log_to_independent_db(
            interaction_id=interaction_id,
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
            model_name=model_name,
            model_provider=model_provider,
            purpose=purpose,
            input_prompt=input_prompt,
            context=context,
        )
        if success:
            logger.info(
                f"✅ [EmergencyAudit] Successfully logged to independent DB session: {interaction_id}"
            )
            return interaction_id
    except Exception as db_error:
        logger.warning(
            f"⚠️ [EmergencyAudit] Independent DB logging failed: {str(db_error)}"
        )
    
    # Strategy 2: Fall back to file logging
    try:
        file_path = await _log_to_file(
            interaction_id=interaction_id,
            raw_response=raw_response,
            service_name=service_name,
            error_message=error_message,
            model_name=model_name,
            model_provider=model_provider,
            purpose=purpose,
            input_prompt=input_prompt,
            context=context,
        )
        logger.warning(
            f"⚠️ [EmergencyAudit] Logged to file (DB unavailable): {file_path}"
        )
        return interaction_id
    except Exception as file_error:
        logger.error(
            f"❌ [EmergencyAudit] File logging failed: {str(file_error)}"
        )
    
    # Strategy 3: Ultimate fallback - log to stderr
    logger.error(
        f"❌ [EmergencyAudit] ALL LOGGING FAILED - Raw response preview (first 500 chars):"
    )
    logger.error(raw_response[:500])
    logger.error(
        f"❌ [EmergencyAudit] Raw response ending (last 500 chars):"
    )
    logger.error(raw_response[-500:])
    
    return interaction_id


async def _log_to_independent_db(
    interaction_id: str,
    raw_response: str,
    service_name: str,
    error_message: str,
    model_name: Optional[str],
    model_provider: Optional[str],
    purpose: Optional[str],
    input_prompt: Optional[str],
    context: Dict[str, Any],
) -> bool:
    """
    Try to log to database using independent session.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from src.database.connection import get_independent_db_session
        from src.services.llm_audit_service import LLMAuditService
        
        # Create independent session
        db_session = get_independent_db_session()
        
        try:
            audit_service = LLMAuditService(db_session)
            
            # Log the failure
            await audit_service.log_llm_interaction(
                interaction_id=interaction_id,
                model_name=model_name or "unknown",
                model_provider=model_provider or "unknown",
                purpose=purpose or "emergency_log",
                input_prompt=input_prompt or "",
                output_content="",
                raw_response=raw_response,
                sub_purpose=f"emergency_{service_name}",
                context_type="emergency_failure",
                hyperparameters={},
                performance_metrics={},
                metadata={
                    "service_name": service_name,
                    "error_message": error_message,
                    "emergency_logged": True,
                    **context,
                },
                tags=["emergency", "parsing_failure", service_name],
                success=False,
                error_message=error_message,
            )
            
            return True
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.debug(f"Independent DB logging failed: {str(e)}")
        return False


async def _log_to_file(
    interaction_id: str,
    raw_response: str,
    service_name: str,
    error_message: str,
    model_name: Optional[str],
    model_provider: Optional[str],
    purpose: Optional[str],
    input_prompt: Optional[str],
    context: Dict[str, Any],
) -> str:
    """
    Log to file as fallback.
    
    Returns:
        Path to the log file
    """
    # Create emergency log directory if it doesn't exist
    EMERGENCY_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create log file with timestamp and interaction ID
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{interaction_id}_{service_name}.json"
    file_path = EMERGENCY_LOG_DIR / filename
    
    # Prepare log data
    log_data = {
        "interaction_id": interaction_id,
        "timestamp": datetime.utcnow().isoformat(),
        "service_name": service_name,
        "error_message": error_message,
        "model_name": model_name,
        "model_provider": model_provider,
        "purpose": purpose,
        "input_prompt": input_prompt[:1000] if input_prompt else None,  # Truncate prompt
        "raw_response": raw_response,
        "raw_response_length": len(raw_response),
        "context": context,
        "emergency_logged": True,
    }
    
    # Write to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    return str(file_path)


def get_emergency_log_files() -> list:
    """
    Get list of emergency log files.
    
    Returns:
        List of file paths
    """
    if not EMERGENCY_LOG_DIR.exists():
        return []
    
    return sorted(EMERGENCY_LOG_DIR.glob("*.json"), reverse=True)


async def load_emergency_log(file_path: str) -> Dict[str, Any]:
    """
    Load an emergency log file.
    
    Args:
        file_path: Path to the log file
        
    Returns:
        Log data as dictionary
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def cleanup_old_emergency_logs(days: int = 7) -> int:
    """
    Clean up emergency log files older than specified days.
    
    Args:
        days: Number of days to keep logs
        
    Returns:
        Number of files deleted
    """
    if not EMERGENCY_LOG_DIR.exists():
        return 0
    
    import time
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    deleted_count = 0
    
    for file_path in EMERGENCY_LOG_DIR.glob("*.json"):
        if file_path.stat().st_mtime < cutoff_time:
            file_path.unlink()
            deleted_count += 1
    
    logger.info(f"🧹 [EmergencyAudit] Cleaned up {deleted_count} old emergency logs")
    return deleted_count

