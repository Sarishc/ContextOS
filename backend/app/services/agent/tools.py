"""Built-in tools for the AI agent."""
from typing import Any, Dict, List
from app.services.agent.base import Tool, ToolParameter
from app.core.logging import get_logger

logger = get_logger(__name__)


# Tool implementations

async def search_documents_tool(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search documents using RAG pipeline.
    
    Args:
        query: Search query
        top_k: Number of results to return
        
    Returns:
        Search results with sources
    """
    from app.services.search_service import search_service
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        results, execution_time = await search_service.search(
            db=db,
            query=query,
            top_k=top_k
        )
        
        return {
            "success": True,
            "results": [
                {
                    "content": r.chunk_content,
                    "source": r.document_source,
                    "title": r.document_title,
                    "score": r.similarity_score
                }
                for r in results
            ],
            "count": len(results),
            "execution_time": execution_time
        }


async def get_document_sources_tool() -> Dict[str, Any]:
    """
    Get available document sources.
    
    Returns:
        List of available sources
    """
    from app.services.ingestion_service import ingestion_service
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        sources = await ingestion_service.get_sources(db)
        stats = await ingestion_service.get_total_stats(db)
        
        return {
            "success": True,
            "sources": sources,
            "total_documents": stats['total_documents'],
            "total_chunks": stats['total_chunks']
        }


async def create_task_tool(task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a background task.
    
    Args:
        task_type: Type of task to create
        data: Task data
        
    Returns:
        Task information
    """
    from app.services.tasks import example_task
    
    task = example_task.apply_async(args=[data])
    
    return {
        "success": True,
        "task_id": task.id,
        "task_type": task_type,
        "status": "pending"
    }


async def get_system_stats_tool() -> Dict[str, Any]:
    """
    Get system statistics.
    
    Returns:
        System statistics
    """
    from app.services.ingestion_service import ingestion_service
    from app.services.vector_store import vector_store
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        db_stats = await ingestion_service.get_total_stats(db)
        vector_stats = vector_store.get_stats()
        
        return {
            "success": True,
            "database": db_stats,
            "vector_store": vector_stats,
            "status": "operational"
        }


# Tool definitions

SEARCH_DOCUMENTS = Tool(
    name="search_documents",
    description="Search through ingested documents using semantic search. Use this when you need to find information from the knowledge base.",
    parameters=[
        ToolParameter(
            name="query",
            type="string",
            description="The search query to find relevant documents",
            required=True
        ),
        ToolParameter(
            name="top_k",
            type="integer",
            description="Number of results to return (default: 5)",
            required=False,
            default=5
        )
    ],
    function=search_documents_tool
)

GET_SOURCES = Tool(
    name="get_sources",
    description="Get list of available document sources and their statistics. Use this when user asks about available data or sources.",
    parameters=[],
    function=get_document_sources_tool
)

CREATE_TASK = Tool(
    name="create_task",
    description="Create a background task for long-running operations. Use this for actions that take time to complete.",
    parameters=[
        ToolParameter(
            name="task_type",
            type="string",
            description="Type of task to create",
            required=True
        ),
        ToolParameter(
            name="data",
            type="object",
            description="Task data",
            required=True
        )
    ],
    function=create_task_tool
)

GET_STATS = Tool(
    name="get_stats",
    description="Get system statistics including database and vector store information. Use this when user asks about system health or data counts.",
    parameters=[],
    function=get_system_stats_tool
)


# Default tool registry
DEFAULT_TOOLS = [
    SEARCH_DOCUMENTS,
    GET_SOURCES,
    CREATE_TASK,
    GET_STATS
]


def get_default_tools() -> List[Tool]:
    """Get default tools for the agent."""
    return DEFAULT_TOOLS.copy()

