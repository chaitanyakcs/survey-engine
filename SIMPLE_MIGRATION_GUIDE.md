# Simple Railway Migration Guide

## Your Current Situation
- ✅ **Data**: ~200MB PostgreSQL data in Railway volumes
- ✅ **App**: Survey Engine (FastAPI + React)
- ❌ **Issue**: Database connection problems

## Easiest Migration Options

### **Option 1: Railway Fresh Start (5 minutes)**
```bash
# 1. Create new Railway project
railway login
railway init survey-engine-new

# 2. Add PostgreSQL service
railway add postgres

# 3. Deploy your app
railway up

# 4. Export data from old project via Railway dashboard
# 5. Import data to new project
```

### **Option 2: Render (10 minutes)**
1. Go to [render.com](https://render.com)
2. Connect your GitHub repo
3. Add PostgreSQL database
4. Deploy app
5. Import data via Render's database tools

### **Option 3: DigitalOcean App Platform (15 minutes)**
1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Create new app from GitHub
3. Add PostgreSQL database
4. Deploy
5. Import data

### **Option 4: Fix Current Railway (2 minutes)**
```bash
# Reset PostgreSQL password
railway variables --service=postgres --set POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Restart services
railway redeploy --service=postgres --yes
railway redeploy --service=survey-engine --yes
```

## Data Export Methods

### **Method 1: Railway Dashboard (Easiest)**
1. Go to [railway.app](https://railway.app)
2. Select your project
3. Go to PostgreSQL service
4. Click "Data" tab
5. Export database

### **Method 2: Railway CLI**
```bash
# Get database connection string
railway variables --service=postgres

# Use external tool to connect and export
# (pgAdmin, DBeaver, etc.)
```

### **Method 3: Application Export**
```python
# Add this to your app to export data
@app.get("/admin/export-data")
async def export_data():
    # Export all tables to JSON/CSV
    pass
```

## Recommended: Railway Fresh Start

**Why this is easiest:**
- ✅ Keep using Railway (familiar)
- ✅ Fresh database (no connection issues)
- ✅ Same deployment process
- ✅ 5 minutes total

**Steps:**
1. Create new Railway project
2. Add PostgreSQL service
3. Deploy your app
4. Export data from old project
5. Import to new project
6. Delete old project

## Cost Comparison
- **Current Railway**: ~$25/month
- **New Railway**: ~$25/month (same)
- **Render**: ~$20-30/month
- **DigitalOcean**: ~$25-35/month

## Next Steps
1. **Choose your option** (I recommend Railway Fresh Start)
2. **Export your data** via Railway dashboard
3. **Create new project** and deploy
4. **Import data** to new database
5. **Test everything** works
6. **Delete old project**

Would you like me to help you with any of these options?
