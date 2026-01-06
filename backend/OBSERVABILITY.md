# Observability & Performance Documentation

## Overview

Comprehensive observability system with request tracing, metrics collection, cost tracking, rate limiting, and query caching.

## Features

### ✅ Request Tracing
- Unique trace ID per request
- Span tracking for operations
- Latency measurement
- Error tracking

### ✅ Token Usage Tracking
- Input/output token counts
- Per-request tracking
- Aggregate statistics

### ✅ Cost Estimation
- Real-time cost calculation
- Per-query estimates
- Monthly projections

### ✅ Latency Logging
- Request duration
- Operation spans
- Detailed timing

### ✅ Rate Limiting
- 100 requests/minute default
- IP-based limiting
- Customizable limits

### ✅ Query Caching
- 1-hour TTL
- 1000-item capacity
- Automatic cache hits

## Architecture

```
Request → Middleware → Trace Start
              ↓
         Rate Limit Check
              ↓
         Cache Check
              ↓
    [Cache Hit] → Return Cached
              ↓
    [Cache Miss] → Process Request
              ↓
         Add Spans (RAG, Gemini, Tools)
              ↓
         Track Tokens & Cost
              ↓
         Cache Result
              ↓
         Record Metrics
              ↓
         Trace End → Response
```

## API Endpoints

### Metrics Endpoint

**GET /api/v1/metrics**

Prometheus-compatible metrics export.

**Response:** Prometheus text format
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/agent/query",status="200"} 42.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
...

# HELP token_usage_total Total tokens used
# TYPE token_usage_total counter
token_usage_total{model="gemini-pro",type="input"} 12450.0
token_usage_total{model="gemini-pro",type="output"} 3821.0

# HELP api_cost_total Total API cost in USD
# TYPE api_cost_total counter
api_cost_total{model="gemini-pro"} 0.00543

# HELP cache_hits_total Total cache hits
# TYPE cache_hits_total counter
cache_hits_total{cache_type="query"} 15.0
```

### Usage Endpoint

**GET /api/v1/usage**

Comprehensive usage statistics.

**Response:**
```json
{
  "success": true,
  "usage": {
    "uptime_seconds": 3600,
    "total_requests": 150,
    "recent_requests_1h": 150,
    "total_tokens": 45280,
    "total_cost_usd": 0.0134,
    "avg_cost_per_request": 0.000089,
    "cache_hits": 25,
    "cache_hit_rate": 16.67,
    "start_time": "2024-01-06T12:00:00"
  },
  "cache": {
    "size": 87,
    "max_size": 1000,
    "hits": 25,
    "misses": 125,
    "sets": 125,
    "hit_rate": 16.67,
    "total_requests": 150
  },
  "recent_requests": [
    {
      "timestamp": "2024-01-06T13:45:22",
      "method": "POST",
      "endpoint": "/api/v1/agent/query",
      "status_code": 200,
      "duration_ms": 2341.2,
      "token_usage": {
        "input_tokens": 1250,
        "output_tokens": 340,
        "total_tokens": 1590
      },
      "cost": 0.00048,
      "cache_hit": false
    }
  ]
}
```

### Usage Summary

**GET /api/v1/usage/summary**

High-level statistics only.

### Cache Statistics

**GET /api/v1/usage/cache**

Cache performance metrics.

**Response:**
```json
{
  "success": true,
  "size": 87,
  "max_size": 1000,
  "hits": 25,
  "misses": 125,
  "hit_rate": 16.67
}
```

### Clear Cache

**POST /api/v1/usage/cache/clear**

Clear all cached queries.

### Recent Requests

**GET /api/v1/usage/requests?limit=50**

Get recent request details.

### Cost Breakdown

**GET /api/v1/usage/cost**

Detailed cost analysis.

**Response:**
```json
{
  "success": true,
  "total_cost_usd": 0.0134,
  "total_requests": 150,
  "average_cost_per_request": 0.000089,
  "cost_by_endpoint": {
    "/api/v1/agent/query": {
      "total": 0.0120,
      "count": 130,
      "average": 0.000092
    },
    "/api/v1/rag/search": {
      "total": 0.0014,
      "count": 20,
      "average": 0.000070
    }
  },
  "estimated_monthly_cost": 0.40
}
```

## Request Tracing

Every request gets:

### Trace Headers

Responses include:
```
X-Trace-ID: 550e8400-e29b-41d4-a716-446655440000
X-Request-ID: 123e4567-e89b-12d3-a456-426614174000
```

### Trace Structure

```python
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "method": "POST",
  "path": "/api/v1/agent/query",
  "duration_ms": 2341.2,
  "status_code": 200,
  "spans": [
    {
      "name": "rag_search",
      "duration_ms": 234.5,
      "metadata": {}
    },
    {
      "name": "gemini_query",
      "duration_ms": 1890.3,
      "metadata": {"context_count": 5}
    }
  ],
  "token_usage": {
    "input_tokens": 1250,
    "output_tokens": 340,
    "total_tokens": 1590
  },
  "cost_estimate": 0.00048,
  "cache_hit": false
}
```

### Log Output

Structured JSON logs (production):
```json
{
  "timestamp": "2024-01-06T13:45:22.123Z",
  "level": "INFO",
  "message": "Request completed: POST /api/v1/agent/query",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 2341.2,
  "status_code": 200,
  "token_usage": {...},
  "cost_estimate": 0.00048,
  "cache_hit": false
}
```

## Cost Estimation

### Pricing Model (Gemini Pro)

- **Input**: $0.00025 per 1K tokens
- **Output**: $0.0005 per 1K tokens

### Calculation

```
Input Cost  = (input_tokens / 1000) × $0.00025
Output Cost = (output_tokens / 1000) × $0.0005
Total Cost  = Input Cost + Output Cost
```

### Example

Query with 1250 input tokens, 340 output tokens:
```
Input:  (1250/1000) × $0.00025 = $0.0003125
Output: (340/1000) × $0.0005   = $0.0001700
Total:  $0.0004825 ≈ $0.00048
```

## Rate Limiting

### Default Limits

- **100 requests per minute** per IP address
- **429 Too Many Requests** when exceeded

### Custom Limits

Decorate endpoints:
```python
from app.core.rate_limit import limiter

@router.post("/expensive-operation")
@limiter.limit("10/minute")
async def expensive_operation():
    ...
```

### Rate Limit Response

```json
{
  "error": "Rate limit exceeded",
  "detail": "100 per 1 minute"
}
```

## Query Caching

### Cache Strategy

- **TTL**: 1 hour
- **Capacity**: 1000 queries
- **Key**: Hash of query + parameters
- **Eviction**: LRU (Least Recently Used)

### Cache Hit

Cached responses include:
```json
{
  ...
  "metadata": {
    "cached": true
  }
}
```

### Cache Performance

Check with:
```bash
curl http://localhost:8000/api/v1/usage/cache
```

### Clear Cache

```bash
curl -X POST http://localhost:8000/api/v1/usage/cache/clear
```

## Monitoring

### Prometheus Integration

Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'contextos-backend'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/metrics'
```

### Grafana Dashboard

Import metrics:
- `http_requests_total`
- `http_request_duration_seconds`
- `token_usage_total`
- `api_cost_total`
- `cache_hits_total`

### Alert Rules

Example Prometheus alerts:
```yaml
groups:
  - name: contextos_alerts
    rules:
      - alert: HighCostPerRequest
        expr: rate(api_cost_total[5m]) / rate(http_requests_total[5m]) > 0.01
        annotations:
          summary: "High cost per request detected"
      
      - alert: LowCacheHitRate
        expr: rate(cache_hits_total[5m]) / rate(http_requests_total[5m]) < 0.1
        annotations:
          summary: "Cache hit rate below 10%"
```

## Usage Examples

### Check Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/metrics

# Usage statistics
curl http://localhost:8000/api/v1/usage

# Cost breakdown
curl http://localhost:8000/api/v1/usage/cost
```

### Monitor in Real-Time

```bash
# Watch usage stats
watch -n 5 'curl -s http://localhost:8000/api/v1/usage/summary | jq'

# Monitor cache performance
watch -n 2 'curl -s http://localhost:8000/api/v1/usage/cache | jq'
```

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get usage
response = requests.get(f"{BASE_URL}/usage")
usage = response.json()

print(f"Total requests: {usage['usage']['total_requests']}")
print(f"Total cost: ${usage['usage']['total_cost_usd']}")
print(f"Cache hit rate: {usage['cache']['hit_rate']}%")

# Get cost breakdown
cost_response = requests.get(f"{BASE_URL}/usage/cost")
cost_data = cost_response.json()

print(f"Monthly estimate: ${cost_data['estimated_monthly_cost']}")
```

## Performance Optimization

### Cache Configuration

Adjust in `app/core/cache.py`:
```python
query_cache = QueryCache(
    max_size=2000,        # Increase capacity
    ttl_seconds=7200      # 2 hour TTL
)
```

### Rate Limit Tuning

Adjust in `app/core/rate_limit.py`:
```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]  # Increase limit
)
```

## Best Practices

### 1. Monitor Costs

```bash
# Daily cost check
curl http://localhost:8000/api/v1/usage/cost
```

### 2. Optimize Cache Hit Rate

- Use consistent query phrasing
- Cache-friendly queries
- Monitor hit rate: aim for >20%

### 3. Track Latency

- Monitor P95/P99 latencies
- Set up alerts for slow requests (>5s)
- Investigate high-latency spans

### 4. Review Usage Patterns

```bash
# Top endpoints by cost
curl http://localhost:8000/api/v1/usage/cost | jq '.cost_by_endpoint'
```

## Troubleshooting

### High Costs

1. Check token usage:
   ```bash
   curl http://localhost:8000/api/v1/usage | jq '.usage.total_tokens'
   ```

2. Review cost by endpoint:
   ```bash
   curl http://localhost:8000/api/v1/usage/cost | jq '.cost_by_endpoint'
   ```

3. Optimize queries or increase caching

### Low Cache Hit Rate

1. Check cache stats:
   ```bash
   curl http://localhost:8000/api/v1/usage/cache
   ```

2. Increase TTL or capacity
3. Review query patterns

### Rate Limit Issues

1. Check current limits in logs
2. Adjust limits if legitimate traffic
3. Consider per-user limits

## Integration

### With Application Code

```python
from app.core.observability import tracer
from app.core.metrics import metrics_collector

# Add custom span
span = tracer.add_span("custom_operation", {"param": "value"})
# ... do work ...
span.end()

# Record custom metric
metrics_collector.record_tool_call("my_tool", success=True)
```

### With External Monitoring

- **Prometheus**: Scrape `/api/v1/metrics`
- **Grafana**: Import Prometheus datasource
- **Datadog**: Use StatsD exporter
- **New Relic**: Use Prometheus integration

## Success Metrics

Track these KPIs:

- **Request Rate**: requests/minute
- **Latency**: P50, P95, P99
- **Error Rate**: 4xx/5xx percentage
- **Token Usage**: tokens/request
- **Cost**: $/request, $/day
- **Cache Hit Rate**: percentage
- **Uptime**: percentage

---

**Observability system is production-ready!** 📊


