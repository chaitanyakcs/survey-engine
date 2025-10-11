# LLM Audit for Evaluations

## Overview
The LLM Audit system tracks all LLM interactions across the survey engine, including evaluation calls. This document explains how audit logging works for evaluations and how to access the logs.

## How Evaluation Auditing Works

### 1. Audit Integration in Evaluation LLM Client
The `EvaluationLLMClient` (`evaluations/llm_client.py`) is responsible for making LLM calls during survey evaluation. It includes built-in audit logging:

```python
# When a database session is available, audit context is created
if self.db_session:
    audit_service = LLMAuditService(self.db_session)
    async with LLMAuditContext(
        audit_service=audit_service,
        interaction_id=f"evaluation_{uuid.uuid4().hex[:8]}",
        model_name=self.model,
        model_provider="replicate",
        purpose="evaluation",
        sub_purpose="survey_evaluation",
        context_type="survey_data",
        parent_survey_id=parent_survey_id,
        parent_rfq_id=parent_rfq_id,
        hyperparameters={...},
        tags=["evaluation", "survey_analysis"]
    ) as audit_context:
        # Make LLM call
        response = await replicate_client.run(...)
        # Set audit output
        audit_context.set_raw_response(str(response))
        audit_context.set_output(output_content=content)
```

### 2. Evaluation Flow with Audit
1. User generates a survey
2. Survey goes through quality gates
3. `ValidatorAgent` calls `EvaluatorService.evaluate_survey()`
4. `EvaluatorService` calls `_evaluate_with_advanced_system()`
5. `_evaluate_with_advanced_system()` creates `SingleCallEvaluator` or `PillarBasedEvaluator`
6. Evaluator uses `EvaluationLLMClient` which has audit context
7. Every LLM call is logged to the `llm_audit` table

### 3. Audit Record Structure
Each evaluation audit record includes:
- **interaction_id**: Unique ID for this LLM call (format: `evaluation_xxxxxxxx`)
- **parent_survey_id**: ID of the survey being evaluated
- **parent_rfq_id**: ID of the RFQ
- **model_name**: LLM model used (e.g., `openai/gpt-5`, `openai/gpt-5-structured`)
- **model_provider**: Provider (usually `replicate`)
- **purpose**: `evaluation`
- **sub_purpose**: `survey_evaluation`
- **context_type**: `survey_data`
- **tags**: `["evaluation", "survey_analysis"]`
- **input_prompt**: Full evaluation prompt sent to LLM
- **output_content**: Processed LLM response
- **raw_response**: Raw LLM response before processing
- **hyperparameters**: Temperature, top_p, max_tokens, etc.
- **response_time_ms**: Time taken for LLM call
- **success**: Whether the call succeeded
- **created_at**: Timestamp of the audit record

## Accessing Evaluation Audit Logs

### Via UI
1. Navigate to the LLM Audit Viewer at `/llm-audit`
2. To filter for evaluations only:
   - Set **Purpose** filter to `evaluation`
3. To view audits for a specific survey:
   - Navigate to `/llm-audit/survey/{survey_id}`
   - This automatically filters by `parent_survey_id`

### Via API
**List all evaluation audits:**
```bash
GET /api/v1/llm-audit/interactions?purpose=evaluation
```

**List evaluation audits for a specific survey:**
```bash
GET /api/v1/llm-audit/interactions?parent_survey_id={survey_id}
```

**Get a specific audit record:**
```bash
GET /api/v1/llm-audit/interactions/{interaction_id}
```

### Example API Response
```json
{
  "records": [
    {
      "id": "uuid",
      "interaction_id": "evaluation_a1b2c3d4",
      "parent_survey_id": "survey-uuid",
      "parent_rfq_id": "rfq-uuid",
      "model_name": "openai/gpt-5",
      "model_provider": "replicate",
      "purpose": "evaluation",
      "sub_purpose": "survey_evaluation",
      "context_type": "survey_data",
      "input_prompt": "Evaluate this survey...",
      "output_content": "{\"pillar_scores\": {...}}",
      "raw_response": "...",
      "temperature": 0.3,
      "top_p": 0.9,
      "max_tokens": 4000,
      "response_time_ms": 2500,
      "success": true,
      "tags": ["evaluation", "survey_analysis"],
      "created_at": "2025-10-11T12:34:56Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 50
}
```

## Why Audit Logs Might Not Appear

### 1. Database Session Not Available
If the `EvaluationLLMClient` is initialized without a database session, audit logging is skipped:
```python
if not self.db_session:
    print("⚠️ [EvaluationLLMClient] No database session available for audit")
```

**Solution**: Ensure the evaluator is initialized with a database session. This is already done in `src/api/pillar_scores.py`:
```python
llm_client = create_evaluation_llm_client(db_session=db)
evaluator = SingleCallEvaluator(llm_client=llm_client, db_session=db)
```

### 2. Audit Service Import Failure
If the audit service imports fail, auditing is skipped:
```python
try:
    from src.services.llm_audit_service import LLMAuditService
    from src.utils.llm_audit_decorator import LLMAuditContext
    audit_service = LLMAuditService(self.db_session)
except Exception as e:
    print(f"⚠️ [EvaluationLLMClient] Failed to create audit service: {e}")
```

**Solution**: Ensure `src` directory is in the Python path and all audit modules are available.

### 3. Audit Context Exception
If an exception occurs during audit logging, it's caught to prevent breaking the evaluation:
```python
try:
    await audit_service.log_llm_interaction(...)
except Exception as e:
    logger.error(f"❌ [LLMAuditContext] Failed to log interaction: {str(e)}")
```

**Solution**: Check application logs for audit-related errors.

### 4. Filtering Issues in UI
The audit records might exist but not be visible due to incorrect filters.

**Solution**: 
- Clear all filters in the LLM Audit Viewer
- Use the API directly to verify records exist
- Check that `purpose=evaluation` filter is working

### 5. Using Legacy Evaluator
If an older evaluator without audit integration is used, no logs will be created.

**Solution**: Ensure you're using `SingleCallEvaluator` or `PillarBasedEvaluator` which both use the audit-enabled `EvaluationLLMClient`.

## Verification Checklist

To verify evaluation auditing is working:

1. **Check Settings**: Ensure evaluation mode is set to `single_call` or `multiple_calls` (not `basic` fallback)
2. **Generate a Survey**: Create a new survey through the normal workflow
3. **Check Logs**: Look for these log messages:
   - `🔍 [EvaluationLLMClient] Audit service created successfully`
   - `🚀 Using single_call evaluation mode` (or `multiple_calls`)
4. **Query API**: Check if audit records exist:
   ```bash
   curl "https://your-domain/api/v1/llm-audit/interactions?purpose=evaluation&page_size=10"
   ```
5. **Check UI**: Navigate to `/llm-audit` and set purpose filter to `evaluation`

## Model Configuration for Evaluations

### Available Evaluation Models
The following models are available for evaluations (configured in `src/api/settings.py`):
- `openai/gpt-5` (default)
- `openai/gpt-5-structured` (NEW - structured output mode)
- `openai/gpt-4o-mini`
- `openai/gpt-4o`
- `meta/meta-llama-3.1-405b-instruct`
- `meta/meta-llama-3-70b-instruct`
- `meta/meta-llama-3-8b-instruct`
- `mistralai/mistral-7b-instruct-v0.1`

### Changing Evaluation Model
1. Navigate to Settings page (`/settings`)
2. Under "Model Configuration", find the "Evaluation" dropdown
3. Select your preferred model (e.g., `openai/gpt-5-structured`)
4. Click "Save Settings"

All subsequent evaluations will use the selected model, and audit logs will reflect the model choice.

## Cost Tracking
Evaluation audit logs include cost information (hidden in UI but available in database):
- **input_tokens**: Number of tokens in the prompt
- **output_tokens**: Number of tokens in the response
- **cost_usd**: Estimated cost of the LLM call

This allows tracking evaluation costs over time.

## Summary
- ✅ Evaluation auditing is **fully integrated** and working
- ✅ All evaluation LLM calls are logged when database session is available
- ✅ Logs can be viewed via UI (`/llm-audit`) or API
- ✅ Filter by `purpose=evaluation` to see only evaluation logs
- ✅ `openai/gpt-5-structured` is now available as an evaluation model option

If you don't see evaluation audit logs, follow the verification checklist above to diagnose the issue.




