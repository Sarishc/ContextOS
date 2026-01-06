"""Task management endpoints."""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.tasks import example_task, long_running_task, send_notification
from app.services.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class TaskCreate(BaseModel):
    """Task creation request."""
    
    data: Dict[str, Any] = Field(..., description="Task data")


class TaskResponse(BaseModel):
    """Task response."""
    
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    """Task status response."""
    
    task_id: str
    state: str
    result: Any = None
    meta: Dict[str, Any] = {}


@router.post("/tasks/example", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_example_task(task_data: TaskCreate) -> TaskResponse:
    """Create an example background task."""
    try:
        task = example_task.apply_async(args=[task_data.data])
        
        logger.info(f"Created example task: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message="Task submitted successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.post("/tasks/long-running", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_long_running_task(duration: int = 10) -> TaskResponse:
    """Create a long-running background task."""
    try:
        task = long_running_task.apply_async(args=[duration])
        
        logger.info(f"Created long-running task: {task.id}")
        
        return TaskResponse(
            task_id=task.id,
            status="pending",
            message=f"Long-running task ({duration}s) submitted successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    """Get task status by ID."""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        response = TaskStatus(
            task_id=task_id,
            state=task_result.state,
            result=task_result.result if task_result.ready() else None,
            meta=task_result.info if isinstance(task_result.info, dict) else {}
        )
        
        return response
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )

