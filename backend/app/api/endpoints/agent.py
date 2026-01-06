"""AI Agent API endpoints."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.services.agent.rag_agent import rag_agent
from app.services.agent.base import AgentContext, AgentResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class Message(BaseModel):
    """Chat message."""
    
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")


class AgentQueryRequest(BaseModel):
    """Agent query request."""
    
    query: str = Field(..., description="User query", min_length=1)
    conversation_history: List[Message] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class AgentQueryResponse(BaseModel):
    """Agent query response."""
    
    response: str
    action_taken: str
    reasoning: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    context_used: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    """Tool information."""
    
    name: str
    description: str
    parameters: Dict[str, Any]


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db_session)
) -> AgentQueryResponse:
    """
    Query the Gemini-powered AI agent with RAG context.
    
    Flow:
    1. Check cache for repeated queries
    2. Retrieve RAG context from knowledge base
    3. Send to Gemini agent with context
    4. Agent calls tools if needed
    5. Cache and return response with sources
    
    Features:
    - Request tracing
    - Token usage tracking
    - Cost estimation
    - Query caching
    - Latency logging
    
    The agent has access to:
    - Knowledge base search
    - Jira ticket management
    - Slack message search
    - Safe SQL execution
    """
    try:
        from app.services.gemini_agent import gemini_agent
        from app.services.gemini_tools import register_all_tools
        from app.services.search_service import search_service
        from app.core.cache import query_cache
        from app.core.observability import tracer
        from app.core.metrics import metrics_collector
        
        logger.info(f"Gemini agent query: '{request.query[:50]}...'")
        
        # Check cache first
        cache_key_params = {
            "top_k": 5,
            "history_count": len(request.conversation_history)
        }
        cached_response = query_cache.get(request.query, **cache_key_params)
        
        if cached_response:
            logger.info("Returning cached response")
            tracer.mark_cache_hit()
            return AgentQueryResponse(**cached_response)
        
        # Start RAG search span
        rag_span = tracer.add_span("rag_search")
        
        # Step 1: Retrieve RAG context
        rag_results, search_time = await search_service.search(
            db=db,
            query=request.query,
            top_k=5
        )
        
        rag_span.end()
        metrics_collector.record_rag_search(success=True)
        
        # Convert RAG results to context format
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
        
        # Start Gemini query span
        gemini_span = tracer.add_span("gemini_query", {"context_count": len(rag_context)})
        
        # Step 2: Query Gemini agent with RAG context
        response = await gemini_agent.query(
            user_query=request.query,
            rag_context=rag_context,
            conversation_history=[msg.dict() for msg in request.conversation_history]
        )
        
        gemini_span.end()
        
        # Track token usage in trace
        token_usage = response.get("token_usage", {})
        if token_usage:
            tracer.add_token_usage(
                input_tokens=token_usage.get("total_input_tokens", 0),
                output_tokens=token_usage.get("total_output_tokens", 0)
            )
        
        # Record tool calls
        for tool_call in response.get("tool_calls", []):
            metrics_collector.record_tool_call(
                tool_name=tool_call.get("tool", "unknown"),
                success=tool_call.get("success", True)
            )
        
        # Step 3: Format response with frontend-compatible structure
        # Calculate total tokens and estimated cost
        total_tokens = token_usage.get("total_input_tokens", 0) + token_usage.get("total_output_tokens", 0)
        
        # Gemini pricing (approximate): $0.001 per 1K tokens for input, $0.002 per 1K tokens for output
        estimated_cost = (
            token_usage.get("total_input_tokens", 0) * 0.001 / 1000 +
            token_usage.get("total_output_tokens", 0) * 0.002 / 1000
        )
        
        agent_response = AgentQueryResponse(
            response=response["response"],
            action_taken="gemini_agent",
            reasoning="Processed with Gemini agent using RAG context and tool calling",
            tool_calls=response.get("tool_calls", []),
            context_used=rag_context,
            metadata={
                "rag_context_count": response.get("rag_context_used", 0),
                "token_usage": token_usage,
                "search_time": search_time,
                "success": response.get("success", True),
                "model": "gemini-pro",
                "cached": False,
                # Add top-level fields for frontend compatibility
                "tokens_used": total_tokens,
                "cost": estimated_cost,
                "latency_ms": search_time * 1000  # Convert to ms
            }
        )
        
        # Cache the response (as dict)
        query_cache.set(request.query, agent_response.dict(), **cache_key_params)
        
        return agent_response
        
    except Exception as e:
        logger.error(f"Gemini agent query error: {e}")
        metrics_collector.record_rag_search(success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )


@router.get("/tools", response_model=List[ToolInfo])
async def list_agent_tools() -> List[ToolInfo]:
    """
    List available tools for the agent.
    
    Returns information about all tools the agent can use.
    """
    try:
        tools = rag_agent.list_tools()
        
        return [
            ToolInfo(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"]
            )
            for tool in tools
        ]
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/system-prompt")
async def get_system_prompt() -> Dict[str, str]:
    """
    Get the agent's system prompt.
    
    Returns the instructions and rules the agent follows.
    """
    return {
        "system_prompt": rag_agent.system_prompt,
        "agent_name": rag_agent.name,
        "tool_count": len(rag_agent.tools)
    }


@router.post("/chat", response_model=AgentQueryResponse)
async def chat_with_agent(
    request: AgentQueryRequest,
    db: AsyncSession = Depends(get_db_session)
) -> AgentQueryResponse:
    """
    Chat with the agent (conversational interface).
    
    Maintains conversation history and provides contextual responses.
    """
    try:
        logger.info(f"Chat message: '{request.query[:50]}...'")
        
        # Build context with conversation history
        context = AgentContext(
            user_query=request.query,
            conversation_history=[msg.dict() for msg in request.conversation_history],
            available_tools=list(rag_agent.tools.keys()),
            metadata={
                **request.metadata,
                "conversational": True
            }
        )
        
        # Process query
        response = await rag_agent.process(context)
        
        logger.info(f"Agent response: {response.action_taken}")
        
        return AgentQueryResponse(
            response=response.response,
            action_taken=response.action_taken,
            reasoning=response.reasoning,
            tool_calls=response.tool_calls,
            context_used=response.context_used,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat error: {str(e)}"
        )


@router.get("/health")
async def agent_health() -> Dict[str, Any]:
    """
    Check agent health status.
    
    Returns information about agent readiness and capabilities.
    """
    return {
        "status": "healthy",
        "agent_name": rag_agent.name,
        "tools_available": len(rag_agent.tools),
        "tools": list(rag_agent.tools.keys()),
        "ready": True
    }

