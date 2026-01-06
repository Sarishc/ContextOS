"""Embedding generation service."""
import asyncio
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu"
    ) -> None:
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use (cpu, cuda, mps)
        """
        self.model_name = model_name
        self.device = device
        self.model: Optional[SentenceTransformer] = None
        self.vector_dim: Optional[int] = None
        logger.info(f"EmbeddingService initialized with model={model_name}, device={device}")
    
    def load_model(self) -> None:
        """Load the embedding model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            # Get vector dimension
            self.vector_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Vector dimension: {self.vector_dim}")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            self.load_model()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            self.model.encode,
            text
        )
        
        return embedding
    
    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            show_progress: Show progress bar
            
        Returns:
            Array of embeddings
        """
        if not self.model:
            self.load_model()
        
        if not texts:
            logger.warning("Empty text list provided for embedding generation")
            return np.array([])
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
        )
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def get_vector_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        if not self.model:
            self.load_model()
        return self.vector_dim
    
    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
embedding_service = EmbeddingService()

