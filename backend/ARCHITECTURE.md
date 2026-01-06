# Architecture Documentation

## Overview

ContextOS Backend is a production-ready FastAPI application built with clean architecture principles, designed for scalability and AI integration.

## Technology Stack

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11**: Latest stable Python version
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: Lightning-fast ASGI server

### Database Layer
- **PostgreSQL 16**: Robust relational database
- **SQLAlchemy 2.0**: Async ORM with advanced features
- **Alembic**: Database migration tool
- **asyncpg**: High-performance PostgreSQL driver

### Caching & Message Broker
- **Redis 7**: In-memory data store for caching
- **redis-py**: Async Redis client

### Background Tasks
- **Celery**: Distributed task queue
- **Flower**: Real-time Celery monitoring

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## Project Structure

```
backend/
├── app/                        # Application code
│   ├── api/                   # API layer
│   │   ├── endpoints/         # API endpoints
│   │   │   ├── health.py     # Health check endpoints
│   │   │   └── tasks.py      # Task management endpoints
│   │   ├── deps.py           # Dependency injection
│   │   └── router.py         # Router configuration
│   ├── core/                  # Core functionality
│   │   ├── config.py         # Application configuration
│   │   ├── logging.py        # Logging setup
│   │   └── exceptions.py     # Custom exceptions
│   ├── db/                    # Database layer
│   │   ├── base.py           # Base models and mixins
│   │   └── session.py        # Session management
│   ├── models/                # Database models
│   │   └── example.py        # Example model
│   └── services/              # Business logic
│       ├── redis_service.py  # Redis caching service
│       ├── celery_app.py     # Celery configuration
│       └── tasks.py          # Background tasks
├── alembic/                   # Database migrations
│   ├── versions/             # Migration files
│   ├── env.py               # Alembic environment
│   └── script.py.mako       # Migration template
├── scripts/                   # Utility scripts
│   ├── start.sh             # Start services
│   ├── stop.sh              # Stop services
│   ├── test.sh              # Test API
│   └── logs.sh              # View logs
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Service orchestration
├── alembic.ini               # Alembic configuration
├── Makefile                  # Development commands
└── README.md                 # Documentation
```

## Architecture Layers

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Components**:
- **Endpoints**: Route handlers organized by domain
- **Dependencies**: Shared dependencies (DB sessions, services)
- **Router**: Central router configuration

**Responsibilities**:
- Request validation
- Response formatting
- Error handling
- API documentation

### 2. Core Layer (`app/core/`)

**Purpose**: Application-wide functionality

**Components**:
- **Config**: Environment-based configuration
- **Logging**: Structured logging setup
- **Exceptions**: Custom exception hierarchy

**Responsibilities**:
- Configuration management
- Logging infrastructure
- Cross-cutting concerns

### 3. Database Layer (`app/db/`)

**Purpose**: Database connection and session management

**Components**:
- **Base**: Base models with common fields
- **Session**: Async session factory

**Responsibilities**:
- Database connection pooling
- Session lifecycle management
- Transaction handling

### 4. Models Layer (`app/models/`)

**Purpose**: Data models and database schema

**Components**:
- Domain models (e.g., `Example`)
- SQLAlchemy ORM models

**Responsibilities**:
- Database schema definition
- Data validation
- Relationships between entities

### 5. Services Layer (`app/services/`)

**Purpose**: Business logic and external integrations

**Components**:
- **Redis Service**: Caching operations
- **Celery App**: Background task configuration
- **Tasks**: Asynchronous task definitions

**Responsibilities**:
- Business logic implementation
- External service integration
- Background processing

## Design Patterns

### Dependency Injection

Used throughout for loose coupling:

```python
# Example: Injecting database session
async def get_items(db: AsyncSession = Depends(get_db_session)):
    # Use db session
    pass
```

### Repository Pattern

Encapsulated data access:

```python
class ItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, id: int):
        # Data access logic
        pass
```

### Service Layer Pattern

Business logic separated from API layer:

```python
class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository
    
    async def process_item(self, data):
        # Business logic
        pass
```

### Factory Pattern

Used for creating instances:

```python
# Session factory
AsyncSessionLocal = async_sessionmaker(engine)
```

## Data Flow

### Request Flow

```
1. Client Request
   ↓
2. FastAPI Router
   ↓
3. Endpoint Handler
   ↓
4. Dependency Injection (DB, Services)
   ↓
5. Business Logic (Services)
   ↓
6. Data Access (Models/DB)
   ↓
7. Response Formatting
   ↓
8. Client Response
```

### Background Task Flow

```
1. API Endpoint
   ↓
2. Task Submission (Celery)
   ↓
3. Redis Queue
   ↓
4. Celery Worker
   ↓
5. Task Execution
   ↓
6. Result Storage (Redis)
   ↓
7. Status Check (API)
```

## Database Design

### Base Model Pattern

All models inherit from `BaseModel`:

```python
class BaseModel(Base, TimestampMixin):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
```

**Provides**:
- Auto-incrementing ID
- Created/updated timestamps
- Common methods

### Migration Strategy

- **Automatic**: Alembic auto-generates migrations from model changes
- **Versioned**: Each migration has unique version ID
- **Reversible**: All migrations support up/down

## Caching Strategy

### Redis Usage

1. **Response Caching**: Cache frequently accessed data
2. **Session Storage**: Store user sessions
3. **Rate Limiting**: Track API usage
4. **Task Results**: Store background task results

### Cache Keys

Convention: `{namespace}:{entity}:{id}`

Examples:
- `user:profile:123`
- `ai:response:abc-def`
- `cache:query:hash-value`

## Background Tasks

### Task Types

1. **Short Tasks** (<30s): Quick operations
2. **Long Tasks** (>30s): Heavy processing
3. **Periodic Tasks**: Scheduled jobs

### Task Design

```python
@celery_app.task(bind=True)
def my_task(self, data):
    # Update progress
    self.update_state(
        state='PROGRESS',
        meta={'current': 1, 'total': 10}
    )
    # Process
    return result
```

## Error Handling

### Exception Hierarchy

```
AppException (Base)
├── DatabaseException
├── CacheException
├── ValidationException
└── NotFoundException
```

### Error Response Format

```json
{
    "error": "Error message",
    "details": {
        "field": "Additional info"
    }
}
```

## Logging

### Log Levels

- **DEBUG**: Development debugging
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error conditions
- **CRITICAL**: Critical issues

### Log Format

**Development**: Human-readable
```
2024-01-06 12:00:00 - app.api - INFO - Request received
```

**Production**: JSON
```json
{
    "timestamp": "2024-01-06T12:00:00Z",
    "level": "INFO",
    "logger": "app.api",
    "message": "Request received"
}
```

## Security Considerations

### Current Implementation

- [x] Environment-based secrets
- [x] CORS configuration
- [x] Input validation (Pydantic)
- [x] SQL injection prevention (ORM)
- [x] Non-root Docker user

### Recommendations for Production

- [ ] JWT authentication
- [ ] Rate limiting
- [ ] API key management
- [ ] HTTPS/TLS
- [ ] Secret management (Vault)
- [ ] Database encryption
- [ ] Audit logging

## Scalability

### Horizontal Scaling

- **API**: Multiple API containers behind load balancer
- **Workers**: Multiple Celery workers
- **Database**: Read replicas, connection pooling
- **Redis**: Redis Cluster or Sentinel

### Vertical Scaling

- Increase container resources (CPU, memory)
- Optimize database queries
- Implement caching strategies
- Use connection pooling

## Monitoring & Observability

### Health Checks

1. **Liveness**: `/api/v1/health/live` - Is app running?
2. **Readiness**: `/api/v1/health/ready` - Can app serve traffic?

### Metrics to Monitor

- Request rate
- Response time
- Error rate
- Database connections
- Redis memory usage
- Celery queue length
- Worker availability

### Recommended Tools

- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **ELK Stack**: Log aggregation
- **Sentry**: Error tracking

## AI Integration Points

The architecture is designed for easy AI integration:

### 1. AI Service Layer

```python
# app/services/ai_service.py
class AIService:
    async def generate_response(self, prompt):
        # AI logic here
        pass
```

### 2. Background Processing

```python
# Long-running AI tasks
@celery_app.task
def process_ai_request(data):
    # AI processing
    pass
```

### 3. Caching AI Responses

```python
# Cache expensive AI operations
cache_key = f"ai:response:{prompt_hash}"
cached = await redis_service.get(cache_key)
```

### 4. Database Storage

```python
# Store AI interactions
class AIInteraction(BaseModel):
    prompt = Column(Text)
    response = Column(Text)
    model = Column(String)
```

## Testing Strategy

### Test Levels

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test endpoints
4. **Load Tests**: Test performance

### Test Structure

```
tests/
├── unit/
├── integration/
├── api/
└── conftest.py
```

## Deployment Architecture

### Development

```
Developer Machine
└── Docker Compose
    ├── API Container
    ├── PostgreSQL Container
    ├── Redis Container
    ├── Celery Worker Container
    └── Flower Container
```

### Production (Example)

```
Load Balancer
├── API Instance 1
├── API Instance 2
└── API Instance 3
    │
    ├─→ PostgreSQL (Primary + Replicas)
    ├─→ Redis Cluster
    └─→ Celery Workers (Auto-scaling)
```

## Performance Optimization

### Database

- [ ] Index frequently queried columns
- [ ] Use connection pooling
- [ ] Implement query optimization
- [ ] Add read replicas
- [ ] Partition large tables

### API

- [ ] Enable response compression
- [ ] Implement caching headers
- [ ] Use async endpoints
- [ ] Optimize serialization
- [ ] Add CDN for static content

### Caching

- [ ] Cache expensive queries
- [ ] Implement cache warming
- [ ] Use cache invalidation strategies
- [ ] Monitor cache hit rates

## Future Enhancements

- [ ] GraphQL API support
- [ ] WebSocket support for real-time
- [ ] Multi-tenancy
- [ ] Advanced authentication (OAuth2, SAML)
- [ ] API versioning strategy
- [ ] Event sourcing
- [ ] CQRS pattern
- [ ] Microservices split

