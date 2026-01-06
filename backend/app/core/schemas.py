"""Pydantic schemas for API requests/responses."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Document schemas
class DocumentBase(BaseModel):
    """Base document schema."""
    
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    doc_type: str = Field(..., description="Document type (plain_text, jira_ticket, slack_message)")
    source: Optional[str] = Field(None, description="Document source/origin")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Schema for document chunk response."""
    
    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


# Search schemas
class SearchRequest(BaseModel):
    """Schema for search request."""
    
    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=100)
    doc_type: Optional[str] = Field(None, description="Filter by document type")
    source: Optional[str] = Field(None, description="Filter by document source")


class SearchResult(BaseModel):
    """Schema for individual search result."""
    
    chunk_id: int
    document_id: int
    document_title: str
    document_type: str
    document_source: Optional[str]
    chunk_content: str
    chunk_index: int
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Schema for search response."""
    
    query: str
    results: List[SearchResult]
    total_results: int
    execution_time: float
    timestamp: datetime


# Source schemas
class DocumentSource(BaseModel):
    """Schema for document source."""
    
    source: str
    doc_type: str
    document_count: int
    chunk_count: int


class SourcesResponse(BaseModel):
    """Schema for sources response."""
    
    sources: List[DocumentSource]
    total_documents: int
    total_chunks: int
    total_sources: int


# Ingestion schemas
class IngestionRequest(BaseModel):
    """Schema for document ingestion request."""
    
    documents: List[DocumentCreate]


class IngestionResponse(BaseModel):
    """Schema for ingestion response."""
    
    task_id: str
    status: str
    message: str
    document_count: int


# Re-indexing schemas
class ReindexRequest(BaseModel):
    """Schema for re-indexing request."""
    
    force: bool = Field(False, description="Force re-indexing of all documents")
    doc_type: Optional[str] = Field(None, description="Re-index specific document type")


class ReindexResponse(BaseModel):
    """Schema for re-index response."""
    
    task_id: str
    status: str
    message: str
    documents_to_process: int

