"""Text chunking service."""
import tiktoken
from typing import List, Dict, Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChunkingService:
    """Service for chunking text documents."""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base"
    ) -> None:
        """Initialize chunking service."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        logger.info(f"ChunkingService initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces with overlap.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to include with each chunk
            
        Returns:
            List of chunk dictionaries with content, token_count, and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        logger.debug(f"Chunking text with {total_tokens} tokens")
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < total_tokens:
            # Get chunk end position
            end = min(start + self.chunk_size, total_tokens)
            
            # Extract chunk tokens
            chunk_tokens = tokens[start:end]
            
            # Decode chunk
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # Create chunk metadata
            chunk_metadata = {
                "token_count": len(chunk_tokens),
                "start_token": start,
                "end_token": end,
                "chunk_index": chunk_index,
            }
            
            # Add original metadata
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "content": chunk_text,
                "token_count": len(chunk_tokens),
                "chunk_index": chunk_index,
                "metadata": chunk_metadata
            })
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            chunk_index += 1
            
            # Prevent infinite loop
            if start >= total_tokens or (end == total_tokens and start + self.chunk_overlap >= total_tokens):
                break
        
        logger.info(f"Created {len(chunks)} chunks from {total_tokens} tokens")
        return chunks
    
    def chunk_by_sentences(
        self,
        text: str,
        max_tokens: int = 512,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text by sentences, respecting token limits.
        
        Args:
            text: Text to chunk
            max_tokens: Maximum tokens per chunk
            metadata: Optional metadata
            
        Returns:
            List of chunk dictionaries
        """
        # Simple sentence splitting (can be improved with spaCy/nltk)
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_text = '. '.join(current_chunk) + '.'
                chunk_metadata = {
                    "token_count": current_tokens,
                    "chunk_index": chunk_index,
                    "sentence_count": len(current_chunk)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "content": chunk_text,
                    "token_count": current_tokens,
                    "chunk_index": chunk_index,
                    "metadata": chunk_metadata
                })
                
                # Start new chunk
                current_chunk = [sentence]
                current_tokens = sentence_tokens
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunk_metadata = {
                "token_count": current_tokens,
                "chunk_index": chunk_index,
                "sentence_count": len(current_chunk)
            }
            if metadata:
                chunk_metadata.update(metadata)
            
            chunks.append({
                "content": chunk_text,
                "token_count": current_tokens,
                "chunk_index": chunk_index,
                "metadata": chunk_metadata
            })
        
        logger.info(f"Created {len(chunks)} sentence-based chunks")
        return chunks


# Global chunking service instance
chunking_service = ChunkingService()

