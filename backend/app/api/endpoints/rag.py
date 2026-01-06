"""RAG pipeline endpoints."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SourcesResponse,
    DocumentSource,
    DocumentCreate,
    IngestionRequest,
    IngestionResponse,
    ReindexRequest,
    ReindexResponse,
    DocumentResponse
)
from app.services.search_service import search_service
from app.services.ingestion_service import ingestion_service
from app.services.tasks import process_documents, rebuild_index
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    db: AsyncSession = Depends(get_db_session)
) -> SearchResponse:
    """
    Search for similar documents using semantic search.
    
    Returns results with source attribution and similarity scores.
    """
    try:
        logger.info(f"Search request: '{search_request.query}' (top_k={search_request.top_k})")
        
        # Perform search
        results, execution_time = await search_service.search(
            db=db,
            query=search_request.query,
            top_k=search_request.top_k,
            doc_type=search_request.doc_type,
            source=search_request.source
        )
        
        return SearchResponse(
            query=search_request.query,
            results=results,
            total_results=len(results),
            execution_time=execution_time,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/sources", response_model=SourcesResponse)
async def get_sources(
    db: AsyncSession = Depends(get_db_session)
) -> SourcesResponse:
    """
    Get available document sources and statistics.
    
    Returns information about all indexed document sources.
    """
    try:
        logger.info("Fetching document sources")
        
        # Get sources
        sources = await ingestion_service.get_sources(db)
        
        # Get total stats
        stats = await ingestion_service.get_total_stats(db)
        
        # Convert to schema
        source_list = [
            DocumentSource(
                source=s['source'],
                doc_type=s['doc_type'],
                document_count=s['document_count'],
                chunk_count=s['chunk_count']
            )
            for s in sources
        ]
        
        return SourcesResponse(
            sources=source_list,
            total_documents=stats['total_documents'],
            total_chunks=stats['total_chunks'],
            total_sources=stats['total_sources']
        )
        
    except Exception as e:
        logger.error(f"Error fetching sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sources: {str(e)}"
        )


@router.post("/ingest", response_model=IngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_documents(
    ingestion_request: IngestionRequest,
    background_tasks: BackgroundTasks
) -> IngestionResponse:
    """
    Ingest documents for indexing (async).
    
    Documents are processed in the background and indexed for search.
    """
    try:
        logger.info(f"Ingestion request for {len(ingestion_request.documents)} documents")
        
        # Convert to dict for Celery
        documents_data = [doc.dict() for doc in ingestion_request.documents]
        
        # Submit background task
        task = process_documents.apply_async(args=[documents_data])
        
        return IngestionResponse(
            task_id=task.id,
            status="accepted",
            message="Documents submitted for processing",
            document_count=len(ingestion_request.documents)
        )
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/ingest/sync", response_model=List[DocumentResponse])
async def ingest_documents_sync(
    ingestion_request: IngestionRequest,
    db: AsyncSession = Depends(get_db_session)
) -> List[DocumentResponse]:
    """
    Ingest documents synchronously (for small batches).
    
    Processes documents immediately and returns results.
    """
    try:
        logger.info(f"Sync ingestion request for {len(ingestion_request.documents)} documents")
        
        # Ingest documents
        documents = await ingestion_service.ingest_documents(
            db,
            ingestion_request.documents,
            generate_embeddings=True
        )
        
        # Rebuild index
        await ingestion_service.rebuild_vector_index(db)
        
        # Convert to response
        responses = []
        for doc in documents:
            response = DocumentResponse(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                doc_type=doc.doc_type,
                source=doc.source,
                metadata=doc.metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                chunk_count=len(doc.chunks) if doc.chunks else 0
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Sync ingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync ingestion failed: {str(e)}"
        )


@router.post("/reindex", response_model=ReindexResponse, status_code=status.HTTP_202_ACCEPTED)
async def reindex_documents(
    reindex_request: ReindexRequest,
    db: AsyncSession = Depends(get_db_session)
) -> ReindexResponse:
    """
    Rebuild the vector index (async).
    
    Re-indexes all documents or documents of a specific type.
    """
    try:
        logger.info(f"Reindex request: force={reindex_request.force}, doc_type={reindex_request.doc_type}")
        
        # Count documents to process
        stats = await ingestion_service.get_total_stats(db)
        documents_count = stats['total_documents']
        
        # Submit background task
        task = rebuild_index.apply_async(args=[reindex_request.doc_type])
        
        return ReindexResponse(
            task_id=task.id,
            status="accepted",
            message="Re-indexing started",
            documents_to_process=documents_count
        )
        
    except Exception as e:
        logger.error(f"Reindex error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex failed: {str(e)}"
        )


@router.get("/stats")
async def get_rag_stats(
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get RAG pipeline statistics.
    
    Returns statistics about documents, chunks, and the vector index.
    """
    try:
        from app.services.vector_store import vector_store
        
        # Get database stats
        db_stats = await ingestion_service.get_total_stats(db)
        
        # Get vector store stats
        vector_stats = vector_store.get_stats()
        
        return {
            "database": db_stats,
            "vector_store": vector_stats,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )

