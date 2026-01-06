"""Search service for RAG pipeline."""
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.document import Document, DocumentChunk, ChunkEmbedding, SearchQuery
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.core.logging import get_logger
from app.core.schemas import SearchResult

logger = get_logger(__name__)


class SearchService:
    """Service for semantic search."""
    
    def __init__(self) -> None:
        """Initialize search service."""
        logger.info("SearchService initialized")
    
    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        source: Optional[str] = None
    ) -> tuple[List[SearchResult], float]:
        """
        Perform semantic search.
        
        Args:
            db: Database session
            query: Search query text
            top_k: Number of results to return
            doc_type: Optional filter by document type
            source: Optional filter by source
            
        Returns:
            Tuple of (search results, execution time)
        """
        start_time = time.time()
        logger.info(f"Searching for: '{query[:50]}...' (top_k={top_k})")
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Search vector store
        vector_results = vector_store.search(query_embedding, top_k=top_k * 2)  # Get more for filtering
        
        if not vector_results:
            logger.warning("No results found in vector store")
            execution_time = time.time() - start_time
            return [], execution_time
        
        # Extract chunk IDs
        chunk_ids = [chunk_id for chunk_id, _ in vector_results]
        
        # Fetch chunk details from database
        query_chunks = select(
            DocumentChunk,
            Document,
            ChunkEmbedding
        ).join(
            Document, DocumentChunk.document_id == Document.id
        ).join(
            ChunkEmbedding, DocumentChunk.id == ChunkEmbedding.chunk_id
        ).where(
            DocumentChunk.id.in_(chunk_ids)
        )
        
        # Apply filters
        if doc_type:
            query_chunks = query_chunks.where(Document.doc_type == doc_type)
        if source:
            query_chunks = query_chunks.where(Document.source == source)
        
        result = await db.execute(query_chunks)
        chunks_data = result.all()
        
        # Create mapping of chunk_id to data
        chunk_map = {
            chunk.id: (chunk, document, embedding)
            for chunk, document, embedding in chunks_data
        }
        
        # Build search results with scores
        search_results = []
        for chunk_id, similarity_score in vector_results:
            if chunk_id in chunk_map:
                chunk, document, embedding = chunk_map[chunk_id]
                
                search_result = SearchResult(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    document_type=document.doc_type,
                    document_source=document.source,
                    chunk_content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    similarity_score=similarity_score,
                    metadata={
                        'token_count': chunk.token_count,
                        'chunk_metadata': chunk.metadata,
                        'document_metadata': document.metadata
                    }
                )
                
                search_results.append(search_result)
                
                if len(search_results) >= top_k:
                    break
        
        execution_time = time.time() - start_time
        
        # Log search query
        search_query = SearchQuery(
            query_text=query,
            top_k=top_k,
            results_count=len(search_results),
            execution_time=execution_time,
            metadata={
                'doc_type_filter': doc_type,
                'source_filter': source
            }
        )
        db.add(search_query)
        await db.commit()
        
        logger.info(f"Search completed in {execution_time:.3f}s with {len(search_results)} results")
        return search_results, execution_time
    
    async def get_chunk_context(
        self,
        db: AsyncSession,
        chunk_id: int,
        context_size: int = 2
    ) -> List[DocumentChunk]:
        """
        Get context chunks around a specific chunk.
        
        Args:
            db: Database session
            chunk_id: Target chunk ID
            context_size: Number of chunks before and after
            
        Returns:
            List of chunks including context
        """
        # Get target chunk
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        target_chunk = result.scalar_one_or_none()
        
        if not target_chunk:
            return []
        
        # Get surrounding chunks
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == target_chunk.document_id,
            DocumentChunk.chunk_index >= target_chunk.chunk_index - context_size,
            DocumentChunk.chunk_index <= target_chunk.chunk_index + context_size
        ).order_by(DocumentChunk.chunk_index)
        
        result = await db.execute(query)
        chunks = result.scalars().all()
        
        return list(chunks)
    
    async def get_document_chunks(
        self,
        db: AsyncSession,
        document_id: int
    ) -> List[DocumentChunk]:
        """
        Get all chunks for a document.
        
        Args:
            db: Database session
            document_id: Document ID
            
        Returns:
            List of chunks
        """
        query = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword search.
        
        Args:
            db: Database session
            query: Search query
            top_k: Number of results
            keyword_weight: Weight for keyword search (0-1)
            semantic_weight: Weight for semantic search (0-1)
            
        Returns:
            List of search results
        """
        # Normalize weights
        total_weight = keyword_weight + semantic_weight
        keyword_weight /= total_weight
        semantic_weight /= total_weight
        
        # Perform semantic search
        semantic_results, _ = await self.search(db, query, top_k=top_k * 2)
        
        # Simple keyword search (can be improved with full-text search)
        query_lower = query.lower()
        keyword_query = select(
            DocumentChunk, Document
        ).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.content.ilike(f'%{query_lower}%')
        ).limit(top_k * 2)
        
        result = await db.execute(keyword_query)
        keyword_chunks = result.all()
        
        # Combine and re-rank results
        combined_scores: Dict[int, float] = {}
        
        # Add semantic scores
        for i, result in enumerate(semantic_results):
            score = result.similarity_score * semantic_weight
            combined_scores[result.chunk_id] = score
        
        # Add keyword scores (simple position-based scoring)
        for i, (chunk, document) in enumerate(keyword_chunks):
            keyword_score = (1.0 - i / len(keyword_chunks)) * keyword_weight
            if chunk.id in combined_scores:
                combined_scores[chunk.id] += keyword_score
            else:
                combined_scores[chunk.id] = keyword_score
        
        # Sort by combined score
        sorted_chunk_ids = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Fetch full details for top results
        final_chunk_ids = [chunk_id for chunk_id, _ in sorted_chunk_ids]
        
        query_final = select(
            DocumentChunk, Document
        ).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.id.in_(final_chunk_ids)
        )
        
        result = await db.execute(query_final)
        final_chunks = result.all()
        
        # Build final results
        chunk_data_map = {chunk.id: (chunk, document) for chunk, document in final_chunks}
        
        hybrid_results = []
        for chunk_id, score in sorted_chunk_ids:
            if chunk_id in chunk_data_map:
                chunk, document = chunk_data_map[chunk_id]
                
                search_result = SearchResult(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    document_title=document.title,
                    document_type=document.doc_type,
                    document_source=document.source,
                    chunk_content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    similarity_score=score,
                    metadata={
                        'token_count': chunk.token_count,
                        'chunk_metadata': chunk.metadata,
                        'search_type': 'hybrid'
                    }
                )
                
                hybrid_results.append(search_result)
        
        logger.info(f"Hybrid search returned {len(hybrid_results)} results")
        return hybrid_results


# Global search service instance
search_service = SearchService()

