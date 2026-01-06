# ContextOS Backend

A production-ready FastAPI backend with async PostgreSQL, Redis caching, and Celery background tasks.

## Features

- ✅ **Async FastAPI** - High-performance async web framework
- ✅ **PostgreSQL** - Async SQLAlchemy with connection pooling
- ✅ **Redis** - Caching layer with async client
- ✅ **Celery** - Background task processing with Flower monitoring
- ✅ **Docker** - Complete containerized setup with docker-compose
- ✅ **Clean Architecture** - Modular, maintainable code structure
- ✅ **Type Hints** - Full type annotations throughout
- ✅ **Logging** - Structured JSON logging for production
- ✅ **Health Checks** - Kubernetes-ready liveness/readiness endpoints
- ✅ **RAG Pipeline** - Complete RAG implementation with FAISS vector search
- ✅ **AI-Ready** - Structured for easy AI integration

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/      # API endpoint definitions
│   │   ├── deps.py         # Dependency injection
│   │   └── router.py       # API router configuration
│   ├── core/
│   │   ├── config.py       # Application configuration
│   │   ├── logging.py      # Logging setup
│   │   └── exceptions.py   # Custom exceptions
│   ├── db/
│   │   ├── base.py         # Database base models
│   │   └── session.py      # Database session management
│   ├── models/             # SQLAlchemy models
│   ├── services/           # Business logic services
│   │   ├── redis_service.py    # Redis caching
│   │   ├── celery_app.py       # Celery configuration
│   │   └── tasks.py            # Background tasks
│   └── __init__.py
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-container setup
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f api
   ```

3. **Access services:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Flower (Celery): http://localhost:5555
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

4. **Stop services:**
   ```bash
   docker-compose down
   ```

5. **Stop and remove volumes:**
   ```bash
   docker-compose down -v
   ```

### Running Locally

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run PostgreSQL and Redis:**
   ```bash
   docker-compose up -d db redis
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

6. **Run Celery worker (in another terminal):**
   ```bash
   celery -A app.services.celery_app worker --loglevel=info
   ```

7. **Run Flower (optional):**
   ```bash
   celery -A app.services.celery_app flower
   ```

## API Endpoints

### Health Checks

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/ready` - Readiness check (DB + Redis)
- `GET /api/v1/health/live` - Liveness check

### Observability & Metrics

- `GET /api/v1/metrics` - Prometheus metrics export
- `GET /api/v1/usage` - Usage statistics with details
- `GET /api/v1/usage/summary` - High-level usage stats
- `GET /api/v1/usage/cache` - Cache performance metrics
- `GET /api/v1/usage/cost` - Cost breakdown and estimates
- `POST /api/v1/usage/cache/clear` - Clear query cache

**See [OBSERVABILITY.md](OBSERVABILITY.md) for detailed documentation**

### Background Tasks

- `POST /api/v1/tasks/example` - Create example task
- `POST /api/v1/tasks/long-running` - Create long-running task
- `GET /api/v1/tasks/{task_id}` - Get task status

### RAG Pipeline

- `POST /api/v1/rag/search` - Semantic search over documents
- `GET /api/v1/rag/sources` - Get available document sources
- `POST /api/v1/rag/ingest` - Ingest documents (async)
- `POST /api/v1/rag/ingest/sync` - Ingest documents (sync)
- `POST /api/v1/rag/reindex` - Rebuild vector index
- `GET /api/v1/rag/stats` - Get RAG statistics

**See [RAG_PIPELINE.md](RAG_PIPELINE.md) for detailed documentation**

### AI Agent (Gemini-Powered)

- `POST /api/v1/agent/query` - Query Gemini agent with RAG context
- `POST /api/v1/agent/chat` - Chat with conversational context
- `GET /api/v1/agent/tools` - List available tools
- `GET /api/v1/gemini/token-stats` - Get token usage statistics
- `GET /api/v1/gemini/tools` - List Gemini tools
- `GET /api/v1/gemini/health` - Gemini agent health

**Tools Available:**
- Knowledge base search
- Jira ticket operations
- Slack message operations
- Safe SQL queries

**See [GEMINI_INTEGRATION.md](GEMINI_INTEGRATION.md) for detailed documentation**

## Development

### Project Organization

- **API Layer** (`app/api/`) - Request/response handling
- **Core** (`app/core/`) - Configuration, logging, exceptions
- **Database** (`app/db/`) - Database setup and session management
- **Models** (`app/models/`) - SQLAlchemy ORM models
- **Services** (`app/services/`) - Business logic, external services

### Adding New Endpoints

1. Create endpoint file in `app/api/endpoints/`
2. Define routes using FastAPI decorators
3. Add router to `app/api/router.py`

### Adding New Models

1. Create model in `app/models/`
2. Inherit from `BaseModel` for automatic timestamps
3. Models are auto-discovered on startup

### Adding Background Tasks

1. Define task in `app/services/tasks.py`
2. Use `@celery_app.task` decorator
3. Access via Celery or API endpoints

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `POSTGRES_*` - Database connection
- `REDIS_*` - Redis connection
- `CELERY_*` - Celery configuration
- `CORS_ORIGINS` - Allowed CORS origins
- `DEBUG` - Enable debug mode
- `LOG_LEVEL` - Logging level

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py
```

## Monitoring

- **Flower**: Celery task monitoring at http://localhost:5555
- **Logs**: Structured JSON logs (production) or formatted (development)
- **Health Checks**: Built-in endpoints for Kubernetes/Docker health checks

## RAG Pipeline (NEW!)

Complete Retrieval-Augmented Generation pipeline included:

- **Document Ingestion** - Ingest plain text, Jira tickets, Slack messages
- **Text Chunking** - Smart chunking with overlap and metadata
- **Embeddings** - Sentence-transformers for semantic understanding
- **FAISS Index** - Fast similarity search over millions of vectors
- **Search API** - Semantic search with source attribution
- **Async Processing** - Background tasks for large ingestion jobs

### Quick Example

```bash
# Ingest documents
curl -X POST http://localhost:8000/api/v1/rag/ingest/sync \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"title": "Guide", "content": "...", "doc_type": "plain_text"}]}'

# Search
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how to reset password", "top_k": 5}'
```

See [RAG_PIPELINE.md](RAG_PIPELINE.md) for complete documentation.

## Ready for AI Integration

This backend includes a complete RAG pipeline and is structured for AI services:

1. **RAG Pipeline**: Built-in semantic search over your documents
2. **Services Layer**: Add AI service in `app/services/ai_service.py`
3. **Background Tasks**: Use Celery for long-running AI operations
4. **Caching**: Use Redis to cache AI responses
5. **Database**: Store AI interaction history in PostgreSQL
6. **API**: Expose AI features through REST endpoints

## Production Considerations

- [ ] Change `SECRET_KEY` in environment
- [ ] Set `DEBUG=False` in production
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerting
- [ ] Configure database backups
- [ ] Set appropriate resource limits
- [ ] Use proper secrets management

## License

MIT

