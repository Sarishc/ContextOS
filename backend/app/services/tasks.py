"""Celery background tasks."""
import asyncio
from typing import Any, Dict
from celery import Task
from app.services.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


class AsyncTask(Task):
    """Base async task class."""
    
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute task."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))
    
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run async task - override in subclasses."""
        raise NotImplementedError


@celery_app.task(name="app.tasks.example_task", bind=True)
def example_task(self: Task, data: Dict[str, Any]) -> Dict[str, Any]:
    """Example background task."""
    logger.info(f"Executing example task with data: {data}")
    
    # Simulate some work
    result = {
        "task_id": self.request.id,
        "status": "completed",
        "data": data,
        "message": "Task completed successfully"
    }
    
    logger.info(f"Example task completed: {result}")
    return result


@celery_app.task(name="app.tasks.long_running_task", bind=True)
def long_running_task(self: Task, duration: int = 10) -> Dict[str, Any]:
    """Example long-running task."""
    import time
    
    logger.info(f"Starting long-running task for {duration} seconds")
    
    for i in range(duration):
        time.sleep(1)
        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1,
                "total": duration,
                "status": f"Processing {i + 1}/{duration}"
            }
        )
    
    result = {
        "task_id": self.request.id,
        "status": "completed",
        "duration": duration,
        "message": "Long-running task completed"
    }
    
    logger.info(f"Long-running task completed: {result}")
    return result


@celery_app.task(name="app.tasks.send_notification", bind=True)
def send_notification(
    self: Task,
    recipient: str,
    message: str,
    notification_type: str = "info"
) -> Dict[str, Any]:
    """Send notification task (placeholder for future implementation)."""
    logger.info(f"Sending {notification_type} notification to {recipient}: {message}")
    
    # Placeholder for actual notification logic
    # This could integrate with email, SMS, push notifications, etc.
    
    return {
        "task_id": self.request.id,
        "status": "sent",
        "recipient": recipient,
        "type": notification_type,
        "message": "Notification sent successfully"
    }


# RAG Pipeline Tasks

@celery_app.task(name="app.tasks.process_documents", bind=True)
def process_documents(self: Task, documents_data: list) -> Dict[str, Any]:
    """Process and ingest documents in background."""
    import asyncio
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion_service import ingestion_service
    from app.core.schemas import DocumentCreate
    
    logger.info(f"Processing {len(documents_data)} documents")
    
    async def _process():
        async with AsyncSessionLocal() as db:
            try:
                # Convert to DocumentCreate objects
                documents = [DocumentCreate(**doc) for doc in documents_data]
                
                # Ingest documents
                result = await ingestion_service.ingest_documents(
                    db, documents, generate_embeddings=True
                )
                
                # Rebuild vector index
                indexed_count = await ingestion_service.rebuild_vector_index(db)
                
                return {
                    "task_id": self.request.id,
                    "status": "completed",
                    "documents_processed": len(result),
                    "vectors_indexed": indexed_count,
                    "message": "Documents processed and indexed successfully"
                }
            except Exception as e:
                logger.error(f"Error processing documents: {e}")
                return {
                    "task_id": self.request.id,
                    "status": "failed",
                    "error": str(e)
                }
    
    # Run async function
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_process())
    return result


@celery_app.task(name="app.tasks.rebuild_index", bind=True)
def rebuild_index(self: Task, doc_type: str = None) -> Dict[str, Any]:
    """Rebuild FAISS vector index in background."""
    import asyncio
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion_service import ingestion_service
    
    logger.info(f"Rebuilding vector index for doc_type={doc_type}")
    
    async def _rebuild():
        async with AsyncSessionLocal() as db:
            try:
                count = await ingestion_service.rebuild_vector_index(db, doc_type=doc_type)
                
                return {
                    "task_id": self.request.id,
                    "status": "completed",
                    "vectors_indexed": count,
                    "message": f"Index rebuilt with {count} vectors"
                }
            except Exception as e:
                logger.error(f"Error rebuilding index: {e}")
                return {
                    "task_id": self.request.id,
                    "status": "failed",
                    "error": str(e)
                }
    
    # Run async function
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_rebuild())
    return result


@celery_app.task(name="app.tasks.generate_embeddings", bind=True)
def generate_embeddings_task(self: Task, chunk_ids: list) -> Dict[str, Any]:
    """Generate embeddings for specific chunks."""
    import asyncio
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion_service import ingestion_service
    from app.models.document import DocumentChunk
    from sqlalchemy import select
    
    logger.info(f"Generating embeddings for {len(chunk_ids)} chunks")
    
    async def _generate():
        async with AsyncSessionLocal() as db:
            try:
                # Fetch chunks
                result = await db.execute(
                    select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
                )
                chunks = result.scalars().all()
                
                # Generate embeddings
                await ingestion_service.generate_embeddings_for_chunks(db, list(chunks))
                await db.commit()
                
                return {
                    "task_id": self.request.id,
                    "status": "completed",
                    "embeddings_generated": len(chunks),
                    "message": "Embeddings generated successfully"
                }
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                return {
                    "task_id": self.request.id,
                    "status": "failed",
                    "error": str(e)
                }
    
    # Run async function
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_generate())
    return result

