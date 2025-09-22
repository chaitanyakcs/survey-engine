# Container Deployment Guide for Survey Engine

This guide provides optimized deployment configurations for various container platforms.

## 🐳 Docker Deployment

### Quick Start
```bash
# Generate container-optimized files
python3 fix_server_restarts_docker.py

# Build and run
docker build -f Dockerfile.optimized -t survey-engine .
docker run -p 8080:8080 -p 8000:8000 -e DATABASE_URL="your-db-url" survey-engine
```

### Features
- ✅ Optimized model loading (prevents multiple loads)
- ✅ Health checks and graceful shutdown
- ✅ Nginx reverse proxy with rate limiting
- ✅ Security headers and gzip compression
- ✅ Proper signal handling

## 🐙 Docker Compose Deployment

### Quick Start
```bash
# Generate container-optimized files
python3 fix_server_restarts_docker.py

# Start all services
docker-compose -f docker-compose.optimized.yml up -d

# View logs
docker-compose -f docker-compose.optimized.yml logs -f
```

### Services Included
- **survey-engine**: Main application
- **db**: PostgreSQL database
- **redis**: Redis cache (optional)

### Environment Variables
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:password@db:5432/survey_engine
  - PORT=8080
  - PYTHONPATH=/app/src
```

## ☸️ Kubernetes Deployment

### Quick Start
```bash
# Generate container-optimized files
python3 fix_server_restarts_docker.py

# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods
kubectl get services
```

### Features
- ✅ Horizontal scaling (2 replicas)
- ✅ Resource limits and requests
- ✅ Health checks (liveness/readiness)
- ✅ LoadBalancer service
- ✅ Configurable secrets

### Scaling
```bash
# Scale up
kubectl scale deployment survey-engine --replicas=5

# Check resource usage
kubectl top pods
```

## 🚀 Cloud Platform Deployments

### AWS ECS
```yaml
# ecs-task-definition.json
{
  "family": "survey-engine",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "survey-engine",
      "image": "your-account.dkr.ecr.region.amazonaws.com/survey-engine:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/survey_engine"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/survey-engine",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: survey-engine
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/your-project/survey-engine:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: survey-engine-secrets
              key: database-url
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
          requests:
            cpu: "1"
            memory: "2Gi"
```

### Azure Container Instances
```yaml
# azure-container-instance.yaml
apiVersion: 2019-12-01
location: eastus
name: survey-engine
properties:
  containers:
  - name: survey-engine
    properties:
      image: your-registry.azurecr.io/survey-engine:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 8080
        protocol: TCP
      environmentVariables:
      - name: DATABASE_URL
        value: "postgresql://user:pass@server.database.windows.net:5432/survey_engine"
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8080
  restartPolicy: Always
```

## 🔧 Configuration Options

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `PORT` | Nginx port | 8080 |
| `PYTHONPATH` | Python path | /app/src |
| `WORKERS` | Number of FastAPI workers | 1 |
| `LOG_LEVEL` | Logging level | INFO |

### Resource Requirements
| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| **Minimum** | 500m | 1Gi | 10Gi |
| **Recommended** | 1000m | 2Gi | 20Gi |
| **Production** | 2000m | 4Gi | 50Gi |

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- `GET /health` - Application health
- `GET /api/health` - API health
- `GET /metrics` - Prometheus metrics (if enabled)

### Logging
All deployments include structured logging:
```json
{
  "timestamp": "2025-01-21T14:30:00Z",
  "level": "INFO",
  "message": "Application started",
  "service": "survey-engine",
  "version": "1.0.0"
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Model Loading Timeout**
   ```bash
   # Increase timeout in nginx config
   proxy_read_timeout 1200s;
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker exec -it container_name psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats container_name
   kubectl top pod pod-name
   ```

### Debug Commands
```bash
# Docker
docker logs container_name
docker exec -it container_name /bin/bash

# Kubernetes
kubectl logs deployment/survey-engine
kubectl exec -it pod-name -- /bin/bash

# Check health
curl http://localhost:8080/health
```

## 🔄 Updates and Maintenance

### Rolling Updates
```bash
# Docker Compose
docker-compose -f docker-compose.optimized.yml up -d --no-deps survey-engine

# Kubernetes
kubectl set image deployment/survey-engine survey-engine=survey-engine:v2.0.0
```

### Database Migrations
```bash
# Run migrations
docker exec -it container_name python3 -c "
from src.database.migrations import run_migrations
run_migrations()
"
```

## 📈 Performance Optimization

### Production Recommendations
1. **Use multiple replicas** for high availability
2. **Enable Redis caching** for better performance
3. **Use CDN** for static assets
4. **Monitor resource usage** and scale accordingly
5. **Use persistent volumes** for database data

### Scaling Strategies
- **Horizontal**: Add more replicas
- **Vertical**: Increase CPU/memory
- **Database**: Use read replicas
- **Caching**: Implement Redis cluster

This guide provides everything you need to deploy Survey Engine on any container platform with optimal performance and reliability!
