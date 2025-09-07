# 🐳 Docker Quick Start Guide

## Prerequisites

- Docker Desktop installed and running
- Git (to clone the repository)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd survey-engine
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

**Required Environment Variables:**
- `REPLICATE_API_TOKEN` - Your Replicate API token for AI generation
- `OPENAI_API_KEY` - Your OpenAI API key (optional, for fallback)

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8001

### 5. Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Development Mode

For development with hot reload:

```bash
# Use the development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Make sure ports 3000, 8000, 8001, 5432, and 6379 are available
2. **API key missing**: Ensure `REPLICATE_API_TOKEN` is set in `.env`
3. **Database connection**: Wait for PostgreSQL to fully initialize (can take 30-60 seconds)

### Useful Commands

```bash
# Test the Docker setup
./test-docker-setup.sh

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f websocket

# Restart a specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build -d

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Check service health
docker-compose ps
```

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   WebSocket     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (WebSocket)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Port: 5432    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │   Port: 6379    │
                    └─────────────────┘
```

## Production Deployment

For production deployment, see:
- `RAILWAY_DEPLOYMENT.md` - Railway deployment guide
- `docker-compose.cloud.yml` - Cloud-optimized configuration

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Run the test script: `./test-docker-setup.sh`
3. Verify environment variables in `.env`
4. Ensure all required ports are available
