# Railway Deployment with RFQ Cancellation Support

This guide ensures that the RFQ cancellation functionality works properly in Railway production environment.

## Overview

The RFQ cancellation feature requires a database constraint update to allow the `'cancelled'` status in the `document_uploads.processing_status` field. This guide covers:

1. Database migration deployment
2. Verification of constraint updates
3. Testing cancellation functionality
4. Troubleshooting common issues

## Database Migration

### Migration Files

The following migration files handle the constraint update:

1. **`alembic/versions/f658efb72a1f_add_cancelled_status_to_document_.py`** - Initial migration
2. **`alembic/versions/ed69aaa0dabc_fix_document_uploads_processing_status_.py`** - Fixed migration

### Migration Process

The migration is automatically applied during Railway deployment via the `start.sh` script:

```bash
# In start.sh, the run_migrations() function handles this:
if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$RAILWAY_PROJECT_ID" ]; then
    log_info "Railway environment detected - using Alembic migrations..."
    run_migrations || exit 1
fi
```

### Manual Migration (if needed)

If automatic migration fails, you can run it manually:

```bash
# Connect to Railway database
railway connect

# Run migration
alembic upgrade head

# Verify migration
alembic current
```

## Verification Script

### Running Verification

Use the provided verification script to ensure the constraint is properly applied:

```bash
# Run verification script
python3 scripts/verify_railway_migration.py
```

### Expected Output

```
2025-10-04 20:30:00,000 - INFO - 🚀 Starting Railway migration verification...
2025-10-04 20:30:00,000 - INFO - ✅ Railway environment detected
2025-10-04 20:30:00,000 - INFO - 🔍 Checking document_uploads.processing_status constraint...
2025-10-04 20:30:00,000 - INFO - Found constraint 'check_processing_status': processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
2025-10-04 20:30:00,000 - INFO - ✅ Constraint includes 'cancelled' status
2025-10-04 20:30:00,000 - INFO - 🧪 Testing insertion of 'cancelled' status...
2025-10-04 20:30:00,000 - INFO - ✅ Successfully inserted/updated record with 'cancelled' status
2025-10-04 20:30:00,000 - INFO - 🧹 Cleaned up test record
2025-10-04 20:30:00,000 - INFO - ✅ All verification tests passed!
2025-10-04 20:30:00,000 - INFO - 🎉 Railway migration verification completed successfully!
```

## Testing Cancellation in Railway

### 1. Test Backend API

```bash
# Test cancellation endpoint
curl -X POST https://your-railway-app.railway.app/api/v1/rfq/cancel/test-session-id

# Expected response:
{
  "status": "cancelled",
  "session_id": "test-session-id",
  "message": "Document processing cancelled successfully"
}
```

### 2. Test Status Endpoint

```bash
# Check status after cancellation
curl https://your-railway-app.railway.app/api/v1/rfq/status/test-session-id

# Expected response:
{
  "status": "cancelled",
  "session_id": "test-session-id",
  "processing_status": "cancelled",
  "error_message": "Processing cancelled by user",
  "timestamp": "2025-10-04T20:30:00.000Z",
  "message": "Document processing cancelled by user"
}
```

### 3. Test Frontend Integration

1. Upload a document in the RFQ editor
2. Wait for processing to start
3. Click "Cancel Processing" button
4. Verify:
   - Form resets to document upload section
   - Polling stops
   - Success toast appears
   - No backend errors in logs

## Troubleshooting

### Common Issues

#### 1. Constraint Not Updated

**Symptoms:**
- `CheckViolation` error when trying to cancel
- Backend logs show constraint violation

**Solution:**
```bash
# Check current migration status
alembic current

# If migration is not at head, run:
alembic upgrade head

# Verify constraint manually
psql $DATABASE_URL -c "SELECT constraint_name, check_clause FROM information_schema.check_constraints WHERE constraint_name = 'check_processing_status';"
```

#### 2. Migration Fails in Railway

**Symptoms:**
- Railway deployment fails during migration
- Database connection issues

**Solution:**
1. Check Railway database connection
2. Ensure `DATABASE_URL` is properly set
3. Run migration manually via Railway CLI
4. Check Railway logs for specific errors

#### 3. Frontend Cancellation Not Working

**Symptoms:**
- Cancel button doesn't respond
- Polling continues after cancellation
- Form doesn't reset

**Solution:**
1. Check browser console for errors
2. Verify API endpoints are accessible
3. Check network tab for failed requests
4. Ensure frontend is using correct API base URL

### Debug Commands

```bash
# Check database constraint
psql $DATABASE_URL -c "SELECT constraint_name, check_clause FROM information_schema.check_constraints WHERE constraint_name = 'check_processing_status';"

# Check migration status
alembic current

# Check recent migrations
alembic history

# Test constraint manually
psql $DATABASE_URL -c "INSERT INTO document_uploads (session_id, filename, file_size, processing_status, created_at) VALUES ('test', 'test.docx', 1024, 'cancelled', NOW()) ON CONFLICT (session_id) DO NOTHING;"

# Clean up test
psql $DATABASE_URL -c "DELETE FROM document_uploads WHERE session_id = 'test';"
```

## Monitoring

### Railway Logs

Monitor Railway logs for:
- Migration success/failure messages
- Database connection issues
- API endpoint errors
- Constraint violation errors

### Health Checks

The application includes health check endpoints:
- `/health` - Basic health check
- `/api/health` - API health check

### Database Monitoring

Monitor database for:
- Constraint violations
- Failed migrations
- Connection issues
- Performance impact

## Rollback Plan

If issues arise, you can rollback the migration:

```bash
# Rollback to previous migration
alembic downgrade -1

# Verify rollback
alembic current

# Test that 'cancelled' status is rejected
psql $DATABASE_URL -c "INSERT INTO document_uploads (session_id, filename, file_size, processing_status, created_at) VALUES ('test', 'test.docx', 1024, 'cancelled', NOW());"
# This should fail with constraint violation
```

## Success Criteria

✅ **Migration Applied**: Constraint includes 'cancelled' status  
✅ **API Working**: Cancellation endpoint responds correctly  
✅ **Frontend Working**: Cancel button stops polling and resets form  
✅ **Database Updated**: Records can be marked as 'cancelled'  
✅ **No Errors**: No constraint violations in logs  

## Support

If you encounter issues:

1. Check Railway logs first
2. Run the verification script
3. Test API endpoints manually
4. Check database constraint status
5. Review this guide for troubleshooting steps

For additional support, check the main project documentation or contact the development team.
