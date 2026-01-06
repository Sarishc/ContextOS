"""Request middleware for observability."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.observability import tracer
from app.core.metrics import metrics_collector, active_requests
from app.core.logging import get_logger

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and metrics."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request with tracing and metrics.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path in ["/metrics", "/health"]:
            return await call_next(request)
        
        # Start trace
        trace = tracer.start_trace(
            method=request.method,
            path=request.url.path
        )
        
        # Increment active requests
        active_requests.inc()
        
        # Add trace ID to request state
        request.state.trace_id = trace.trace_id
        request.state.request_id = trace.request_id
        
        error = None
        response = None
        
        try:
            # Process request
            response = await call_next(request)
            
            # End trace
            trace.end(status_code=response.status_code)
            
            # Add trace headers to response
            response.headers["X-Trace-ID"] = trace.trace_id
            response.headers["X-Request-ID"] = trace.request_id
            
            return response
            
        except Exception as e:
            error = e
            logger.error(f"Request error: {e}")
            trace.end(status_code=500, error=e)
            raise
            
        finally:
            # Decrement active requests
            active_requests.dec()
            
            # Log trace summary
            trace.log_summary()
            
            # Record metrics
            if response:
                metrics_collector.record_request(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code if response else 500,
                    duration_ms=trace.duration_ms or 0,
                    token_usage=trace.token_usage,
                    cost=trace.cost_estimate,
                    cache_hit=trace.cache_hit
                )

