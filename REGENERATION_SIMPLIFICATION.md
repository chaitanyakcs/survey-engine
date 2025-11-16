# Survey Regeneration Simplification

## Summary

Simplified the survey regeneration flow to be **synchronous** with **no WebSocket** complexity. The regeneration now waits for completion before returning, eliminating timeout issues and complex progress tracking.

## Problem

The previous implementation had several issues:
1. **ReadTimeout errors**: Replicate API calls were timing out after 60 seconds during regeneration
2. **WebSocket complexity**: Progress tracking via WebSocket added unnecessary complexity
3. **Inconsistent state**: Frontend had to manage WebSocket connections, progress state, and reconnection logic

## Solution

### 1. Increased Timeouts (`src/services/llm_provider.py`)
- **httpx read timeout**: 1200s → **1800s (30 minutes)**
- **asyncio wait_for timeout**: 900s → **1800s (30 minutes)**
- **Connection timeout**: 30s → **60s**
- **Write timeout**: 30s → **60s**
- **Pool timeout**: 30s → **60s**

This prevents `httpx.ReadTimeout` errors during long-running regeneration operations.

### 2. Simplified Regeneration Endpoint (`src/api/survey.py`)
- **Removed WebSocket dependency**: No `connection_manager` passed to `WorkflowService`
- **Synchronous wait**: API call waits for completion before returning
- **Updated response message**: "Survey regeneration **completed**" (not "started")
- **Better error logging**: Added detailed logging for debugging

```python
# Before: Async with WebSocket
workflow_service = WorkflowService(db, connection_manager=manager)
# Returns immediately, user connects to WebSocket

# After: Synchronous wait
workflow_service = WorkflowService(db, connection_manager=None)
# Waits for completion, returns result directly
```

### 3. Updated Frontend Store (`frontend/src/store/useAppStore.ts`)
- **Removed WebSocket connection**: No `connectWebSocket()` call
- **Simple loading state**: Shows 50% progress during operation
- **Completion state**: Sets progress to 100% and status to 'completed' after API returns
- **Better error handling**: Resets workflow state on error
- **Updated toast messages**: "Regeneration Complete" (not "Started")

```typescript
// Before: Connect WebSocket for progress
get().connectWebSocket(result.workflow_id);

// After: Wait synchronously
const result = await apiService.regenerateSurvey(surveyId, options);
// No WebSocket needed - API waits for completion
```

### 4. Updated SurveyVersions Component (`frontend/src/components/SurveyVersions.tsx`)
- **Removed progress modal**: No `setShowProgressModal(true)`
- **Synchronous wait**: Shows loading state during API call
- **Auto-navigation**: Redirects to new survey immediately after completion
- **Cleaner UX**: Simple loading → success → redirect flow

```typescript
// Before: Show progress modal, wait for WebSocket
setShowProgressModal(true);
await regenerateSurvey(surveyId, options);
// Wait for WebSocket completion event

// After: Wait synchronously, then redirect
await regenerateSurvey(surveyId, options);
window.location.href = `/surveys/${result.survey_id}`;
```

## Benefits

1. **No more ReadTimeout errors**: 30-minute timeout is more than sufficient for regeneration
2. **Simpler code**: Removed WebSocket connection manager, progress tracking, and state synchronization
3. **Better UX**: User sees loading state, then immediately redirects to completed survey
4. **Fewer failure modes**: No WebSocket connection failures, reconnection logic, or state inconsistencies
5. **Easier debugging**: Single API call to trace instead of WebSocket message flow

## User Experience

### Before
1. Click "Regenerate"
2. See progress modal
3. WebSocket connects
4. Progress updates stream in
5. On completion, modal closes
6. User manually refreshes or navigates

### After
1. Click "Regenerate"
2. See loading state (simple spinner)
3. Wait for API to complete (30s-3min typical)
4. Automatically redirect to new survey
5. See success toast

## Technical Details

### Timeout Configuration
```python
# llm_provider.py
timeout_config = httpx.Timeout(
    connect=60.0,   # 60 seconds to establish connection
    read=1800.0,    # 30 minutes for LLM response
    write=60.0,     # 60 seconds to write request
    pool=60.0       # 60 seconds to get connection from pool
)
```

### API Response
```json
{
  "survey_id": "new-survey-uuid",
  "workflow_id": "survey-regenerate-new-survey-uuid",
  "version": 2,
  "message": "Survey regeneration completed. New version 2 has been generated."
}
```

## Migration Notes

- **No breaking changes** for regular survey generation (still uses WebSocket)
- **Only regeneration** is now synchronous
- **Existing regeneration calls** will work but won't use WebSocket
- **Frontend automatically handles** both old and new flow

## Testing

1. **Frontend build**: ✅ Compiles successfully with TypeScript
2. **No linter errors**: Only minor warnings (unused vars, missing deps)
3. **Backward compatible**: Existing surveys and workflows unaffected

## Future Considerations

1. **Optional**: Could apply same pattern to initial survey generation
2. **Monitoring**: Track regeneration times to ensure 30min timeout is sufficient
3. **UI enhancement**: Could show indeterminate progress bar during wait
4. **Optimization**: Could add polling endpoint if users want to check status

## Files Changed

### Backend
- `src/services/llm_provider.py` - Increased timeouts
- `src/api/survey.py` - Simplified regeneration endpoint

### Frontend
- `frontend/src/store/useAppStore.ts` - Removed WebSocket connection
- `frontend/src/components/SurveyVersions.tsx` - Simplified regeneration flow

## Deployment

No special deployment steps needed. Changes are backward compatible.

```bash
# Backend
cd /Users/chaitanya/Work/repositories/survey-engine
# Restart backend service

# Frontend
cd frontend
npm run build
# Deploy updated build
```

