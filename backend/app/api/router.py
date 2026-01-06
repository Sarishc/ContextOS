"""API router configuration."""
from fastapi import APIRouter

from app.api.endpoints import health, tasks, rag

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

