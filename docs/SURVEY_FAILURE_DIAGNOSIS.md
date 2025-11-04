# Survey Generation Failure Diagnosis

## Summary

Survey ID: `edc1dd30-3f29-4469-b6df-0cd0ee5afac5`

**Status**: Survey generation **succeeded**, but **evaluation failed**

## Timeline

1. **2025-10-30 15:15:26 UTC** - ✅ Survey generation completed successfully
2. **2025-10-30 15:22:18 UTC** - ❌ Evaluation failed

## Root Cause

The evaluation step failed due to an extremely large prompt:

- **Prompt Length**: 70,018 characters (~70 KB)
- **Max Tokens**: 4,000
- **Model**: `openai/gpt-5-structured` (via Replicate)
- **Error Message**: Empty (suggests exception wasn't properly captured)

### Why This Failed

1. **Prompt Size**: The evaluation prompt includes the entire survey JSON, RFQ text, and all questions. For large surveys, this can exceed API limits or cause timeouts.

2. **Missing Error Handling**: The LLM audit record shows `success: false` but `error_message: null`, indicating the exception was caught but not properly logged.

3. **Evaluation Should Be Non-Critical**: According to the codebase, evaluation failures should be graceful (see `src/services/evaluator_service.py` lines 117-134), but the workflow still marks the survey as failed.

## Technical Details

### Evaluation Flow

The evaluation uses a "single-call evaluator" (`evaluations/modules/single_call_evaluator.py`):
- Builds a comprehensive prompt with full survey JSON + RFQ text
- Calls LLM with `max_tokens=4000`
- Expected to return structured JSON with pillar scores

### Error Handling Issue

Looking at `evaluations/llm_client.py`:
- Uses `LLMAuditContext` for audit logging
- If an exception occurs in the `except` block (line 279), it falls back to heuristic evaluation
- However, the error message may not be properly captured in the audit record

## Impact

- ✅ Survey was successfully generated
- ❌ Evaluation failed (no quality scores/pillar analysis)
- ❌ Survey marked as "failed" status (should be "draft" or "validated")

## Recommendations

### Immediate Fixes

1. **Add Prompt Size Validation**
   - Check prompt length before sending to LLM
   - Truncate or summarize survey content if prompt exceeds limits
   - Suggested limit: 50,000 characters

2. **Improve Error Handling**
   - Ensure exceptions are properly caught and logged
   - Store error messages in LLM audit records
   - Add timeout handling for large prompts

3. **Make Evaluation Truly Non-Critical**
   - Evaluation failures should NOT mark survey as failed
   - Survey should complete successfully even if evaluation fails
   - See `src/services/evaluator_service.py` - it already returns graceful fallback, but workflow needs to respect this

### Long-term Improvements

1. **Prompt Optimization**
   - Don't include full survey JSON in evaluation prompt
   - Use summaries or key excerpts instead
   - Only include essential survey metadata

2. **Chunked Evaluation**
   - For large surveys, evaluate sections separately
   - Aggregate results after all sections evaluated
   - Prevents prompt size issues

3. **Better Monitoring**
   - Alert when prompt sizes exceed thresholds
   - Track evaluation failure rates
   - Monitor API response times

## Code References

- Evaluation LLM Client: `evaluations/llm_client.py:128`
- Single Call Evaluator: `evaluations/modules/single_call_evaluator.py:118`
- Evaluator Service: `src/services/evaluator_service.py:65`
- Workflow Service: `src/services/workflow_service.py` (marks survey as failed)

## Diagnostic Script

Use the diagnostic script to investigate future failures:

```bash
python scripts/diagnose_survey_failure.py <survey_id> --api-url https://survey-engine-production.up.railway.app
```

## Related Issues

- Evaluation should be non-critical but workflow marks survey as failed
- Large prompts may cause API timeouts (no timeout handling in evaluation)
- Error messages not properly captured in audit records

