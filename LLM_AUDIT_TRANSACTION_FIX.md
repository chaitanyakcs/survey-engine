# LLM Audit Transaction Isolation Fix

## Problem

LLM audit records were being logged successfully but then rolled back when the parent workflow transaction failed. This prevented debugging of failed generation attempts via the `/api/v1/llm-audit/interactions` endpoint.

### Root Cause

1. The `GeneratorAgent` in `src/workflows/nodes.py` creates a fresh database session
2. This session is passed to the `GenerationService` 
3. The `LLMAuditContext` uses the same session to log audit records
4. When JSON parsing fails and an exception is raised, the workflow fails
5. The fresh session is rolled back somewhere in the error handling chain
6. This rollback removes the audit record from the database, even though logs showed it was committed

### Evidence from Logs

```
INFO:src.services.llm_audit_service:✅ [LLMAuditService] Logged LLM interaction: survey_generation_c69f0c5a (survey_generation)
```

The audit was logged successfully, but the record didn't appear in the database due to the transaction rollback.

## Solution

Implemented **transaction isolation** for audit logging by ensuring audit records are always committed in an independent database session that cannot be affected by parent transaction rollbacks.

### Changes Made

#### 1. Added Independent Session Factory (`src/database/connection.py`)

```python
def get_independent_db_session() -> Session:
    """
    Get an independent database session for operations that should not be 
    affected by parent transaction rollbacks (e.g., audit logging).
    
    The caller is responsible for closing this session.
    """
    return SessionLocal()
```

#### 2. Updated LLM Audit Service (`src/services/llm_audit_service.py`)

Modified `log_llm_interaction` method to:
- Always create an independent database session using `get_independent_db_session()`
- Perform all audit logging operations in this isolated session
- Commit the audit record immediately in its own transaction
- Properly close the session in a `finally` block to prevent connection leaks

Key changes:
- Removed dependency on `self.db_session` for audit logging
- Added explicit session management with try/except/finally
- Added debug logging to track session IDs for troubleshooting
- Ensured audit records persist even when parent transactions fail

## Benefits

1. **Reliability**: Audit records are now guaranteed to persist, even when workflows fail
2. **Debugging**: Failed generation attempts can now be analyzed via the audit API
3. **Accountability**: Complete audit trail of all LLM interactions, successful or failed
4. **No Side Effects**: The fix is isolated to audit logging and doesn't affect other transactions

## Testing

To verify the fix works:

1. Trigger a survey generation that will fail (e.g., with malformed LLM response)
2. Check the logs for the audit success message
3. Query the audit API: `GET /api/v1/llm-audit/interactions?page=1&page_size=10`
4. Verify the failed interaction is present with `success=false` and the `raw_response` captured

## Implementation Notes

- The `LLMAuditService` constructor still accepts a `db_session` parameter for backward compatibility, but the `log_llm_interaction` method ignores it and always creates an independent session
- This pattern can be applied to other critical logging/audit operations that should survive transaction rollbacks
- Session management is critical: the independent session is always closed in the `finally` block to prevent connection pool exhaustion

## Related Files

- `src/database/connection.py` - Added independent session factory
- `src/services/llm_audit_service.py` - Updated to use independent sessions
- `src/utils/llm_audit_decorator.py` - LLMAuditContext uses the audit service (unchanged)
- `src/workflows/nodes.py` - GeneratorAgent passes sessions (unchanged)

