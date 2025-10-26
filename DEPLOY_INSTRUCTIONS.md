# Deploy Phase 3 Labels Fix

## Status

Changes deployed locally but NOT to Railway production.

## What Needs to be Deployed

### Modified File
- `src/services/annotation_rag_sync_service.py` - Fixed label storage to use arrays

### Changes Made
1. Removed normalization that was converting `Medical_Conditions_Study` → different formats
2. Keep labels as-is if they're already in correct format (uppercase with underscores)
3. Always store as arrays, never as objects
4. Added logging to track label processing

## Deploy Steps

1. **Commit changes:**
   ```bash
   git add src/services/annotation_rag_sync_service.py
   git commit -m "Fix label storage to use arrays instead of objects"
   git push origin master
   ```

2. **Railway auto-deploys** from master branch

3. **After deployment, re-sync annotations:**
   ```bash
   curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/sync-annotations-to-rag
   ```

4. **Verify labels are now arrays:**
   ```bash
   curl -s 'https://survey-engine-production.up.railway.app/api/v1/golden-content/questions?limit=5' | jq '.[0].labels'
   ```
   
   Should return: `["Medical_Conditions_Study"]` instead of `{}`

## Expected Result

After deployment and re-sync:
- Labels stored as arrays: `["Medical_Conditions_Study"]`
- Phase 3's `retrieve_golden_questions_by_labels()` can find questions by label
- Smart retrieval will work for new surveys

## Current Production Status

- Labels in annotations: ✅ Arrays like `["Medical_Conditions_Study"]`
- Labels in golden_questions: ❌ Still `{}` (empty objects)
- Reason: Changes not deployed to Railway yet
- Action Needed: Deploy and re-sync

