# ProxiBase - Advanced Reverse Proxy Server

**ProxiBase** is a sophisticated reverse proxy server for creating and managing mirror websites with advanced URL rewriting, security features, session management, and ad/analytics control.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Use Cases](#-use-cases)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Server](#-running-the-server)
- [Usage Guide](#-usage-guide)
- [Testing](#-testing)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Advanced Features](#-advanced-features)

---

## 🚀 Features

### Core Proxy Features
- **🌐 Mirror Site Creation**: Map mirror domains to origin domains (e.g., `mirror.com` → `source.com`)
- **🔗 Complete URL Rewriting**: Automatically rewrites all links, forms, images, scripts, and stylesheets
- **🌲 Subdomain Support**: Proxy entire subdomain trees (e.g., `xyz.source.com` → `xyz.mirror.com`)
- **🌍 External Domain Proxying**: Proxy external domains as `/external.domain.com/path`
- **📝 HTML Content Rewriting**: Intelligent rewriting of hrefs, src attributes, forms, and more

### Advanced Features
- **🔒 Session Management**: Cookie jar system for maintaining user sessions and login states
- **🍪 Cookie Handling**: Server-side cookie storage with per-user, per-origin isolation
- **🎨 Ad Blocking & Injection**: Remove origin ads/analytics and inject custom ads
- **🔄 JavaScript Redirect Rewriting**: Rewrite `location.href` and similar patterns in inline scripts
- **🎭 CSS URL Rewriting**: Handle `url()` patterns in stylesheets and inline styles
- **🖼️ Flexible Media Policies**: Control how images, videos, and other media are handled

### Security & Performance (Phase 9)
- **🛡️ SSRF Protection**: Blocks requests to private IPs, localhost, and unsafe schemes
- **⏱️ Rate Limiting**: Configurable request rate limiting per client IP (default: 60 req/min)
- **📊 Response Size Limits**: Prevents proxy abuse with configurable size limits (default: 15MB for non-media)
- **⏰ Request Timeouts**: Configurable timeouts to prevent hanging connections (default: 15s)
- **📝 Structured Logging**: JSON-formatted logs with full request context for analysis
- **🔐 Admin Authentication**: Secure admin panel with session-based authentication

### Management Features
- **🎛️ Web Admin Panel**: User-friendly interface for managing sites and configurations
- **⚙️ Per-Site Configuration**: Override global settings for individual mirror sites
- **🌍 Global Defaults**: Set default behaviors for all sites
- **📈 Dashboard Statistics**: Real-time stats on sites, rate limits, and system health

---

## 💡 Use Cases

### 1. **Content Archiving & Preservation**
Create mirrors of websites for archival purposes, research, or offline access.

### 2. **Bypassing Geo-Restrictions**
Provide access to geo-restricted content through proxy mirrors.

### 3. **Ad-Free Browsing**
Remove ads and trackers from websites while optionally injecting your own content.

### 4. **Website Testing & Development**
Test how websites behave when accessed through different domains or with modified content.

### 5. **Load Distribution**
Distribute traffic across multiple origins or provide fallback access points.

### 6. **Privacy & Anonymization**
Proxy websites to provide anonymous access without revealing user IP addresses to origin servers.

### 7. **Content Modification**
Inject custom scripts, analytics, or modifications into proxied content.

---

## 🏗️ Architecture

ProxiBase is built with a modern, scalable architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Request (mirror.com)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      ProxiBase Server                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                      │  │
│  │  ├─ Rate Limiter (Phase 9)                               │  │
│  │  ├─ SSRF Protection (Phase 9)                            │  │
│  │  ├─ Admin Router (/admin, /login, /logout)              │  │
│  │  └─ Proxy Router (catch-all for mirror domains)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Components                                          │  │
│  │  ├─ Session Manager (Cookie Jar)                         │  │
│  │  ├─ Cookie Manager (Storage/Retrieval)                   │  │
│  │  ├─ URL Rewriter (HTML/JS/CSS)                           │  │
│  │  ├─ Ad Filter (Block/Inject)                             │  │
│  │  └─ Security Module (SSRF, Validation)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SQLite Database                                          │  │
│  │  ├─ sites (mirror configurations)                        │  │
│  │  ├─ global_config (default settings)                     │  │
│  │  ├─ cookie_jars (session cookies)                        │  │
│  │  └─ admin_users (authentication)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Request (source.com)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       Origin Server                              │
│                    (source.com, wikipedia.org, etc.)             │
└──────────────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- **Backend**: Python 3.11+, FastAPI, uvicorn
- **Database**: SQLite with SQLAlchemy (async)
- **HTTP Client**: httpx (async)
- **HTML Parsing**: BeautifulSoup4, lxml
- **Templates**: Jinja2 (for admin panel)
- **Process Management**: supervisor
- **Authentication**: JWT-based sessions

---

## 🔍 How It Works

### Request Flow

1. **Client Request**: Browser requests `http://mirror.com/page`
   
2. **Host Matching**: ProxiBase matches `mirror.com` against configured mirror sites
   
3. **Origin Mapping**: Maps to origin URL: `http://source.com/page`
   
4. **Security Checks** (Phase 9):
   - SSRF validation (block private IPs, localhost)
   - Rate limit check (per client IP)
   
5. **Session Management** (Phase 8):
   - Check for `px_session_id` cookie
   - Retrieve stored cookies for this origin
   - Inject cookies into origin request
   
6. **Origin Request**:
   - Forward request to origin with proper headers
   - Handle redirects (rewrite Location headers)
   - Capture Set-Cookie headers
   
7. **Response Processing**:
   - HTML: Parse and rewrite all URLs, forms, scripts
   - JS: Rewrite redirect patterns (if enabled)
   - CSS: Rewrite url() patterns
   - Media: Proxy or pass through based on policy
   
8. **Content Filtering** (Phase 6):
   - Remove ads/analytics (if enabled)
   - Inject custom ads/trackers (if configured)
   
9. **Response Delivery**:
   - Store origin cookies in database
   - Set session cookie (if new session)
   - Return modified content to client

### URL Rewriting Examples

**Scenario**: Mirror `wiki.test.local` → Origin `en.wikipedia.org`

| Origin URL | Mirror URL |
|-----------|------------|
| `https://en.wikipedia.org/wiki/Page` | `https://wiki.test.local/wiki/Page` |
| `https://upload.wikimedia.org/image.jpg` | `https://wiki.test.local/external.upload.wikimedia.org/image.jpg` |
| `/wiki/Article` | `https://wiki.test.local/wiki/Article` |
| `https://login.wikipedia.org/auth` | `https://wiki.test.local/external.login.wikipedia.org/auth` |

---

## 📦 Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version
- **supervisor**: For process management
- **SQLite**: 3.x (usually pre-installed)
- **Git**: For cloning the repository

**System Requirements:**
- Linux/Unix-based system (Ubuntu, Debian, CentOS, macOS)
- 512MB RAM minimum (2GB+ recommended for production)
- 1GB disk space

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ProxiBase
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies (Optional)

The frontend is a placeholder React app. Only needed if you want to customize it.

```bash
cd frontend
yarn install
# or
npm install
```

### 5. Initialize Database

The database will be automatically initialized on first run. To manually initialize:

```bash
cd backend
python3 << 'EOF'
from app.db.session import engine, Base
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully!")

asyncio.run(init_db())
EOF
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# backend/.env

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Admin Panel Configuration
ADMIN_HOST=0.0.0.0
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Security
SECRET_KEY=your-secret-key-change-in-production-1234567890

# MongoDB (optional, legacy)
MONGO_URL=mongodb://localhost:27017
DB_NAME=proxibase_db

# CORS Configuration
CORS_ORIGINS=*

# Phase 9: Security & Performance
RATE_LIMIT_REQUESTS=60        # Max requests per window
RATE_LIMIT_WINDOW=60          # Time window in seconds
MAX_RESPONSE_SIZE_MB=15       # Max response size for non-media content
REQUEST_TIMEOUT=15            # Request timeout in seconds
ENABLE_RATE_LIMITING=true     # Enable/disable rate limiting
```

### Frontend Configuration (Optional)

Create `.env` in the `frontend` directory:

```bash
# frontend/.env

REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=443
```

---

## 🚀 Running the Server

### Method 1: Using Supervisor (Recommended for Production)

Supervisor keeps the services running in the background and restarts them if they crash.

```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# View logs
sudo supervisorctl tail -f backend

# Restart services
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart all

# Stop services
sudo supervisorctl stop backend frontend
```

### Method 2: Manual Start (Development)

**Terminal 1 - Backend:**

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend (Optional):**

```bash
cd frontend
yarn start
```

### Method 3: Background Processes

**Start backend in background:**

```bash
cd backend
nohup uvicorn server:app --host 0.0.0.0 --port 8001 > backend.log 2>&1 &
echo $! > backend.pid
```

**Stop backend:**

```bash
kill $(cat backend/backend.pid)
rm backend/backend.pid
```

### Verify Services are Running

```bash
# Check if backend is responding
curl http://localhost:8001/health

# Expected output: {"status":"ok"}
```

---

## 📚 Usage Guide

### Accessing the Admin Panel

1. **Access URL**: 
   ```
   http://localhost:8001/login
   ```

2. **Login Credentials** (from .env):
   - Username: `admin` (default, change in `.env`)
   - Password: `admin123` (default, **CHANGE IN PRODUCTION**)

3. **After Login**:
   - Dashboard: View stats and system info
   - Sites: Manage mirror site configurations
   - Settings: Configure global defaults

### Creating a Mirror Site

**Via Admin Panel:**

1. Navigate to `/admin/sites`
2. Click "Create New Site"
3. Fill in the form:
   - **Mirror Root**: Your mirror domain (e.g., `mirror.example.com`)
   - **Source Root**: Origin domain (e.g., `source.example.com`)
   - **Enabled**: Check to activate

**Via Database:**

```bash
cd backend
python3 << 'EOF'
import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

cursor.execute('''
    INSERT INTO sites (mirror_root, source_root, enabled, proxy_subdomains, session_mode)
    VALUES (?, ?, ?, ?, ?)
''', ('wiki.test.local', 'en.wikipedia.org', 1, 1, 'cookie_jar'))

conn.commit()
conn.close()
print("Site created successfully!")
EOF
```

### Testing Your Mirror

1. **Add hosts entry** (for local testing):
   ```bash
   echo "127.0.0.1 wiki.test.local" | sudo tee -a /etc/hosts
   ```

2. **Test with cURL**:
   ```bash
   curl -H "Host: wiki.test.local" http://localhost:8001/
   ```

3. **Test in Browser**:
   ```
   http://wiki.test.local:8001/
   ```

---

## 🧪 Testing

### Quick Health Check

```bash
curl http://localhost:8001/health
# Expected: {"status":"ok"}
```

### Running Test Scripts

```bash
# Phase 9: Security and hardening (comprehensive)
bash test_phase9_e2e.sh

# Phase 8: Cookie jar and sessions
bash test_phase8_e2e.sh

# Phase 7: JS and CSS rewriting
bash test_phase7_e2e.sh
```

### Manual Testing

```bash
# Test with example.com mirror
curl -H "Host: proxy.test.local" http://localhost:8001/

# Test rate limiting
for i in {1..65}; do
  curl -s -H "Host: proxy.test.local" \
    -w "Request $i: %{http_code}\n" \
    http://localhost:8001/ -o /dev/null
done
```

### Viewing Logs

```bash
# Backend logs (JSON formatted)
tail -f /var/log/supervisor/backend.err.log

# Parse JSON logs
tail -20 /var/log/supervisor/backend.err.log | grep '^{' | jq .
```

---

## 📡 API Reference

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Admin Endpoints

**Login:**
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Get Stats:**
```
GET /admin/api/stats
Cookie: admin_session=<token>
```

---

## 🔒 Security

### SSRF Protection (Phase 9)

Blocks requests to:
- Localhost (`127.0.0.0/8`)
- Private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
- Link-local addresses (`169.254.0.0/16`)

### Rate Limiting

- Default: 60 requests per minute per client IP
- Configurable via environment variables

### Best Practices

1. **Change default credentials**
2. **Use strong SECRET_KEY**
3. **Enable HTTPS in production**
4. **Monitor logs for suspicious activity**
5. **Regular security updates**

---

## 🔧 Troubleshooting

### Backend Won't Start

```bash
# Check logs
tail -50 /var/log/supervisor/backend.err.log

# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

### Mirror Site Not Working

```bash
# Check if site exists
cd backend
python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM sites')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

### Rate Limiting Issues

```bash
# Increase limits in backend/.env
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW=60

# Restart backend
sudo supervisorctl restart backend
```

---

## 🎯 Advanced Features

### Custom Ad Injection

Configure in admin panel:
1. Enable "Inject Ads"
2. Add HTML in "Custom Ad HTML" field

### External Domain Proxying

Proxy external resources as `/external.domain.com/path`

### Media Policies

- `proxy`: Proxy all media (default)
- `direct`: Serve directly from origin
- `block`: Block all media

### Database Management

```bash
# Export configuration
cd backend
sqlite3 app.db << 'EOF'
.mode json
.output sites_export.json
SELECT * FROM sites;
.quit
EOF

# Backup database
cp backend/app.db backend/app.db.backup
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- BeautifulSoup for HTML parsing
- httpx for async HTTP client
- SQLAlchemy for database ORM

---

**Built with ❤️ by the ProxiBase Team**

*Version: 1.0.0 (Phase 9 Complete)*
