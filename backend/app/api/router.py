"""API router configuration."""
from fastapi import APIRouter

from app.api.endpoints import health, tasks, rag, agent, agent_v2, gemini, metrics

api_router = APIRouter()

# Include routers
api_router.include_router(
    health.router,
    tags=["health"]
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)

api_router.include_router(
    rag.router,
    prefix="/rag",
    tags=["rag"]
)

api_router.include_router(
    agent_v2.router,
    prefix="/agent",
    tags=["agent"]
)

# Keep original agent endpoint for backward compatibility
api_router.include_router(
    agent.router,
    prefix="/agent/v1",
    tags=["agent-v1"]
)

api_router.include_router(
    gemini.router,
    prefix="/gemini",
    tags=["gemini"]
)

api_router.include_router(
    metrics.router,
    tags=["metrics"]
)

