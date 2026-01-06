# RAG Pipeline Documentation

## Overview

The RAG (Retrieval-Augmented Generation) pipeline enables semantic search over ingested documents using vector embeddings and FAISS indexing.

## Architecture

### Components

1. **Document Ingestion** - Process and store documents
2. **Text Chunking** - Split documents into manageable chunks
3. **Embedding Generation** - Create vector embeddings using sentence-transformers
4. **FAISS Indexing** - Build and maintain vector index for similarity search
5. **Semantic Search** - Query documents using natural language

### Data Flow

```
Document → Chunking → Embedding → FAISS Index → Search
```

## Supported Document Types

### 1. Plain Text Documents
```python
{
    "title": "Document Title",
    "content": "Full document text...",
    "doc_type": "plain_text",
    "source": "file_path.txt",
    "metadata": {"author": "John Doe"}
}
```

### 2. Jira-style Tickets
```python
{
    "title": "JIRA-123: Bug in authentication",
    "content": "Description: Users cannot log in...",
    "doc_type": "jira_ticket",
    "source": "JIRA",
    "metadata": {
        "ticket_id": "JIRA-123",
        "status": "Open",
        "priority": "High"
    }
}
```

### 3. Slack Messages
```python
{
    "title": "Slack Thread: Product Discussion",
    "content": "Message content from Slack...",
    "doc_type": "slack_message",
    "source": "#product-channel",
    "metadata": {
        "channel": "product",
        "timestamp": "2024-01-06T12:00:00Z",
        "user": "jane_doe"
    }
}
```

## API Endpoints

### 1. Search Documents

**POST /api/v1/rag/search**

Search for similar documents using semantic search.

**Request:**
```json
{
    "query": "How do I reset my password?",
    "top_k": 5,
    "doc_type": "jira_ticket",
    "source": "JIRA"
}
```

**Response:**
```json
{
    "query": "How do I reset my password?",
    "results": [
        {
            "chunk_id": 123,
            "document_id": 45,
            "document_title": "JIRA-456: Password Reset Issue",
            "document_type": "jira_ticket",
            "document_source": "JIRA",
            "chunk_content": "To reset password, go to settings...",
            "chunk_index": 0,
            "similarity_score": 0.92,
            "metadata": {
                "token_count": 120,
                "chunk_metadata": {...},
                "document_metadata": {...}
            }
        }
    ],
    "total_results": 5,
    "execution_time": 0.234,
    "timestamp": "2024-01-06T12:00:00Z"
}
```

### 2. Get Sources

**GET /api/v1/rag/sources**

Get available document sources and statistics.

**Response:**
```json
{
    "sources": [
        {
            "source": "JIRA",
            "doc_type": "jira_ticket",
            "document_count": 150,
            "chunk_count": 456
        },
        {
            "source": "#engineering",
            "doc_type": "slack_message",
            "document_count": 320,
            "chunk_count": 890
        }
    ],
    "total_documents": 500,
    "total_chunks": 1500,
    "total_sources": 5
}
```

### 3. Ingest Documents (Async)

**POST /api/v1/rag/ingest**

Submit documents for background processing.

**Request:**
```json
{
    "documents": [
        {
            "title": "User Guide",
            "content": "Complete user guide content...",
            "doc_type": "plain_text",
            "source": "docs/user_guide.txt",
            "metadata": {"version": "1.0"}
        }
    ]
}
```

**Response:**
```json
{
    "task_id": "abc-123-def",
    "status": "accepted",
    "message": "Documents submitted for processing",
    "document_count": 1
}
```

### 4. Ingest Documents (Sync)

**POST /api/v1/rag/ingest/sync**

Process documents immediately (for small batches).

**Request:** Same as async ingestion

**Response:**
```json
[
    {
        "id": 123,
        "title": "User Guide",
        "content": "Complete user guide content...",
        "doc_type": "plain_text",
        "source": "docs/user_guide.txt",
        "metadata": {"version": "1.0"},
        "created_at": "2024-01-06T12:00:00Z",
        "updated_at": "2024-01-06T12:00:00Z",
        "chunk_count": 8
    }
]
```

### 5. Rebuild Index

**POST /api/v1/rag/reindex**

Rebuild the FAISS vector index.

**Request:**
```json
{
    "force": true,
    "doc_type": "jira_ticket"
}
```

**Response:**
```json
{
    "task_id": "xyz-789-abc",
    "status": "accepted",
    "message": "Re-indexing started",
    "documents_to_process": 150
}
```

### 6. Get Statistics

**GET /api/v1/rag/stats**

Get RAG pipeline statistics.

**Response:**
```json
{
    "database": {
        "total_documents": 500,
        "total_chunks": 1500,
        "total_sources": 5
    },
    "vector_store": {
        "total_vectors": 1500,
        "vector_dim": 384,
        "index_type": "Flat",
        "is_trained": true
    },
    "status": "operational"
}
```

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/rag"

# 1. Ingest documents
documents = {
    "documents": [
        {
            "title": "API Documentation",
            "content": "This is the API documentation...",
            "doc_type": "plain_text",
            "source": "docs/api.txt"
        }
    ]
}

response = requests.post(f"{BASE_URL}/ingest", json=documents)
print(f"Task ID: {response.json()['task_id']}")

# 2. Search documents
search_query = {
    "query": "How do I authenticate?",
    "top_k": 5
}

response = requests.post(f"{BASE_URL}/search", json=search_query)
results = response.json()

for result in results['results']:
    print(f"Score: {result['similarity_score']:.3f}")
    print(f"Title: {result['document_title']}")
    print(f"Content: {result['chunk_content'][:100]}...")
    print(f"Source: {result['document_source']}")
    print("---")

# 3. Get sources
response = requests.get(f"{BASE_URL}/sources")
sources = response.json()
print(f"Total Documents: {sources['total_documents']}")
```

### cURL Examples

```bash
# Search
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "password reset",
    "top_k": 5
  }'

# Get sources
curl http://localhost:8000/api/v1/rag/sources

# Ingest document
curl -X POST http://localhost:8000/api/v1/rag/ingest/sync \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [{
      "title": "Test Doc",
      "content": "This is a test document",
      "doc_type": "plain_text",
      "source": "test.txt"
    }]
  }'
```

## Configuration

### Chunking Parameters

Configure in `app/services/chunking_service.py`:

```python
ChunkingService(
    chunk_size=512,      # Tokens per chunk
    chunk_overlap=50     # Overlap between chunks
)
```

### Embedding Model

Configure in `app/services/embedding_service.py`:

```python
EmbeddingService(
    model_name="all-MiniLM-L6-v2",  # Sentence-transformers model
    device="cpu"                     # cpu, cuda, or mps
)
```

### FAISS Index Type

Configure in `app/services/vector_store.py`:

```python
FAISSVectorStore(
    vector_dim=384,        # Embedding dimension
    index_type="Flat"      # Flat, IP, or IVFFlat
)
```

## Performance Considerations

### Chunking Strategy

- **chunk_size**: Balance between context and granularity
  - Smaller chunks (256-512): More precise matching
  - Larger chunks (512-1024): More context per result

- **chunk_overlap**: Prevents information loss at boundaries
  - Recommended: 10-20% of chunk_size

### Embedding Model Selection

| Model | Dimension | Speed | Quality |
|-------|-----------|-------|---------|
| all-MiniLM-L6-v2 | 384 | Fast | Good |
| all-mpnet-base-v2 | 768 | Medium | Better |
| multi-qa-mpnet-base-dot-v1 | 768 | Medium | Best for QA |

### Index Types

- **Flat**: Exact search, slower, best for <100K vectors
- **IP**: Inner product, use with normalized vectors
- **IVFFlat**: Approximate search, faster, best for >100K vectors

## Monitoring

### Health Checks

```bash
# Check if index is loaded
curl http://localhost:8000/api/v1/rag/stats

# View Celery tasks (for async operations)
open http://localhost:5555
```

### Logs

```bash
# View RAG-related logs
docker-compose logs -f api | grep -i "rag\|search\|embedding"
```

## Best Practices

### 1. Document Preparation

- Clean and normalize text before ingestion
- Include rich metadata for filtering
- Use consistent naming for sources

### 2. Chunking

- Adjust chunk size based on document type
- Use sentence-based chunking for better coherence
- Include overlap to preserve context

### 3. Search

- Use filters (doc_type, source) to narrow results
- Set appropriate top_k based on use case
- Consider hybrid search for better recall

### 4. Re-indexing

- Re-index after bulk ingestion
- Schedule periodic re-indexing
- Use doc_type filter for partial re-indexing

## Troubleshooting

### No Search Results

1. Check if documents are ingested:
   ```bash
   curl http://localhost:8000/api/v1/rag/sources
   ```

2. Verify index is built:
   ```bash
   curl http://localhost:8000/api/v1/rag/stats
   ```

3. Re-index if needed:
   ```bash
   curl -X POST http://localhost:8000/api/v1/rag/reindex \
     -H "Content-Type: application/json" \
     -d '{"force": true}'
   ```

### Slow Search

- Reduce top_k
- Use IVFFlat index for large datasets
- Add filters (doc_type, source)
- Consider caching frequent queries

### High Memory Usage

- Use smaller embedding model
- Reduce chunk_size
- Implement batch processing for large ingestions

## Advanced Features

### Hybrid Search

Combine semantic and keyword search:

```python
# Not exposed via API yet, but available in search_service
results = await search_service.hybrid_search(
    db=db,
    query="password reset",
    keyword_weight=0.3,
    semantic_weight=0.7
)
```

### Context Retrieval

Get surrounding chunks for better context:

```python
chunks = await search_service.get_chunk_context(
    db=db,
    chunk_id=123,
    context_size=2  # 2 chunks before and after
)
```

## Future Enhancements

- [ ] PostgreSQL pgvector extension for native vector storage
- [ ] Document update and versioning
- [ ] Multi-modal embeddings (text + images)
- [ ] Query expansion and re-ranking
- [ ] Federated search across multiple indexes
- [ ] Real-time ingestion via webhooks
- [ ] Advanced filters and faceting
- [ ] A/B testing for different embedding models

## References

- [Sentence Transformers](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [RAG Best Practices](https://www.pinecone.io/learn/retrieval-augmented-generation/)

