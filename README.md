# Survey Generation Engine

Transform RFQs into researcher-ready surveys, reducing cleanup time from 3-4 hours to <30 minutes using AI with golden standard examples.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- Python 3.11+ (for local development)

### Environment Setup
1. Copy environment variables:
```bash
cp .env.example .env
```

2. Set your OpenAI API key in `.env`:
```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Running with Docker
```bash
# Start all services
docker-compose up -d

# Run database migrations
docker-compose run migrate

# View logs
docker-compose logs -f app
```

The API will be available at http://localhost:8000

### API Documentation
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 Core Workflow

1. **Submit RFQ** → `POST /api/v1/rfq/`
2. **Retrieve Survey** → `GET /api/v1/survey/{id}`
3. **Submit Edits** → `PUT /api/v1/survey/{id}/edit`
4. **Analytics** → `GET /api/v1/analytics/quality-trends`

## 🏗️ Architecture

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL 15+ with pgvector extension
- **AI/ML**: OpenAI API, Sentence Transformers
- **Orchestration**: LangGraph for agent workflows
- **Caching**: Redis
- **Deployment**: Docker

## 🧪 Development

### Local Setup
```bash
# Install UV (fast Python package manager)
pip install uv

# Install dependencies
uv pip install -e .

# Run locally
python src/main.py
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## 📈 Success Metrics

- **Generation Time**: <30 seconds end-to-end
- **Golden Similarity**: >0.75 similarity score
- **Cleanup Time**: <30 minutes (vs 3-4 hours baseline)
- **Methodology Compliance**: 80%+ validation pass rate

## 🔧 Configuration

Key environment variables (see `.env.example`):

- `GOLDEN_SIMILARITY_THRESHOLD`: Quality threshold (default: 0.75)
- `MAX_GOLDEN_EXAMPLES`: Examples per generation (default: 3)
- `METHODOLOGY_VALIDATION_STRICT`: Strict compliance checking
- `ENABLE_EDIT_TRACKING`: Collect training data

## 🗂️ Project Structure

```
src/
├── api/             # FastAPI endpoints
├── config/          # Settings and configuration  
├── database/        # Models and connection
├── services/        # Business logic
└── workflows/       # LangGraph workflow nodes
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details