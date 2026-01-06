# ContextOS - AI Agent System

A production-ready AI agent system with RAG (Retrieval-Augmented Generation), tool calling, and observability.

## Architecture

```
┌─────────────────┐
│   React UI      │  ← Chat interface, metrics dashboard
│   (Port 3000)   │
└────────┬────────┘
         │
         ↓ HTTP
┌─────────────────┐
│  FastAPI Backend│  ← Agent, RAG, Tools
│   (Port 8000)   │
└────────┬────────┘
         │
    ┌────┴─────┐
    ↓          ↓
┌─────────┐ ┌──────────┐
│PostgreSQL│ │  Redis   │
│(Port 5432)│(Port 6379)│
└──────────┘ └──────────┘
```

## Features

### Frontend
- **Chat Interface**: Talk to the AI agent
- **Source Display**: See RAG sources for each response
- **Action Tracking**: Monitor tool executions
- **Metrics Dashboard**: Token usage, costs, latency

### Backend
- **RAG Pipeline**: Document ingestion, chunking, embedding, FAISS vector search
- **AI Agent**: Gemini-powered agent with tool calling
- **Tool System**: Jira, Slack, SQL, document search
- **Observability**: Request tracing, metrics, rate limiting, caching
- **Background Tasks**: Celery workers for async processing

## Quick Start

### One-Command Start

```bash
./start.sh
```

This will:
1. Start the backend (PostgreSQL, Redis, API, Celery)
2. Install frontend dependencies
3. Start the frontend development server

### Manual Start

**Backend:**
```bash
cd backend
docker-compose up -d
```

**Frontend:**
```bash
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

### Access Points

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Flower (Celery): http://localhost:5555

## Project Structure

```
/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, logging, metrics
│   │   ├── models/      # SQLAlchemy models
│   │   └── services/    # Business logic
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── components/          # React components
├── services/            # API client
├── App.tsx             # Main app
└── package.json

```

## Environment Variables

### Backend (.env in backend/)
```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=contextos

# Redis
REDIS_URL=redis://redis:6379/0

# Gemini
GEMINI_API_KEY=your-api-key-here

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend (.env in root)
```env
VITE_API_URL=http://localhost:8000
```

## API Endpoints

### Agent
- `POST /agent/query` - Send a query to the agent

### RAG
- `POST /rag/ingest` - Ingest documents
- `POST /rag/search` - Search documents
- `GET /rag/sources` - List all sources

### Observability
- `GET /metrics` - Prometheus metrics
- `GET /usage` - Usage statistics
- `GET /health` - Health check

### Gemini
- `GET /gemini/token-stats` - Token usage stats
- `GET /gemini/tools` - Available tools

## Development

### Backend

**Run tests:**
```bash
cd backend
./scripts/test.sh
```

**View logs:**
```bash
cd backend
docker-compose logs -f api
```

**Database migrations:**
```bash
cd backend
docker-compose exec api alembic revision --autogenerate -m "description"
docker-compose exec api alembic upgrade head
```

### Frontend

**Build for production:**
```bash
npm run build
```

**Preview production build:**
```bash
npm run preview
```

**Type checking:**
```bash
npx tsc --noEmit
```

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite
- TailwindCSS
- Lucide Icons

### Backend
- FastAPI
- PostgreSQL + SQLAlchemy
- Redis
- Celery
- FAISS
- Sentence Transformers
- Google Gemini API
- Prometheus

## Documentation

- [Frontend Setup](./FRONTEND_SETUP.md)
- [Backend Architecture](./backend/ARCHITECTURE.md)
- [RAG Pipeline](./backend/RAG_PIPELINE.md)
- [AI Agent](./backend/AI_AGENT.md)
- [Gemini Integration](./backend/GEMINI_INTEGRATION.md)
- [Observability](./backend/OBSERVABILITY.md)
- [Quick Start](./backend/QUICKSTART.md)

## Troubleshooting

### Backend won't start
```bash
cd backend
docker-compose down -v
docker-compose up -d
```

### Frontend can't connect to backend
1. Check backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend
3. Verify `.env` has correct API URL

### Database issues
```bash
cd backend
docker-compose exec db psql -U postgres -d contextos
```

### Clear all data and restart
```bash
cd backend
docker-compose down -v
rm -rf data/
docker-compose up -d
```

## Production Deployment

### Backend
1. Set production environment variables
2. Use production-ready database (managed PostgreSQL)
3. Set up Redis cluster
4. Configure reverse proxy (nginx)
5. Enable HTTPS
6. Set up monitoring (Prometheus + Grafana)

### Frontend
1. Build: `npm run build`
2. Deploy `dist/` to CDN or static hosting
3. Update `VITE_API_URL` to production backend
4. Configure DNS and SSL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in `backend/`
- Review API docs at http://localhost:8000/docs

---

Built with ❤️ using FastAPI + React

