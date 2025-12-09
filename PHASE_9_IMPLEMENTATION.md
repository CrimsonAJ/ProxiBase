# ProxiBase Phase 9 - Hardening, Limits, and Polishing

## Overview

Phase 9 implements production-ready hardening, security measures, rate limiting, structured logging, and admin dashboard enhancements for ProxiBase.

## Features Implemented

### 1. SSRF Protection and Target Validation

**Location**: `backend/app/core/security.py`

Comprehensive SSRF (Server-Side Request Forgery) protection that blocks requests to:
- `localhost` / `127.0.0.0/8` (loopback addresses)
- `10.0.0.0/8` (private network)
- `172.16.0.0/12` (private network)
- `192.168.0.0/16` (private network)
- `169.254.0.0/16` (link-local addresses)
- Non-HTTP/HTTPS schemes (FTP, FILE, etc.)

**Functions**:
- `is_safe_origin_url(url)` - Returns (bool, reason) tuple
- `validate_target_url(url)` - Raises ValueError if unsafe

**Example**:
```python
from app.core.security import is_safe_origin_url

is_safe, reason = is_safe_origin_url("http://192.168.1.1/admin")
if not is_safe:
    print(f"Blocked: {reason}")
    # Output: Blocked: private IP address 192.168.1.1
```

### 2. Rate Limiting

**Location**: `backend/app/core/rate_limiter.py`

In-memory rate limiter using sliding window algorithm:
- Default: 60 requests per minute per client IP
- Configurable via environment variables
- Thread-safe implementation
- Automatic cleanup of old entries

**Configuration** (in `.env`):
```env
ENABLE_RATE_LIMITING=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

**Response Headers** (when rate limited):
- `Retry-After`: Seconds until retry allowed
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Seconds until limit resets

**HTTP Status**: `429 Too Many Requests`

### 3. Response Size Limits

**Configuration**:
```env
MAX_RESPONSE_SIZE_MB=15
```

- Enforced for non-media content (HTML, JSON, etc.)
- Media types (images, videos, audio) are not limited
- Returns `413 Payload Too Large` if exceeded

**Detected Media Types**:
- `image/*`
- `video/*`
- `audio/*`
- `application/octet-stream`

### 4. Request Timeouts

**Configuration**:
```env
REQUEST_TIMEOUT=15
```

- Default: 15 seconds per origin request
- Prevents hanging connections
- Returns `502 Bad Gateway` on timeout

### 5. Structured Logging

**Location**: `backend/app/main.py`

JSON-formatted logs for easy parsing and analysis:

**Log Fields**:
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (INFO, WARNING, ERROR)
- `logger`: Logger name ("proxibase")
- `message`: Log message
- `client_ip`: Client IP address
- `mirror_host`: Mirror hostname
- `origin_url`: Origin URL being proxied
- `status_code`: HTTP status code
- `latency_ms`: Request latency in milliseconds
- `user_agent`: Client user agent

**Example Log Entry**:
```json
{
  "timestamp": "2025-12-09T16:32:05.483163",
  "level": "INFO",
  "logger": "proxibase",
  "message": "Proxy content: https://en.wikipedia.org/",
  "client_ip": "127.0.0.1",
  "mirror_host": "wiki.test.local",
  "origin_url": "https://en.wikipedia.org/",
  "status_code": 200,
  "latency_ms": 674,
  "user_agent": "curl/7.88.1"
}
```

**Log Locations**:
- Console output (JSON formatted)
- `/var/log/supervisor/backend.err.log` (JSON logs)
- `/var/log/supervisor/backend.out.log` (SQLAlchemy queries)

### 6. Admin Dashboard Enhancements

**New API Endpoint**: `/admin/api/stats`

Returns comprehensive system statistics:
```json
{
  "total_sites": 4,
  "active_sites": 4,
  "inactive_sites": 0,
  "rate_limit_config": {
    "enabled": true,
    "max_requests": 60,
    "window_seconds": 60
  },
  "limits": {
    "max_response_size_mb": 15,
    "request_timeout_seconds": 15
  },
  "sites": [...],
  "global_config": {...}
}
```

**Authentication Required**: Must be logged in as admin

## Configuration Reference

### Environment Variables

Add these to `backend/.env`:

```env
# Phase 9: Hardening and Limits
RATE_LIMIT_REQUESTS=60          # Requests per window
RATE_LIMIT_WINDOW=60            # Window size in seconds
MAX_RESPONSE_SIZE_MB=15         # Max response size for non-media
REQUEST_TIMEOUT=15              # Request timeout in seconds
ENABLE_RATE_LIMITING=true       # Toggle rate limiting
```

### Default Values

| Setting | Default | Description |
|---------|---------|-------------|
| `RATE_LIMIT_REQUESTS` | 60 | Maximum requests per window |
| `RATE_LIMIT_WINDOW` | 60 | Time window in seconds |
| `MAX_RESPONSE_SIZE_MB` | 15 | Max response size (non-media) |
| `REQUEST_TIMEOUT` | 15 | Request timeout in seconds |
| `ENABLE_RATE_LIMITING` | true | Enable/disable rate limiting |

## Testing

### Test SSRF Protection

```bash
cd /app/backend
python3 << 'EOF'
from app.core.security import is_safe_origin_url

test_urls = [
    "https://example.com/",
    "http://localhost:8080/",
    "http://10.0.0.1/",
    "http://192.168.1.1/",
]

for url in test_urls:
    is_safe, reason = is_safe_origin_url(url)
    print(f"{'✓' if is_safe else '✗'} {url}")
    if not is_safe:
        print(f"  → {reason}")
EOF
```

### Test Rate Limiting

```bash
# Make 65 rapid requests (limit is 60)
for i in {1..65}; do
  curl -s -H "Host: wiki.test.local" \
    -w "Request $i: %{http_code}\n" \
    http://localhost:8001/ -o /dev/null
done
```

Expected: First ~60 requests succeed, remaining return `429`

### Test Structured Logging

```bash
# Make a request
curl -H "Host: wiki.test.local" http://localhost:8001/

# View JSON logs
tail -5 /var/log/supervisor/backend.err.log | grep '^{'
```

### Test Admin Stats API

```bash
# Login first (get session cookie)
# Then:
curl -s http://localhost:8001/admin/api/stats \
  -H "Cookie: admin_session=YOUR_TOKEN" | python3 -m json.tool
```

## Security Best Practices

1. **Change default admin credentials** in production
2. **Enable HTTPS** and set `secure=True` for cookies
3. **Monitor logs** regularly for suspicious activity
4. **Adjust rate limits** based on your traffic patterns
5. **Review SSRF rules** if you need to proxy internal services
6. **Set appropriate timeouts** based on your origin response times

## Production Checklist

- [ ] Change `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
- [ ] Set `SECRET_KEY` to a secure random value
- [ ] Enable HTTPS and update cookie settings
- [ ] Configure appropriate rate limits
- [ ] Set up log aggregation (e.g., ELK stack, Splunk)
- [ ] Monitor error logs for attack attempts
- [ ] Test SSRF protection with your specific requirements
- [ ] Verify response size limits work for your content
- [ ] Load test with expected traffic patterns

## Performance Considerations

### Rate Limiter

- **Memory usage**: Stores timestamps per IP
- **Cleanup**: Automatic cleanup of old entries
- **Scalability**: For high-traffic sites, consider Redis-based rate limiting

### Logging

- **Disk I/O**: JSON logging adds minimal overhead
- **Log rotation**: Configure logrotate for production
- **Analysis**: Use log aggregation tools for large-scale analysis

### SSRF Protection

- **DNS lookups**: May add 10-50ms latency per request
- **Caching**: Consider caching DNS results for frequently accessed domains

## Troubleshooting

### Rate Limit False Positives

If legitimate users are getting rate limited:

1. Check current settings:
   ```python
   from app.config import settings
   print(f"Limit: {settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}s")
   ```

2. Increase limits in `.env`:
   ```env
   RATE_LIMIT_REQUESTS=120
   RATE_LIMIT_WINDOW=60
   ```

3. Restart backend:
   ```bash
   sudo supervisorctl restart backend
   ```

### SSRF Blocking Legitimate Sites

If a legitimate site is being blocked:

1. Check the reason:
   ```python
   from app.core.security import is_safe_origin_url
   is_safe, reason = is_safe_origin_url("http://your-site.com")
   print(reason)
   ```

2. If it's a false positive, you may need to adjust the security rules in `core/security.py`

### Large Response Size Errors

If legitimate content is being blocked:

1. Increase the limit in `.env`:
   ```env
   MAX_RESPONSE_SIZE_MB=25
   ```

2. Or verify content type detection is working correctly

### Timeout Issues

If origin sites are slow:

1. Increase timeout in `.env`:
   ```env
   REQUEST_TIMEOUT=30
   ```

2. Monitor latency in logs to find problematic origins

## Log Analysis Examples

### Find slow requests:
```bash
grep '"latency_ms"' /var/log/supervisor/backend.err.log | \
  jq 'select(.latency_ms > 1000)' | \
  jq -r '[.timestamp, .origin_url, .latency_ms] | @tsv'
```

### Count requests by IP:
```bash
grep '"client_ip"' /var/log/supervisor/backend.err.log | \
  jq -r '.client_ip' | sort | uniq -c | sort -rn
```

### Find rate limit violations:
```bash
grep '"Rate limit exceeded"' /var/log/supervisor/backend.err.log | \
  jq -r '.client_ip' | sort | uniq -c
```

### Monitor error rates:
```bash
grep '"level": "ERROR"' /var/log/supervisor/backend.err.log | \
  jq -r '.message'
```

## Summary

Phase 9 successfully implements:

✅ **SSRF Protection** - Blocks private IPs and localhost  
✅ **Rate Limiting** - 60 req/min per IP (configurable)  
✅ **Response Limits** - 15MB max for non-media content  
✅ **Timeouts** - 15s request timeout  
✅ **Structured Logging** - JSON logs with full context  
✅ **Admin Dashboard** - Enhanced stats API  

All features are production-ready and configurable via environment variables.
