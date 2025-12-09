from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
import json
from datetime import datetime
from app.admin.router import router as admin_router
from app.proxy.router import router as proxy_router
from app.config import settings
from app.core.rate_limiter import init_rate_limiter

# Phase 9: Configure structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'client_ip'):
            log_data['client_ip'] = record.client_ip
        if hasattr(record, 'mirror_host'):
            log_data['mirror_host'] = record.mirror_host
        if hasattr(record, 'origin_url'):
            log_data['origin_url'] = record.origin_url
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'latency_ms'):
            log_data['latency_ms'] = record.latency_ms
        if hasattr(record, 'user_agent'):
            log_data['user_agent'] = record.user_agent
        
        return json.dumps(log_data)

# Set up logging
logger = logging.getLogger("proxibase")
logger.setLevel(logging.INFO)

# Console handler with JSON formatting
console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONFormatter())
logger.addHandler(console_handler)

# Initialize rate limiter
init_rate_limiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW
)

app = FastAPI(title="ProxiBase", version="1.0.0")

# Mount static files and templates
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# Create directories if they don't exist
os.makedirs(static_path, exist_ok=True)
os.makedirs(template_path, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=template_path)


# Health check - must be before routers
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include admin router (handles /admin, /login, /logout paths)
app.include_router(admin_router)

# Include proxy router last (catch-all for mirror domains)
app.include_router(proxy_router)
