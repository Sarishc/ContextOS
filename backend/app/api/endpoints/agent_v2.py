"""
Enhanced AI Agent API endpoints with frontend-compatible responses.

This module provides a wrapper around the agent endpoints to ensure
responses match the frontend TypeScript interface exactly.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Frontend-compatible models
class FrontendSource(BaseModel):
    """Source model matching frontend TypeScript interface."""
    document_id: str
    title: str
    content: str
    chunk_id: str = Field(default="")
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FrontendToolCall(BaseModel):
    """Tool call model matching frontend TypeScript interface."""
    name: str
    args: Dict[str, Any]
    result: Any


class FrontendAgentResponse(BaseModel):
    """Agent response model matching frontend TypeScript interface."""
    response: str
    sources: Optional[List[FrontendSource]] = None
    tool_calls: Optional[List[FrontendToolCall]] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None


class AgentQueryRequest(BaseModel):
    """Agent query request."""
    query: str = Field(..., description="User query", min_length=1)
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


@router.post("/query", response_model=FrontendAgentResponse)
async def query_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db_session)
) -> FrontendAgentResponse:
    """
    Query the AI agent with frontend-compatible response format.
    
    This endpoint wraps the Gemini agent and transforms the response
    to match the frontend TypeScript interface exactly.
    
    Frontend expects:
    - response: string (the agent's answer)
    - sources: array of Source objects (RAG context)
    - tool_calls: array of ToolCall objects (actions taken)
    - tokens_used: number (total tokens)
    - cost: number (estimated cost in USD)
    - latency_ms: number (total latency)
    """
    try:
        from app.services.gemini_agent import gemini_agent
        from app.services.search_service import search_service
        from app.core.cache import query_cache
        from app.core.observability import tracer
        from app.core.metrics import metrics_collector
        import time
        
        start_time = time.time()
        
        logger.info(f"Agent query: '{request.query[:50]}...'")
        
        # Check cache first
        cache_key_params = {
            "top_k": 5,
            "history_count": len(request.conversation_history)
        }
        cached_response = query_cache.get(request.query, **cache_key_params)
        
        if cached_response:
            logger.info("Returning cached response")
            tracer.mark_cache_hit()
            return FrontendAgentResponse(**cached_response)
        
        # Step 1: Retrieve RAG context
        rag_span = tracer.add_span("rag_search")
        rag_results, search_time = await search_service.search(
            db=db,
            query=request.query,
            top_k=5
        )
        rag_span.end()
        metrics_collector.record_rag_search(success=True)
        
        # Transform RAG results to frontend Source format
        sources = [
            FrontendSource(
                document_id=r.document_id or f"doc-{i}",
                title=r.document_title or "Untitled",
                content=r.chunk_content or "",
                chunk_id=r.chunk_id or f"chunk-{i}",
                score=float(r.similarity_score or 0.0),
                metadata={
                    "source": r.document_source,
                    "type": r.document_type,
                    "chunk_index": i
                }
            )
            for i, r in enumerate(rag_results)
        ]
        
        # Convert RAG results to context format for Gemini
        rag_context = [
            {
                "title": r.document_title,
                "content": r.chunk_content,
                "source": r.document_source,
                "score": r.similarity_score,
                "doc_type": r.document_type
            }
            for r in rag_results
        ]
        
        logger.info(f"Retrieved {len(rag_context)} RAG results in {search_time:.3f}s")
        
        # Step 2: Query Gemini agent
        gemini_span = tracer.add_span("gemini_query", {"context_count": len(rag_context)})
        
        response = await gemini_agent.query(
            user_query=request.query,
            rag_context=rag_context,
            conversation_history=request.conversation_history
        )
        
        gemini_span.end()
        
        # Step 3: Transform to frontend format
        token_usage = response.get("token_usage", {})
        total_tokens = (
            token_usage.get("total_input_tokens", 0) + 
            token_usage.get("total_output_tokens", 0)
        )
        
        # Calculate cost (Gemini Pro pricing)
        estimated_cost = (
            token_usage.get("total_input_tokens", 0) * 0.00025 / 1000 +  # $0.00025 per 1K input
            token_usage.get("total_output_tokens", 0) * 0.0005 / 1000    # $0.0005 per 1K output
        )
        
        # Transform tool calls to frontend format
        tool_calls = []
        for tc in response.get("tool_calls", []):
            tool_calls.append(
                FrontendToolCall(
                    name=tc.get("tool", tc.get("name", "unknown")),
                    args=tc.get("args", {}),
                    result=tc.get("result", {})
                )
            )
            
            # Record tool call metric
            metrics_collector.record_tool_call(
                tool_name=tc.get("tool", "unknown"),
                success=tc.get("success", True)
            )
        
        # Calculate total latency
        total_latency_ms = (time.time() - start_time) * 1000
        
        # Add token usage to trace
        if token_usage:
            tracer.add_token_usage(
                input_tokens=token_usage.get("total_input_tokens", 0),
                output_tokens=token_usage.get("total_output_tokens", 0)
            )
        
        # Build frontend response
        frontend_response = FrontendAgentResponse(
            response=response.get("response", "No response generated"),
            sources=sources if sources else None,
            tool_calls=tool_calls if tool_calls else None,
            tokens_used=total_tokens if total_tokens > 0 else None,
            cost=estimated_cost if estimated_cost > 0 else None,
            latency_ms=total_latency_ms
        )
        
        # Cache the response
        query_cache.set(request.query, frontend_response.dict(), **cache_key_params)
        
        logger.info(f"Agent query complete: {total_tokens} tokens, {total_latency_ms:.0f}ms")
        
        return frontend_response
        
    except Exception as e:
        logger.error(f"Agent query error: {e}", exc_info=True)
        metrics_collector.record_rag_search(success=False)
        
        # Check if it's an API key issue
        if "API_KEY" in str(e).upper() or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service not configured. Please set GEMINI_API_KEY in environment."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )


@router.get("/health")
async def agent_health() -> Dict[str, Any]:
    """
    Check agent health status.
    
    Validates that all required services are configured and available.
    """
    from app.core.config import settings
    
    # Check if Gemini API key is configured
    api_key_configured = bool(
        settings.GEMINI_API_KEY and 
        settings.GEMINI_API_KEY != "your-gemini-api-key"
    )
    
    health_status = {
        "status": "healthy" if api_key_configured else "degraded",
        "agent_ready": api_key_configured,
        "gemini_configured": api_key_configured,
        "model": settings.GEMINI_MODEL,
        "issues": []
    }
    
    if not api_key_configured:
        health_status["issues"].append(
            "GEMINI_API_KEY not configured. Set it in .env or environment variables."
        )
    
    return health_status

