# ProxiBase Phase 4 - Demo Instructions

## Quick Start Guide

### 1. Access the Admin Panel

**URL**: `http://0.0.0.0:8001/login`

**Credentials**:
- Username: `admin`
- Password: `admin123`

### 2. Existing Test Sites

The database already has these test sites configured:

| ID | Mirror Root | Source Root | Status |
|----|-------------|-------------|--------|
| 1 | mirror.example.com | source.example.com | ✅ Active |
| 2 | test.mirror.com | test.source.com | ✅ Active |
| 3 | proxy.test.local | example.com | ✅ Active |
| 4 | wiki.test.local | en.wikipedia.org | ✅ Active |

### 3. Testing Proxy Functionality

#### Test 1: Basic Proxy (Example.com)
```bash
curl -H "Host: proxy.test.local" http://127.0.0.1:8001/

# Expected Result:
# Returns HTML content from example.com
# Status: 200 OK
```

#### Test 2: Subdomain Mapping
```bash
# This tests subdomain mapping: xyz.mirror.com → xyz.source.com
curl -H "Host: test.proxy.test.local" http://127.0.0.1:8001/

# Expected Result:
# Attempts to fetch test.example.com (doesn't exist)
# Status: 502 Bad Gateway
# Message: Error fetching origin: [Errno -2] Name or service not known
# This proves subdomain mapping is working!
```

#### Test 3: External Domain Encoding
```bash
# This tests external domain encoding
curl -i -H "Host: proxy.test.local" http://127.0.0.1:8001/google.com/

# Expected Result:
# Redirect intercepted and rewritten
# Status: 301 Moved Permanently
# Location: https://proxy.test.local/www.google.com/
# This shows external domains are encoded in the URL path!
```

#### Test 4: Wikipedia Proxy
```bash
curl -H "Host: wiki.test.local" http://127.0.0.1:8001/wiki/Test

# Expected Result:
# Successfully proxies to en.wikipedia.org
# Status: 403 Forbidden (Wikipedia blocks bots)
# Content: "Please respect our robot policy..."
# This proves the proxy is working, Wikipedia is just blocking it!
```

### 4. Creating a New Site via Admin Panel

1. Login at `http://0.0.0.0:8001/login`
2. Navigate to "Sites" → "Create New Site"
3. Fill in the form:
   - **Mirror Root**: `myproxy.local` (your mirror domain)
   - **Source Root**: `httpbin.org` (the origin domain to proxy)
   - **Enabled**: ✅ (check this box)
4. Click "Create Site"

### 5. Testing Your New Site

```bash
# Test httpbin.org proxy
curl -H "Host: myproxy.local" http://127.0.0.1:8001/html

# Expected Result:
# Returns HTML from httpbin.org/html
# Status: 200 OK
```

### 6. Testing Redirect Interception

```bash
# Test redirect handling
curl -i -H "Host: myproxy.local" http://127.0.0.1:8001/redirect/3

# Expected Result:
# Intercepts redirect and rewrites Location header
# Status: 302 Found
# Location: https://myproxy.local/get (or similar)
```

## Phase 4 Features Demonstrated

### ✅ Mirror Domain Routing
- Requests with `Host: proxy.test.local` are routed to `example.com`
- Multiple mirror domains can be configured for different origins

### ✅ Subdomain Mapping
- `xyz.mirror.com` automatically maps to `xyz.source.com`
- Preserves subdomain structure across proxy

### ✅ External Domain Encoding
- External redirects like `https://external.com/path` become `/external.com/path`
- Keeps all browsing within the mirror domain

### ✅ Redirect Interception
- All 3xx redirects are intercepted
- Location headers are rewritten to mirror URLs
- Status codes are preserved (301, 302, 307, 308)

### ✅ SSRF Protection
- Blocks localhost, 127.0.0.1, private IPs
- Only allows HTTP and HTTPS
- Prevents attacks on internal services

### ✅ Header Filtering
- Strips security headers (CSP, HSTS, X-Frame-Options)
- Removes Set-Cookie (cookie jars in future phase)
- Removes CORS headers

### ✅ HTML Pass-through
- HTML content returned as-is
- No rewriting yet (that's Phase 5)
- Other content types streamed directly

### ✅ All HTTP Methods
- Supports GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- Body and query parameters forwarded correctly

## Advanced Testing with curl

### Test with Custom Headers
```bash
curl -H "Host: myproxy.local" \
     -H "User-Agent: Mozilla/5.0" \
     -H "Accept: text/html" \
     http://127.0.0.1:8001/headers

# Shows which headers are forwarded to origin
```

### Test POST Request
```bash
curl -X POST \
     -H "Host: myproxy.local" \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}' \
     http://127.0.0.1:8001/post

# Tests POST data forwarding
```

### Test Query Parameters
```bash
curl -H "Host: myproxy.local" \
     "http://127.0.0.1:8001/get?foo=bar&test=123"

# Tests query parameter forwarding
```

## Troubleshooting

### Issue: 404 Not Found
**Cause**: No site configured for the Host header
**Solution**: Create a site in the admin panel with matching `mirror_root`

### Issue: 502 Bad Gateway
**Cause**: Origin server unreachable or doesn't exist
**Solution**: 
- Check the `source_root` domain is valid
- Verify DNS resolution: `nslookup <source_root>`

### Issue: 403 Forbidden
**Cause**: Origin server blocking the request (e.g., bot protection)
**Solution**: 
- This is expected for sites like Wikipedia
- The proxy is working, the origin is rejecting the request
- Try a different test site (e.g., example.com, httpbin.org)

### Issue: Connection refused
**Cause**: Backend not running
**Solution**: 
```bash
sudo supervisorctl status backend
sudo supervisorctl restart backend
```

## Next Phase Preview

Phase 5 will add **HTML rewriting** to replace URLs within HTML content:
- Rewrite `<a href="https://source.com/path">` to mirror URLs
- Rewrite `<img src="...">` to proxy images
- Rewrite `<script src="...">` and `<link href="...">` 
- Handle inline JavaScript redirects

For now, Phase 4 provides the **core proxy infrastructure** with redirect interception!

## Need Help?

Check the logs:
```bash
# Backend logs
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log

# Check services
sudo supervisorctl status
```

Check database:
```bash
cd /app/backend
python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('SELECT id, mirror_root, source_root, enabled FROM sites')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1]} → {row[2]} (enabled: {row[3]})')
conn.close()
"
```
