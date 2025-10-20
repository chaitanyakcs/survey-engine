# Multi-Level RAG Production Deployment Guide

## Overview

This guide covers deploying the multi-level RAG system to production on Railway. The system enables section-level and question-level retrieval from golden examples, significantly improving survey generation quality.

## What's New

### Multi-Level RAG Features
- **Section-Level Retrieval**: Find relevant sections from golden surveys
- **Question-Level Retrieval**: Find specific questions that match your needs
- **Human Verification Priority**: Human-verified examples rank higher
- **Automatic Population**: Existing golden pairs are automatically processed

### Database Tables Added
- `golden_sections`: Stores individual sections with embeddings
- `golden_questions`: Stores individual questions with embeddings
- Vector similarity indexes for fast retrieval

## Production Deployment Steps

### Step 1: Deploy with Auto-Migration (Recommended)

```bash
# Deploy with automatic migration and bootstrap
./deploy.sh --auto-migrate
```

This will:
1. Deploy the application to Railway
2. Run all database migrations (including multi-level RAG tables)
3. Bootstrap golden pairs from existing surveys
4. Populate multi-level RAG tables automatically

### Step 2: Manual Deployment (If Needed)

If you prefer manual control:

```bash
# Deploy without auto-migration
./deploy.sh

# Then run migrations manually
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all

# Bootstrap golden pairs
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/bootstrap-golden-pairs

# Populate multi-level RAG
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/populate-multi-level-rag
```

### Step 3: Verify Deployment

Check that everything is working:

```bash
# Check migration status
curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status

# Check golden pairs count
curl https://survey-engine-production.up.railway.app/api/v1/golden-pairs/stats

# Test survey generation (should now use multi-level RAG)
curl -X POST https://survey-engine-production.up.railway.app/api/v1/survey/generate \
  -H "Content-Type: application/json" \
  -d '{"rfq_text": "Test survey generation"}'
```

## Expected Results

### After Deployment
- **Golden Pairs**: ~21+ reference examples (from bootstrap)
- **Golden Sections**: ~64+ sections with embeddings
- **Golden Questions**: ~444+ questions with embeddings
- **Retrieval Quality**: Significantly improved due to multi-level matching

### Performance Impact
- **Generation Time**: Slightly longer due to additional retrieval steps
- **Quality**: Much higher due to more relevant examples
- **Coverage**: Better coverage across different survey types

## Monitoring & Maintenance

### Key Metrics to Monitor
1. **Golden Pairs Growth**: Track new reference examples created
2. **Retrieval Effectiveness**: Monitor similarity scores
3. **Generation Quality**: Track pillar scores of generated surveys
4. **User Adoption**: Monitor "Mark as Reference" usage

### Regular Maintenance
- **Weekly**: Check golden pairs growth
- **Monthly**: Review retrieval effectiveness
- **Quarterly**: Analyze generation quality trends

## Troubleshooting

### Common Issues

#### 1. Migration Fails
```bash
# Check migration status
curl https://survey-engine-production.up.railway.app/api/v1/admin/check-migration-status

# Re-run specific migration
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/migrate-all
```

#### 2. Bootstrap Fails
```bash
# Check existing golden pairs
curl https://survey-engine-production.up.railway.app/api/v1/golden-pairs/stats

# Re-run bootstrap
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/bootstrap-golden-pairs
```

#### 3. Multi-Level RAG Population Fails
```bash
# Check golden pairs exist first
curl https://survey-engine-production.up.railway.app/api/v1/golden-pairs/stats

# Re-run population
curl -X POST https://survey-engine-production.up.railway.app/api/v1/admin/populate-multi-level-rag
```

#### 4. Poor Retrieval Quality
- Check that golden pairs have embeddings
- Verify multi-level RAG tables are populated
- Review retrieval weights configuration

### Logs and Debugging

```bash
# Check Railway logs
railway logs

# Check specific service logs
railway logs --service backend

# Check database connection
railway connect postgres
```

## API Endpoints

### New Admin Endpoints
- `POST /api/v1/admin/populate-multi-level-rag` - Populate multi-level RAG tables
- `GET /api/v1/admin/check-migration-status` - Check migration status

### Enhanced Retrieval
- Survey generation now uses multi-level retrieval automatically
- No API changes needed for existing workflows

## User Experience

### For Researchers
- **Immediate Value**: Start with 21+ reference examples
- **Better Quality**: More relevant survey generation
- **No Learning Curve**: Existing workflow unchanged

### For Administrators
- **Easy Deployment**: One-command deployment with `--auto-migrate`
- **Automatic Setup**: Bootstrap and population happen automatically
- **Monitoring**: Built-in endpoints for status checking

## Rollback Plan

If issues occur:

1. **Disable Multi-Level RAG**: Set retrieval weights to 0 for section/question weights
2. **Revert to Survey-Level Only**: Use existing golden pairs retrieval
3. **Database Rollback**: Drop multi-level RAG tables if needed

```sql
-- Emergency rollback (only if needed)
DROP TABLE IF EXISTS golden_questions;
DROP TABLE IF EXISTS golden_sections;
```

## Success Metrics

### Immediate (Day 1)
- ✅ 21+ golden pairs created
- ✅ 64+ sections indexed
- ✅ 444+ questions indexed
- ✅ Survey generation working

### Short-term (Week 1)
- 📈 Improved generation quality scores
- 📈 Higher user satisfaction
- 📈 More reference examples created

### Long-term (Month 1)
- 📈 Consistent quality improvements
- 📈 User adoption of "Mark as Reference"
- 📈 Reduced manual survey editing

## Support

For issues or questions:
1. Check this deployment guide
2. Review Railway logs
3. Test API endpoints manually
4. Contact development team

---

**Last Updated**: October 20, 2024
**Version**: Multi-Level RAG v1.0
**Deployment Target**: Railway Production
