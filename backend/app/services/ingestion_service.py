"""Document ingestion service."""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
import numpy as np

from app.models.document import Document, DocumentChunk, ChunkEmbedding, DocumentType
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.core.logging import get_logger
from app.core.schemas import DocumentCreate

logger = get_logger(__name__)


class IngestionService:
    """Service for ingesting and processing documents."""
    
    def __init__(self) -> None:
        """Initialize ingestion service."""
        logger.info("IngestionService initialized")
    
    async def ingest_document(
        self,
        db: AsyncSession,
        document_data: DocumentCreate,
        generate_embeddings: bool = True
    ) -> Document:
        """
        Ingest a single document.
        
        Args:
            db: Database session
            document_data: Document data
            generate_embeddings: Whether to generate embeddings immediately
            
        Returns:
            Created document
        """
        logger.info(f"Ingesting document: {document_data.title}")
        
        # Create document
        document = Document(
            title=document_data.title,
            content=document_data.content,
            doc_type=document_data.doc_type,
            source=document_data.source,
            metadata=document_data.metadata
        )
        db.add(document)
        await db.flush()
        
        # Chunk document
        chunks = chunking_service.chunk_text(
            document_data.content,
            metadata={
                'doc_type': document_data.doc_type,
                'source': document_data.source,
                'title': document_data.title
            }
        )
        
        logger.info(f"Created {len(chunks)} chunks for document {document.id}")
        
        # Create chunk records
        chunk_models = []
        for chunk_data in chunks:
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_data['chunk_index'],
                content=chunk_data['content'],
                token_count=chunk_data['token_count'],
                metadata=chunk_data['metadata']
            )
            db.add(chunk)
            chunk_models.append(chunk)
        
        await db.flush()
        
        # Generate embeddings if requested
        if generate_embeddings:
            await self.generate_embeddings_for_chunks(db, chunk_models)
        
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"Successfully ingested document {document.id}")
        return document
    
    async def ingest_documents(
        self,
        db: AsyncSession,
        documents_data: List[DocumentCreate],
        generate_embeddings: bool = True
    ) -> List[Document]:
        """
        Ingest multiple documents.
        
        Args:
            db: Database session
            documents_data: List of document data
            generate_embeddings: Whether to generate embeddings
            
        Returns:
            List of created documents
        """
        logger.info(f"Ingesting {len(documents_data)} documents")
        
        documents = []
        for doc_data in documents_data:
            try:
                document = await self.ingest_document(db, doc_data, generate_embeddings)
                documents.append(document)
            except Exception as e:
                logger.error(f"Error ingesting document '{doc_data.title}': {e}")
                await db.rollback()
                raise
        
        logger.info(f"Successfully ingested {len(documents)} documents")
        return documents
    
    async def generate_embeddings_for_chunks(
        self,
        db: AsyncSession,
        chunks: List[DocumentChunk]
    ) -> None:
        """
        Generate embeddings for document chunks.
        
        Args:
            db: Database session
            chunks: List of document chunks
        """
        if not chunks:
            return
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract chunk texts
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings(texts)
        vector_dim = embedding_service.get_vector_dimension()
        
        # Store embeddings in database
        for chunk, embedding_vector in zip(chunks, embeddings):
            embedding = ChunkEmbedding(
                chunk_id=chunk.id,
                embedding_model=embedding_service.model_name,
                vector_dim=vector_dim,
                embedding_vector=embedding_vector.tolist()
            )
            db.add(embedding)
        
        await db.flush()
        logger.info(f"Stored {len(chunks)} embeddings in database")
    
    async def rebuild_vector_index(
        self,
        db: AsyncSession,
        doc_type: Optional[str] = None
    ) -> int:
        """
        Rebuild FAISS vector index from database.
        
        Args:
            db: Database session
            doc_type: Optional filter by document type
            
        Returns:
            Number of vectors indexed
        """
        logger.info("Rebuilding vector index...")
        
        # Build query
        query = select(ChunkEmbedding).join(DocumentChunk).join(Document)
        
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        
        # Fetch all embeddings
        result = await db.execute(query)
        embeddings_data = result.scalars().all()
        
        if not embeddings_data:
            logger.warning("No embeddings found to index")
            return 0
        
        logger.info(f"Found {len(embeddings_data)} embeddings to index")
        
        # Clear existing index
        vector_store.clear_index()
        
        # Prepare vectors and chunk IDs
        vectors = np.array([emb.embedding_vector for emb in embeddings_data], dtype=np.float32)
        chunk_ids = [emb.chunk_id for emb in embeddings_data]
        
        # Add to vector store
        vector_store.add_vectors(vectors, chunk_ids)
        
        # Save index
        vector_store.save_index()
        
        logger.info(f"Successfully rebuilt index with {len(vectors)} vectors")
        return len(vectors)
    
    async def get_sources(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get available document sources.
        
        Args:
            db: Database session
            
        Returns:
            List of source information
        """
        # Query for sources with counts
        query = select(
            Document.source,
            Document.doc_type,
            func.count(distinct(Document.id)).label('document_count'),
            func.count(DocumentChunk.id).label('chunk_count')
        ).join(
            DocumentChunk, Document.id == DocumentChunk.document_id, isouter=True
        ).group_by(
            Document.source,
            Document.doc_type
        )
        
        result = await db.execute(query)
        sources_data = result.all()
        
        sources = []
        for row in sources_data:
            sources.append({
                'source': row.source or 'unknown',
                'doc_type': row.doc_type,
                'document_count': row.document_count,
                'chunk_count': row.chunk_count or 0
            })
        
        return sources
    
    async def get_total_stats(
        self,
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Get total statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with total counts
        """
        # Count documents
        doc_result = await db.execute(select(func.count(Document.id)))
        total_documents = doc_result.scalar() or 0
        
        # Count chunks
        chunk_result = await db.execute(select(func.count(DocumentChunk.id)))
        total_chunks = chunk_result.scalar() or 0
        
        # Count distinct sources
        source_result = await db.execute(select(func.count(distinct(Document.source))))
        total_sources = source_result.scalar() or 0
        
        return {
            'total_documents': total_documents,
            'total_chunks': total_chunks,
            'total_sources': total_sources
        }


# Global ingestion service instance
ingestion_service = IngestionService()

