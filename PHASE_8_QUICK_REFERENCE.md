# Phase 8 Quick Reference

## What Was Implemented

**Phase 8: Cookie Jar, Sessions, and Header Forwarding**

✅ Per-user, per-origin cookie storage and management  
✅ Signed session identification (px_session_id cookie)  
✅ Cookie capture from origin Set-Cookie headers  
✅ Cookie injection into origin requests  
✅ Enhanced header forwarding with Referer rewriting  
✅ Configuration control via session_mode (stateless/cookie_jar)

## Files Added

### Models
- `/app/backend/app/models/cookie_jar.py` - CookieJar database model

### Core Utilities
- `/app/backend/app/core/session_manager.py` - Session ID generation, signing, verification
- `/app/backend/app/core/cookie_manager.py` - Cookie parsing, storage, retrieval

### Tests
- `/app/test_phase8_e2e.sh` - Automated test suite
- `/app/backend/test_phase8_integration.py` - Integration tests

### Documentation
- `/app/PHASE_8_DEMO.md` - Complete demo and usage guide
- `/app/PHASE_8_QUICK_REFERENCE.md` - This file

## Files Modified

- `/app/backend/app/proxy/router.py` - Enhanced with cookie jar logic
- `/app/backend/app/models/__init__.py` - Added CookieJar import

## Database Changes

### New Table: `cookie_jars`
```sql
CREATE TABLE cookie_jars (
    id INTEGER PRIMARY KEY,
    site_id INTEGER NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    origin_host VARCHAR(255) NOT NULL,
    cookie_data TEXT,
    FOREIGN KEY(site_id) REFERENCES sites(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_cookie_jar_lookup ON cookie_jars(site_id, session_id, origin_host);
CREATE INDEX ix_cookie_jars_session_id ON cookie_jars(session_id);
CREATE INDEX ix_cookie_jars_origin_host ON cookie_jars(origin_host);
```

## Configuration

### Enable Cookie Jar for a Site
```python
# Via database
UPDATE sites SET session_mode = 'cookie_jar' WHERE id = <site_id>;

# Via Python
site.session_mode = "cookie_jar"
```

### Disable Cookie Jar (Stateless Mode)
```python
# Via database
UPDATE sites SET session_mode = 'stateless' WHERE id = <site_id>;

# Via Python
site.session_mode = "stateless"
```

## Key Components

### Session Manager
```python
from app.core.session_manager import (
    SESSION_COOKIE_NAME,          # "px_session_id"
    generate_session_id(),        # Generate random session ID
    sign_session_id(sid),         # Sign session ID with HMAC
    verify_session_id(signed),    # Verify and extract session ID
    create_signed_session_cookie() # Generate new signed cookie
)
```

### Cookie Manager
```python
from app.core.cookie_manager import (
    store_cookies(db, site_id, session_id, origin_host, set_cookie_headers),
    get_cookies(db, site_id, session_id, origin_host),
    build_cookie_header(cookies_dict),
    parse_cookie_header(cookie_string)
)
```

## Testing

### Run All Phase 8 Tests
```bash
/app/test_phase8_e2e.sh
```

### Run Integration Tests
```bash
cd /app/backend && python3 test_phase8_integration.py
```

### Manual Test with cURL
```bash
# Enable cookie jar mode for site ID 4
cd /app/backend && python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('UPDATE sites SET session_mode = \"cookie_jar\" WHERE id = 4')
conn.commit()
conn.close()
"

# Make request and check for session cookie
curl -v -H "Host: wiki.test.local" http://localhost:8001/wiki/Test 2>&1 | grep px_session_id
```

## How It Works

1. **Client makes request** to mirror domain
2. **Check session cookie** (px_session_id)
   - If missing: create and sign new session ID
   - If present: verify signature
3. **Look up stored cookies** for (site_id, session_id, origin_host)
4. **Inject cookies** into origin request as Cookie header
5. **Forward request** to origin with proper headers
6. **Capture Set-Cookie** headers from origin response
7. **Store cookies** in database for this session/origin
8. **Strip Set-Cookie** headers (don't forward to client)
9. **Set px_session_id** cookie on response (if new session)
10. **Return response** to client

## Cookie Isolation

Cookies are isolated by three dimensions:
- **Site ID**: Which mirror site (prevents cross-site cookie leakage)
- **Session ID**: Which user session (prevents cross-user cookie access)
- **Origin Host**: Which origin domain (prevents cross-origin cookie access)

## Security Features

- **HMAC-SHA256 signing** of session IDs prevents tampering
- **HttpOnly flag** on px_session_id prevents JavaScript access
- **SameSite=lax** provides CSRF protection
- **Server-side storage** keeps origin cookies hidden from client
- **Cookie isolation** prevents unauthorized access

## Environment Variables

```bash
# Required in backend/.env
SECRET_KEY="your-secret-key-change-in-production"  # For session signing
```

⚠️ **Change SECRET_KEY in production!**

## Verification Commands

### Check Database
```bash
cd /app/backend && python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Check table exists
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"cookie_jars\"')
print('Table exists:', cursor.fetchone() is not None)

# Count entries
cursor.execute('SELECT COUNT(*) FROM cookie_jars')
print('Cookie jars:', cursor.fetchone()[0])

# View entries
cursor.execute('SELECT session_id, origin_host, cookie_data FROM cookie_jars LIMIT 5')
for row in cursor.fetchall():
    print(f'  {row[0][:20]}... -> {row[1]}')
"
```

### Check Site Configuration
```bash
cd /app/backend && python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('SELECT mirror_root, source_root, session_mode FROM sites')
for row in cursor.fetchall():
    print(f'{row[0]} -> {row[1]} [{row[2] or \"default\"}]')
"
```

### Test Module Imports
```bash
cd /app/backend && python3 -c "
from app.models.cookie_jar import CookieJar
from app.core.session_manager import SESSION_COOKIE_NAME
from app.core.cookie_manager import store_cookies, get_cookies
print('✓ All Phase 8 modules import successfully')
"
```

## Status

✅ **Phase 8 is COMPLETE and TESTED**

All tests passing (10/10):
- Backend health check
- Database table creation
- Session ID generation/signing/verification
- Cookie parsing and building
- Cookie storage and retrieval
- Configuration control (stateless vs cookie_jar)
- Integration with proxy router

## Next Steps

1. Test with real authenticated websites
2. Monitor cookie jar database size
3. Implement cookie expiration/cleanup
4. Consider Redis for high-traffic scenarios
5. Add admin UI for session management
