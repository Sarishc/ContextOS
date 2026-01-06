"""Metrics collection and monitoring."""
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from app.core.logging import get_logger

logger = get_logger(__name__)

# Prometheus metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

token_usage_total = Counter(
    'token_usage_total',
    'Total tokens used',
    ['model', 'type']  # type: input or output
)

cost_total = Counter(
    'api_cost_total',
    'Total API cost in USD',
    ['model']
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

active_requests = Gauge(
    'active_requests',
    'Number of active requests'
)

tool_calls = Counter(
    'tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

rag_searches = Counter(
    'rag_searches_total',
    'Total RAG searches',
    ['status']
)


class MetricsCollector:
    """Collect and aggregate metrics."""
    
    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.requests: List[Dict[str, Any]] = []
        self.usage_stats: Dict[str, Any] = defaultdict(int)
        self.start_time = datetime.utcnow()
        logger.info("MetricsCollector initialized")
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        token_usage: Dict[str, int],
        cost: float,
        cache_hit: bool = False
    ) -> None:
        """Record request metrics."""
        # Prometheus metrics
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_ms / 1000)  # Convert to seconds
        
        # Token usage
        if token_usage:
            model = "gemini-pro"
            token_usage_total.labels(
                model=model,
                type="input"
            ).inc(token_usage.get('input_tokens', 0))
            
            token_usage_total.labels(
                model=model,
                type="output"
            ).inc(token_usage.get('output_tokens', 0))
            
            cost_total.labels(model=model).inc(cost)
        
        # Cache metrics
        if cache_hit:
            cache_hits.labels(cache_type="query").inc()
        
        # Store request data
        self.requests.append({
            'timestamp': datetime.utcnow().isoformat(),
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'token_usage': token_usage,
            'cost': cost,
            'cache_hit': cache_hit
        })
        
        # Keep only recent requests (last 1000)
        if len(self.requests) > 1000:
            self.requests = self.requests[-1000:]
        
        # Update usage stats
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_tokens'] += token_usage.get('total_tokens', 0)
        self.usage_stats['total_cost'] += cost
        if cache_hit:
            self.usage_stats['cache_hits'] += 1
    
    def record_tool_call(self, tool_name: str, success: bool) -> None:
        """Record tool call."""
        status = "success" if success else "error"
        tool_calls.labels(tool_name=tool_name, status=status).inc()
    
    def record_rag_search(self, success: bool) -> None:
        """Record RAG search."""
        status = "success" if success else "error"
        rag_searches.labels(status=status).inc()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        uptime = datetime.utcnow() - self.start_time
        
        # Calculate averages
        total_requests = self.usage_stats.get('total_requests', 0)
        avg_cost_per_request = (
            self.usage_stats.get('total_cost', 0) / total_requests
            if total_requests > 0 else 0
        )
        
        cache_hit_rate = (
            (self.usage_stats.get('cache_hits', 0) / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        # Recent requests (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_requests = [
            r for r in self.requests
            if datetime.fromisoformat(r['timestamp']) > one_hour_ago
        ]
        
        return {
            'uptime_seconds': int(uptime.total_seconds()),
            'total_requests': total_requests,
            'recent_requests_1h': len(recent_requests),
            'total_tokens': self.usage_stats.get('total_tokens', 0),
            'total_cost_usd': round(self.usage_stats.get('total_cost', 0), 4),
            'avg_cost_per_request': round(avg_cost_per_request, 6),
            'cache_hits': self.usage_stats.get('cache_hits', 0),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'start_time': self.start_time.isoformat()
        }
    
    def get_recent_requests(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent requests."""
        return self.requests[-limit:]
    
    def export_prometheus_metrics(self) -> tuple[bytes, str]:
        """Export Prometheus metrics."""
        return generate_latest(), CONTENT_TYPE_LATEST


# Global metrics collector
metrics_collector = MetricsCollector()

