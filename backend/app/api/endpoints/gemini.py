"""Gemini-specific endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.services.gemini_agent import gemini_agent
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/token-stats")
async def get_token_stats() -> Dict[str, Any]:
    """
    Get token usage statistics for Gemini agent.
    
    Returns token tracking information including:
    - Total input tokens
    - Total output tokens
    - Total requests
    """
    try:
        stats = gemini_agent.get_token_stats()
        
        return {
            "success": True,
            "stats": stats,
            "model": "gemini-pro"
        }
        
    except Exception as e:
        logger.error(f"Error getting token stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get token stats: {str(e)}"
        )


@router.post("/reset-token-stats")
async def reset_token_stats() -> Dict[str, str]:
    """
    Reset token usage statistics.
    
    Clears all token tracking counters.
    """
    try:
        gemini_agent.reset_token_stats()
        
        return {
            "success": True,
            "message": "Token statistics reset"
        }
        
    except Exception as e:
        logger.error(f"Error resetting token stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset token stats: {str(e)}"
        )


@router.get("/tools")
async def list_gemini_tools() -> Dict[str, Any]:
    """
    List all tools available to the Gemini agent.
    
    Returns tool schemas and descriptions.
    """
    try:
        tools = gemini_agent.dispatcher.get_tool_schemas()
        
        return {
            "success": True,
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/health")
async def gemini_health() -> Dict[str, Any]:
    """
    Check Gemini agent health status.
    
    Returns information about agent configuration and status.
    """
    from app.core.config import settings
    
    return {
        "status": "healthy",
        "model": settings.GEMINI_MODEL,
        "temperature": settings.GEMINI_TEMPERATURE,
        "max_tokens": settings.GEMINI_MAX_TOKENS,
        "tools_registered": len(gemini_agent.dispatcher.tools),
        "api_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key")
    }

