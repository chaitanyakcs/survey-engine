
# Railway to AWS Migration Instructions

## What we have:
- PostgreSQL database with pgvector extension
- Survey Engine application data
- ~200MB of data in Railway volumes

## Migration Options:

### Option 1: AWS RDS (Recommended)
1. Create RDS PostgreSQL instance
2. Install pgvector extension: `CREATE EXTENSION vector;`
3. Import data: `psql -h your-rds-endpoint -U postgres -d survey_engine < railway_export.sql`

### Option 2: Railway Fresh Start
1. Create new Railway project
2. Add PostgreSQL service
3. Import data: `psql -h new-postgres.railway.internal -U postgres -d railway < railway_export.sql`

### Option 3: Render
1. Create Render PostgreSQL database
2. Import data using Render's database tools

### Option 4: DigitalOcean
1. Create DigitalOcean PostgreSQL cluster
2. Import data using their migration tools

## Environment Variables to Set:
- DATABASE_URL: postgresql://user:pass@host:port/database
- REPLICATE_API_TOKEN: your-replicate-token
- ENVIRONMENT: production

## Next Steps:
1. Choose your target platform
2. Create new database
3. Import railway_export.sql
4. Update application with new DATABASE_URL
5. Deploy application
