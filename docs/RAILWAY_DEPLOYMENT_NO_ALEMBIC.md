# Railway Deployment Guide - No Alembic

## 🚀 Railway Deployment Steps

### 1. Deploy to Railway
```bash
# Connect your GitHub repo to Railway
# Railway will automatically detect the Python app and deploy
```

### 2. Run Database Migrations
After deployment, run the comprehensive migration:

```bash
curl -X POST https://your-app.railway.app/api/v1/admin/migrate-all
```

### 3. Verify Migration Status
Check that all migrations completed successfully:

```bash
curl https://your-app.railway.app/api/v1/admin/check-migration-status
```

### 4. Test Annotation Insights
Verify the annotation insights API is working:

```bash
curl https://your-app.railway.app/api/v1/annotation-insights
```

## 🔧 Admin Endpoints

### Health Check
```bash
curl https://your-app.railway.app/api/v1/admin/health
```

### Migration Status
```bash
curl https://your-app.railway.app/api/v1/admin/check-migration-status
```

### Human vs AI Stats
```bash
curl https://your-app.railway.app/api/v1/admin/human-vs-ai-stats
```

### Run All Migrations
```bash
curl -X POST https://your-app.railway.app/api/v1/admin/migrate-all
```

## 📊 Migration Steps

The `migrate-all` endpoint runs these steps in order:

1. **Core Tables**: Creates `question_annotations`, `section_annotations`, `survey_annotations`
2. **AI Fields**: Adds `ai_generated`, `ai_confidence`, `human_verified`, `generation_timestamp`
3. **Override Fields**: Adds `human_overridden`, `override_timestamp`, `original_ai_*` fields
4. **Performance Indexes**: Creates optimized indexes for human vs AI queries

## ✅ Benefits

- **No Alembic dependency** - simpler deployment
- **Idempotent migrations** - can be run multiple times safely
- **Railway-optimized** - handles production database constraints
- **Self-verifying** - confirms migration success
- **Production-ready** - includes proper error handling and rollback

## 🛠️ Troubleshooting

If migrations fail:

1. Check the migration status: `/api/v1/admin/check-migration-status`
2. Review the error details in the response
3. Run individual migration steps if needed
4. Contact support if issues persist

## 📝 Notes

- All migrations use `IF NOT EXISTS` to avoid conflicts
- Database changes are transactional with rollback on failure
- Indexes are created with `IF NOT EXISTS` for safety
- All endpoints include comprehensive error handling
