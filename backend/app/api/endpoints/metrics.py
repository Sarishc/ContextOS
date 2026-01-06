"""Metrics and observability endpoints."""
from typing import Dict, Any, List
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from app.core.metrics import metrics_collector
from app.core.cache import query_cache
from app.core.observability import tracer
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics() -> Response:
    """
    Get Prometheus-compatible metrics.
    
    Returns metrics in Prometheus format for scraping.
    """
    metrics_data, content_type = metrics_collector.export_prometheus_metrics()
    
    return Response(
        content=metrics_data,
        media_type=content_type
    )


@router.get("/usage")
async def get_usage_stats() -> Dict[str, Any]:
    """
    Get comprehensive usage statistics.
    
    Returns:
        Usage statistics including:
        - Request counts
        - Token usage
        - Cost estimates
        - Cache performance
        - Recent requests
    """
    try:
        usage_summary = metrics_collector.get_usage_summary()
        cache_stats = query_cache.get_stats()
        
        # Get recent requests (last 10)
        recent_requests = metrics_collector.get_recent_requests(limit=10)
        
        return {
            "success": True,
            "usage": usage_summary,
            "cache": cache_stats,
            "recent_requests": recent_requests
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/usage/summary")
async def get_usage_summary() -> Dict[str, Any]:
    """
    Get usage summary without detailed requests.
    
    Returns:
        High-level usage statistics.
    """
    try:
        return {
            "success": True,
            **metrics_collector.get_usage_summary()
        }
        
    except Exception as e:
        logger.error(f"Error getting usage summary: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/usage/cache")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Cache performance metrics.
    """
    try:
        return {
            "success": True,
            **query_cache.get_stats()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/usage/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear the query cache.
    
    Returns:
        Confirmation message.
    """
    try:
        query_cache.clear()
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/usage/requests")
async def get_recent_requests(limit: int = 50) -> Dict[str, Any]:
    """
    Get recent requests with details.
    
    Args:
        limit: Number of requests to return (max 100)
        
    Returns:
        Recent request data.
    """
    try:
        limit = min(limit, 100)  # Cap at 100
        requests = metrics_collector.get_recent_requests(limit=limit)
        
        return {
            "success": True,
            "requests": requests,
            "count": len(requests)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent requests: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/usage/cost")
async def get_cost_breakdown() -> Dict[str, Any]:
    """
    Get cost breakdown and estimates.
    
    Returns:
        Cost analysis.
    """
    try:
        usage = metrics_collector.get_usage_summary()
        recent_requests = metrics_collector.get_recent_requests(limit=100)
        
        # Calculate cost breakdown
        total_cost = usage.get('total_cost_usd', 0)
        total_requests = usage.get('total_requests', 0)
        
        # Average cost per request
        avg_cost = (total_cost / total_requests) if total_requests > 0 else 0
        
        # Calculate costs by endpoint
        endpoint_costs = {}
        for req in recent_requests:
            endpoint = req.get('endpoint', 'unknown')
            cost = req.get('cost', 0)
            
            if endpoint not in endpoint_costs:
                endpoint_costs[endpoint] = {'total': 0, 'count': 0}
            
            endpoint_costs[endpoint]['total'] += cost
            endpoint_costs[endpoint]['count'] += 1
        
        # Calculate averages
        for endpoint, data in endpoint_costs.items():
            data['average'] = data['total'] / data['count'] if data['count'] > 0 else 0
        
        return {
            "success": True,
            "total_cost_usd": round(total_cost, 4),
            "total_requests": total_requests,
            "average_cost_per_request": round(avg_cost, 6),
            "cost_by_endpoint": endpoint_costs,
            "estimated_monthly_cost": round(total_cost * 30, 2) if total_requests > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {e}")
        return {
            "success": False,
            "error": str(e)
        }

