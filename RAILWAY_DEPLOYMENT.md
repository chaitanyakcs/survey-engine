# Railway Deployment Guide

This guide explains how to deploy the Survey Engine application to Railway, a modern cloud platform for deploying applications.

## Prerequisites

1. [Railway CLI](https://docs.railway.app/develop/cli) installed
2. Railway account created
3. GitHub repository set up

## Architecture

The application consists of three main services:
- **Backend API** (FastAPI on port 8000)
- **WebSocket Server** (port 8001) 
- **Frontend** (React app served via nginx on port 80)
- **Database** (PostgreSQL with pgvector extension)
- **Cache** (Redis)

## Deployment Steps

### 1. Set up Railway Project

```bash
# Login to Railway
railway login

# Create a new project
railway new

# Link to your GitHub repository
railway connect
```

### 2. Choose Your Deployment Strategy

You have **three options** for deploying your services:

#### Option A: Single Container (Recommended for Small/Medium Scale)
Deploy both FastAPI and WebSocket in one container:

1. Create a single service from your main repository
2. Set environment variables:
   ```
   # No SERVICE specified = both services start
   DATABASE_URL=<your-postgres-connection-string>
   REPLICATE_API_TOKEN=<your-replicate-token>
   ENVIRONMENT=production
   DEBUG=false
   ```
3. Railway will expose both ports (8000 and 8001) automatically

#### Option B: Separate Services (Recommended for High Scale)
Deploy FastAPI and WebSocket as separate, scalable services:

**Backend API Service:**
```
SERVICE=backend
PORT=8000
DATABASE_URL=<your-postgres-connection-string>
REPLICATE_API_TOKEN=<your-replicate-token>
ENVIRONMENT=production
DEBUG=false
```

**WebSocket Service:**
```
SERVICE=websocket
PORT=8001
DATABASE_URL=<same-as-backend>
REPLICATE_API_TOKEN=<your-replicate-token>
SKIP_MIGRATIONS=true
ENVIRONMENT=production
DEBUG=false
```

#### Option C: Frontend Service
1. Create a service from the `frontend/` directory
2. Use the frontend Dockerfile
3. Set environment variables pointing to your backend URLs

### 3. Database Setup

#### Option A: Railway PostgreSQL Plugin
```bash
railway add postgresql
```
This automatically creates a PostgreSQL database with connection strings.

#### Option B: External PostgreSQL
If using external PostgreSQL (like AWS RDS), ensure it has the pgvector extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Redis Setup

```bash
railway add redis
```

### 5. Environment Variables

Set these variables in Railway dashboard for each service:

**Backend Service:**
```
SERVICE=backend
PORT=8000
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis-host:6379
REPLICATE_API_TOKEN=your_token_here
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO
```

**WebSocket Service:**
```
SERVICE=websocket  
PORT=8001
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis-host:6379
REPLICATE_API_TOKEN=your_token_here
SKIP_MIGRATIONS=true
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Frontend Service:**
```
REACT_APP_API_URL=https://your-backend-url.railway.app
REACT_APP_WS_URL=wss://your-websocket-url.railway.app
```

### 6. Custom Domains (Optional)

1. Go to Railway dashboard
2. Select your service
3. Go to Settings > Networking
4. Add your custom domain

### 7. Health Checks

Railway will automatically use the health check endpoints:
- Backend: `GET /health`
- WebSocket: `GET /health` 
- Frontend: `GET /`

## Local Testing with Docker

Before deploying, test locally:

```bash
# Copy environment template
cp .env.production .env

# Update .env with your local values
# Then run:
docker-compose up --build
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000  
- WebSocket: http://localhost:8001

## Monitoring and Logs

Railway provides built-in monitoring:
1. Go to your project dashboard
2. Click on any service to view:
   - Deployment logs
   - Runtime logs
   - Metrics (CPU, Memory, Network)
   - Environment variables

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Ensure DATABASE_URL is correct
   - Check if pgvector extension is installed
   - Verify database is accessible from Railway

2. **WebSocket connection failures:**
   - Ensure both backend and websocket services are deployed
   - Check CORS settings
   - Verify WebSocket URL in frontend

3. **Frontend API calls failing:**
   - Update REACT_APP_API_URL to point to your Railway backend URL
   - Check CORS configuration in backend

4. **Build failures:**
   - Check Dockerfile syntax
   - Ensure all dependencies are in pyproject.toml/package.json
   - Review build logs in Railway dashboard

### Debugging Commands

```bash
# View service logs
railway logs --service <service-name>

# Connect to service shell
railway shell --service <service-name>

# Check environment variables
railway variables --service <service-name>

# Redeploy service
railway redeploy --service <service-name>
```

## Cost Optimization

- Railway offers $5/month in free credits
- Use hobby plan for development
- Scale to pro plan for production workloads
- Monitor resource usage in dashboard

## Security Considerations

1. **Environment Variables:**
   - Never commit secrets to git
   - Use Railway's built-in secret management
   - Rotate API tokens regularly

2. **Database:**
   - Use SSL connections
   - Restrict access to Railway services only
   - Regular backups

3. **Application:**
   - Enable HTTPS only
   - Configure CORS properly
   - Use secure session management

## Support

- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status Page](https://status.railway.app/)