# AWS Migration Plan for Survey Engine

## Current Railway Setup
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL with pgvector extension
- **Frontend**: React + TypeScript
- **AI**: Replicate API integration
- **Deployment**: Railway with Docker

## AWS Target Architecture

### 1. Database Layer
```
Amazon RDS PostgreSQL
├── Instance: db.t3.medium (2 vCPU, 4GB RAM)
├── Storage: 100GB GP2
├── Extensions: pgvector, pgcrypto
├── Backup: 7-day retention
└── Multi-AZ: Yes (for production)
```

### 2. Application Layer
```
Amazon ECS Fargate
├── Task Definition: survey-engine
├── Service: 2-10 tasks (auto-scaling)
├── Load Balancer: Application Load Balancer
├── Container Registry: Amazon ECR
└── Logs: CloudWatch Logs
```

### 3. Frontend Layer
```
Amazon S3 + CloudFront
├── Static hosting on S3
├── CloudFront CDN
├── Custom domain with SSL
└── CI/CD with GitHub Actions
```

## Migration Steps

### Phase 1: Database Migration
1. **Create RDS PostgreSQL instance**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier survey-engine-db \
     --db-instance-class db.t3.medium \
     --engine postgres \
     --engine-version 15.4 \
     --master-username postgres \
     --master-user-password <secure-password> \
     --allocated-storage 100 \
     --storage-type gp2 \
     --vpc-security-group-ids sg-xxxxxxxxx \
     --db-subnet-group-name survey-engine-subnet-group
   ```

2. **Install pgvector extension**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   ```

3. **Export data from Railway**
   ```bash
   # Export schema and data
   pg_dump -h postgres.railway.internal -U postgres -d railway > survey_engine_backup.sql
   ```

4. **Import to RDS**
   ```bash
   psql -h your-rds-endpoint.amazonaws.com -U postgres -d survey_engine < survey_engine_backup.sql
   ```

### Phase 2: Container Migration
1. **Create ECR repository**
   ```bash
   aws ecr create-repository --repository-name survey-engine
   ```

2. **Build and push Docker image**
   ```bash
   # Build image
   docker build -t survey-engine .
   
   # Tag for ECR
   docker tag survey-engine:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/survey-engine:latest
   
   # Push to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/survey-engine:latest
   ```

3. **Create ECS Task Definition**
   ```json
   {
     "family": "survey-engine",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "survey-engine",
         "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/survey-engine:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "postgresql://postgres:password@your-rds-endpoint:5432/survey_engine"
           },
           {
             "name": "REPLICATE_API_TOKEN",
             "value": "your-replicate-token"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/survey-engine",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

### Phase 3: Frontend Migration
1. **Build React app**
   ```bash
   cd frontend
   npm run build
   ```

2. **Upload to S3**
   ```bash
   aws s3 sync build/ s3://survey-engine-frontend --delete
   ```

3. **Create CloudFront distribution**
   ```bash
   aws cloudfront create-distribution \
     --distribution-config file://cloudfront-config.json
   ```

### Phase 4: CI/CD Pipeline
1. **GitHub Actions workflow**
   ```yaml
   name: Deploy to AWS
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v1
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: us-east-1
         
         - name: Build and push Docker image
           run: |
             docker build -t survey-engine .
             docker tag survey-engine:latest $ECR_REGISTRY/survey-engine:latest
             docker push $ECR_REGISTRY/survey-engine:latest
         
         - name: Update ECS service
           run: |
             aws ecs update-service --cluster survey-engine-cluster --service survey-engine-service --force-new-deployment
   ```

## Cost Comparison

### Railway (Current)
- **Database**: ~$20/month
- **Application**: ~$5/month
- **Total**: ~$25/month

### AWS (Projected)
- **RDS PostgreSQL**: ~$30/month
- **ECS Fargate**: ~$15/month
- **S3 + CloudFront**: ~$5/month
- **Total**: ~$50/month

## Benefits of AWS Migration

1. **Better Control**: Full control over infrastructure
2. **Scalability**: Auto-scaling based on demand
3. **Reliability**: Multi-AZ deployment, automated backups
4. **Security**: VPC, IAM, security groups
5. **Monitoring**: CloudWatch, X-Ray tracing
6. **Cost Optimization**: Reserved instances, spot instances

## Migration Timeline

- **Week 1**: Database migration and testing
- **Week 2**: Application containerization and ECS setup
- **Week 3**: Frontend migration and CDN setup
- **Week 4**: CI/CD pipeline and production cutover

## Next Steps

1. **Create AWS account** and set up billing alerts
2. **Set up VPC** with public/private subnets
3. **Create RDS instance** and migrate data
4. **Build and test** containerized application
5. **Set up monitoring** and alerting
6. **Plan cutover** with minimal downtime
