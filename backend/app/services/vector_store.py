"""FAISS vector store service."""
import os
import pickle
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import faiss
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for similarity search."""
    
    def __init__(
        self,
        vector_dim: int = 384,
        index_type: str = "Flat",
        storage_path: str = "./data/faiss_index"
    ) -> None:
        """
        Initialize FAISS vector store.
        
        Args:
            vector_dim: Dimension of embedding vectors
            index_type: Type of FAISS index (Flat, IVFFlat, HNSW)
            storage_path: Path to store index files
        """
        self.vector_dim = vector_dim
        self.index_type = index_type
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.index: Optional[faiss.Index] = None
        self.chunk_ids: List[int] = []
        
        logger.info(f"FAISSVectorStore initialized with dim={vector_dim}, type={index_type}")
    
    def create_index(self) -> None:
        """Create a new FAISS index."""
        if self.index_type == "Flat":
            # L2 distance (Euclidean)
            self.index = faiss.IndexFlatL2(self.vector_dim)
        elif self.index_type == "IP":
            # Inner Product (for normalized vectors, equivalent to cosine similarity)
            self.index = faiss.IndexFlatIP(self.vector_dim)
        elif self.index_type == "IVFFlat":
            # Inverted File Index with Flat quantizer (faster but approximate)
            quantizer = faiss.IndexFlatL2(self.vector_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.vector_dim, 100)
        else:
            # Default to Flat L2
            self.index = faiss.IndexFlatL2(self.vector_dim)
        
        self.chunk_ids = []
        logger.info(f"Created new FAISS index: {self.index_type}")
    
    def add_vectors(
        self,
        vectors: np.ndarray,
        chunk_ids: List[int]
    ) -> None:
        """
        Add vectors to the index.
        
        Args:
            vectors: Array of embedding vectors (shape: [n, vector_dim])
            chunk_ids: List of chunk IDs corresponding to vectors
        """
        if self.index is None:
            self.create_index()
        
        if len(vectors) != len(chunk_ids):
            raise ValueError(f"Mismatch between vectors ({len(vectors)}) and chunk_ids ({len(chunk_ids)})")
        
        # Ensure vectors are float32
        vectors = vectors.astype(np.float32)
        
        # Normalize vectors for cosine similarity (if using IP index)
        if self.index_type == "IP":
            faiss.normalize_L2(vectors)
        
        # Train index if needed (for IVF)
        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
            logger.info("Training IVF index...")
            self.index.train(vectors)
        
        # Add vectors to index
        self.index.add(vectors)
        self.chunk_ids.extend(chunk_ids)
        
        logger.info(f"Added {len(vectors)} vectors to index. Total: {self.index.ntotal}")
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (chunk_id, distance/similarity) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty or not initialized")
            return []
        
        # Ensure query is the right shape and type
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        
        # Normalize query for cosine similarity (if using IP index)
        if self.index_type == "IP":
            faiss.normalize_L2(query_vector)
        
        # Search
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # Convert to results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1 and idx < len(self.chunk_ids):
                chunk_id = self.chunk_ids[idx]
                # Convert distance to similarity score (for L2, lower is better; for IP, higher is better)
                if self.index_type == "IP":
                    similarity = float(dist)
                else:
                    # Convert L2 distance to similarity score (0-1 range, 1 is most similar)
                    similarity = 1.0 / (1.0 + float(dist))
                
                results.append((chunk_id, similarity))
        
        logger.debug(f"Found {len(results)} results for query")
        return results
    
    def save_index(self, filename: str = "faiss_index.bin") -> None:
        """
        Save index to disk.
        
        Args:
            filename: Filename for the index
        """
        if self.index is None:
            logger.warning("No index to save")
            return
        
        index_path = self.storage_path / filename
        metadata_path = self.storage_path / f"{filename}.metadata"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_path))
        
        # Save metadata (chunk IDs)
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'chunk_ids': self.chunk_ids,
                'vector_dim': self.vector_dim,
                'index_type': self.index_type
            }, f)
        
        logger.info(f"Saved index to {index_path}")
    
    def load_index(self, filename: str = "faiss_index.bin") -> bool:
        """
        Load index from disk.
        
        Args:
            filename: Filename of the index
            
        Returns:
            True if loaded successfully, False otherwise
        """
        index_path = self.storage_path / filename
        metadata_path = self.storage_path / f"{filename}.metadata"
        
        if not index_path.exists() or not metadata_path.exists():
            logger.warning(f"Index files not found at {index_path}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.chunk_ids = metadata['chunk_ids']
                self.vector_dim = metadata['vector_dim']
                self.index_type = metadata['index_type']
            
            logger.info(f"Loaded index from {index_path} with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def clear_index(self) -> None:
        """Clear the index."""
        self.create_index()
        logger.info("Index cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if self.index is None:
            return {
                'total_vectors': 0,
                'vector_dim': self.vector_dim,
                'index_type': self.index_type,
                'is_trained': False
            }
        
        return {
            'total_vectors': self.index.ntotal,
            'vector_dim': self.vector_dim,
            'index_type': self.index_type,
            'is_trained': self.index.is_trained if hasattr(self.index, 'is_trained') else True,
            'chunk_ids_count': len(self.chunk_ids)
        }


# Global vector store instance
vector_store = FAISSVectorStore()

