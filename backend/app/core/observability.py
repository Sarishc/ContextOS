"""Observability and tracing system."""
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger(__name__)

# Context variable for request tracing
request_context: ContextVar[Optional['RequestTrace']] = ContextVar('request_context', default=None)


@dataclass
class SpanMetrics:
    """Metrics for a span."""
    
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def end(self) -> None:
        """End the span and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class RequestTrace:
    """Request tracing information."""
    
    trace_id: str
    request_id: str
    method: str
    path: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    
    # Metrics
    spans: List[SpanMetrics] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost_estimate: float = 0.0
    cache_hit: bool = False
    
    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    def end(self, status_code: int, error: Optional[Exception] = None) -> None:
        """End the request trace."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status_code = status_code
        
        if error:
            self.error = str(error)
            self.error_type = type(error).__name__
    
    def add_span(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> SpanMetrics:
        """Add a new span."""
        span = SpanMetrics(
            name=name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.spans.append(span)
        return span
    
    def add_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add token usage."""
        self.token_usage['input_tokens'] = self.token_usage.get('input_tokens', 0) + input_tokens
        self.token_usage['output_tokens'] = self.token_usage.get('output_tokens', 0) + output_tokens
        self.token_usage['total_tokens'] = self.token_usage.get('total_tokens', 0) + input_tokens + output_tokens
    
    def estimate_cost(self, model: str = "gemini-pro") -> None:
        """
        Estimate cost based on token usage.
        
        Gemini Pro pricing (as of 2024):
        - Input: $0.00025 per 1K tokens
        - Output: $0.0005 per 1K tokens
        """
        input_tokens = self.token_usage.get('input_tokens', 0)
        output_tokens = self.token_usage.get('output_tokens', 0)
        
        input_cost = (input_tokens / 1000) * 0.00025
        output_cost = (output_tokens / 1000) * 0.0005
        
        self.cost_estimate = input_cost + output_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data['spans'] = [
            {
                'name': s.name,
                'duration_ms': s.duration_ms,
                'metadata': s.metadata
            }
            for s in self.spans if s.duration_ms is not None
        ]
        return data
    
    def log_summary(self) -> None:
        """Log request summary."""
        if self.error:
            logger.error(
                f"Request failed: {self.method} {self.path}",
                extra={
                    'trace_id': self.trace_id,
                    'request_id': self.request_id,
                    'duration_ms': self.duration_ms,
                    'status_code': self.status_code,
                    'error': self.error,
                    'error_type': self.error_type
                }
            )
        else:
            logger.info(
                f"Request completed: {self.method} {self.path}",
                extra={
                    'trace_id': self.trace_id,
                    'request_id': self.request_id,
                    'duration_ms': self.duration_ms,
                    'status_code': self.status_code,
                    'token_usage': self.token_usage,
                    'cost_estimate': self.cost_estimate,
                    'cache_hit': self.cache_hit,
                    'spans': len(self.spans)
                }
            )


class Tracer:
    """Request tracer."""
    
    @staticmethod
    def start_trace(method: str, path: str) -> RequestTrace:
        """Start a new request trace."""
        trace = RequestTrace(
            trace_id=str(uuid.uuid4()),
            request_id=str(uuid.uuid4()),
            method=method,
            path=path,
            start_time=time.time()
        )
        request_context.set(trace)
        return trace
    
    @staticmethod
    def get_current_trace() -> Optional[RequestTrace]:
        """Get current request trace."""
        return request_context.get()
    
    @staticmethod
    def add_span(name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[SpanMetrics]:
        """Add span to current trace."""
        trace = request_context.get()
        if trace:
            return trace.add_span(name, metadata)
        return None
    
    @staticmethod
    def add_token_usage(input_tokens: int, output_tokens: int, model: str = "gemini-pro") -> None:
        """Add token usage to current trace."""
        trace = request_context.get()
        if trace:
            trace.add_token_usage(input_tokens, output_tokens)
            trace.estimate_cost(model)
    
    @staticmethod
    def mark_cache_hit() -> None:
        """Mark current request as cache hit."""
        trace = request_context.get()
        if trace:
            trace.cache_hit = True


# Global tracer instance
tracer = Tracer()

