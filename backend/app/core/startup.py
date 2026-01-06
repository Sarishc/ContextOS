"""Startup initialization for RAG pipeline."""
from app.core.logging import get_logger
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logger = get_logger(__name__)


async def initialize_rag_services() -> None:
    """Initialize RAG services on startup."""
    logger.info("Initializing RAG services...")
    
    try:
        # Load embedding model
        logger.info("Loading embedding model...")
        embedding_service.load_model()
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_dim = embedding_service.get_vector_dimension()
        vector_store.vector_dim = vector_dim
        
        # Try to load existing index
        if vector_store.load_index():
            logger.info("Loaded existing FAISS index")
        else:
            logger.info("No existing index found, will create new one on first ingestion")
            vector_store.create_index()
        
        logger.info("RAG services initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing RAG services: {e}")
        raise


async def shutdown_rag_services() -> None:
    """Cleanup RAG services on shutdown."""
    logger.info("Shutting down RAG services...")
    
    try:
        # Save vector store index
        if vector_store.index is not None:
            logger.info("Saving FAISS index...")
            vector_store.save_index()
        
        logger.info("RAG services shut down successfully")
        
    except Exception as e:
        logger.error(f"Error shutting down RAG services: {e}")

