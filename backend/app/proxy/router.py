"""
ProxiBase Proxy Router - Phase 8
Core proxy functionality with cookie jar and session support
"""

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
import ipaddress
import socket
import time
import logging
from typing import Optional, Tuple

from app.db.session import get_db
from app.models.site import Site
from app.models.global_config import GlobalConfig
from app.core.url_utils import build_origin_url, encode_external_url_for_mirror
from app.core.domain_mapping import map_mirror_host_to_origin_host
from app.core.config_helper import get_effective_config
from app.config import settings
from app.proxy.rewriter import rewrite_html
from app.proxy.filter_ads import clean_html, inject_ads_and_trackers
from app.core.session_manager import (
    SESSION_COOKIE_NAME,
    create_signed_session_cookie,
    verify_session_id
)
from app.core.cookie_manager import (
    parse_set_cookie_headers,
    store_cookies,
    get_cookies,
    build_cookie_header
)
# Phase 9: Import security and rate limiting
from app.core.security import is_safe_origin_url
from app.core.rate_limiter import get_rate_limiter

# Phase 9: Set up logger
logger = logging.getLogger("proxibase")

router = APIRouter()

# Headers to strip from origin responses
STRIP_HEADERS = {
    'set-cookie',
    'content-security-policy',
    'strict-transport-security',
    'x-frame-options',
    'access-control-allow-origin',
    'content-encoding',  # We'll handle encoding ourselves
    'transfer-encoding',  # FastAPI handles this
    'content-length',  # Will be recalculated
}

# Headers to forward from client to origin
FORWARD_HEADERS = {
    'user-agent',
    'accept',
    'accept-language',
    'accept-encoding',
    'content-type',
    'referer',
}


async def find_site_by_host(host: str, db: AsyncSession) -> Optional[Site]:
    """
    Find a Site by matching the host against mirror_root.
    Supports exact match and subdomain matching.
    
    Examples:
        host='mirror.com' matches mirror_root='mirror.com'
        host='xyz.mirror.com' matches mirror_root='mirror.com'
        host='a.b.mirror.com' matches mirror_root='mirror.com'
    
    Args:
        host: The incoming host header
        db: Database session
    
    Returns:
        Site instance or None
    """
    # Remove port if present
    host_without_port = host.split(':')[0] if ':' in host else host
    
    # Get all enabled sites
    result = await db.execute(select(Site).where(Site.enabled == True))
    sites = result.scalars().all()
    
    # Try to find a matching site
    # First try exact match, then try subdomain match
    for site in sites:
        mirror_root = site.mirror_root
        
        # Exact match
        if host_without_port == mirror_root:
            return site
        
        # Subdomain match: host ends with .mirror_root
        if host_without_port.endswith('.' + mirror_root):
            return site
    
    return None


def normalize_redirect_location(location: str, origin_url: str) -> str:
    """
    Normalize a redirect Location header to an absolute URL.
    
    Args:
        location: The Location header value (may be relative)
        origin_url: The origin URL that returned the redirect
    
    Returns:
        Absolute URL
    """
    if not location:
        return location
    
    # If already absolute, return as-is
    if location.startswith('http://') or location.startswith('https://'):
        return location
    
    # Make relative URL absolute
    return urljoin(origin_url, location)


def map_origin_url_to_mirror(
    origin_url: str,
    site: Site,
    mirror_host: str
) -> str:
    """
    Map an origin URL to a mirror URL.
    
    Handles:
    1. Same domain or subdomain of source_root -> map via host mapping
    2. External domain -> encode as /external.host/path
    
    Args:
        origin_url: The origin URL to map
        site: The Site configuration
        mirror_host: The incoming mirror host
    
    Returns:
        Mirror URL
    """
    parsed = urlparse(origin_url)
    origin_host = parsed.hostname or ''
    origin_path = parsed.path or '/'
    query = parsed.query
    fragment = parsed.fragment
    
    # Check if origin_host is same as or subdomain of source_root
    source_root = site.source_root
    is_same_domain = (
        origin_host == source_root or
        origin_host.endswith('.' + source_root)
    )
    
    if is_same_domain:
        # Map via reverse domain mapping
        # origin_host -> mirror_host transformation
        # e.g., xyz.source.com -> xyz.mirror.com
        
        if origin_host == source_root:
            # Exact match: source.com -> mirror.com
            new_host = site.mirror_root
        else:
            # Subdomain: xyz.source.com -> xyz.mirror.com
            # Extract subdomain prefix
            subdomain_prefix = origin_host[:-len(source_root) - 1]
            new_host = f"{subdomain_prefix}.{site.mirror_root}"
        
        # Build mirror URL
        scheme = 'https'  # Always use HTTPS for mirror
        path_with_query = origin_path
        if query:
            path_with_query += '?' + query
        if fragment:
            path_with_query += '#' + fragment
        
        return f"{scheme}://{new_host}{path_with_query}"
    else:
        # External domain: encode as /external.host/path
        encoded_path = encode_external_url_for_mirror(
            site.mirror_root,
            origin_host,
            origin_path
        )
        
        # Add query and fragment
        if query:
            encoded_path += '?' + query
        if fragment:
            encoded_path += '#' + fragment
        
        # Use the same mirror host that was used in the request
        scheme = 'https'
        return f"{scheme}://{mirror_host}{encoded_path}"


async def proxy_request(
    request: Request,
    site: Site,
    origin_url: str,
    db: AsyncSession,
    response_to_client: Optional[Response] = None
) -> Response:
    """
    Proxy a request to the origin and return the response.
    
    Phase 8 Enhancement: Cookie jar and session support
    
    Handles:
    - Session cookie management (px_session_id)
    - Cookie jar storage and retrieval
    - Forwarding request with appropriate headers
    - Redirect interception and rewriting
    - Header filtering
    - Response streaming
    
    Args:
        request: The incoming FastAPI request
        site: The Site configuration
        origin_url: The origin URL to fetch
        db: Database session
        response_to_client: Optional Response object to set cookies on
    
    Returns:
        FastAPI Response
    """
    # Get global config for effective config merging
    global_config_result = await db.execute(select(GlobalConfig).where(GlobalConfig.id == 1))
    global_config = global_config_result.scalar_one_or_none()
    
    # If no global config exists, create default
    if not global_config:
        global_config = GlobalConfig(id=1)
        db.add(global_config)
        await db.commit()
        await db.refresh(global_config)
    
    # Get effective configuration
    effective_config = get_effective_config(site, global_config)
    
    # === PHASE 8: SESSION MANAGEMENT ===
    session_id = None
    new_session_created = False
    
    if effective_config.get('session_mode') == 'cookie_jar':
        # Check for existing session cookie
        signed_session_id = request.cookies.get(SESSION_COOKIE_NAME)
        
        if signed_session_id:
            # Verify existing session
            session_id = verify_session_id(signed_session_id)
        
        if not session_id:
            # Create new session
            signed_session_id = create_signed_session_cookie()
            session_id = verify_session_id(signed_session_id)
            new_session_created = True
    
    # Prepare headers to forward
    forward_headers = {}
    for header_name in FORWARD_HEADERS:
        header_value = request.headers.get(header_name)
        if header_value:
            forward_headers[header_name] = header_value
    
    # Override Host header with origin host
    origin_parsed = urlparse(origin_url)
    forward_headers['Host'] = origin_parsed.hostname
    
    # === PHASE 8: REFERER REWRITING ===
    # Rewrite Referer header to origin domain
    if 'referer' in forward_headers:
        referer = forward_headers['referer']
        # Parse referer and rewrite host to origin
        referer_parsed = urlparse(referer)
        if referer_parsed.hostname:
            # Map mirror host back to origin host
            # This is a simplified approach - just use origin host
            forward_headers['referer'] = origin_url
    
    # === PHASE 8: COOKIE JAR - INJECT COOKIES ===
    if session_id and effective_config.get('session_mode') == 'cookie_jar':
        # Retrieve stored cookies for this origin
        origin_host = origin_parsed.hostname
        stored_cookies = await get_cookies(db, site.id, session_id, origin_host)
        
        if stored_cookies:
            # Build Cookie header
            cookie_header = build_cookie_header(stored_cookies)
            if cookie_header:
                forward_headers['Cookie'] = cookie_header
    
    # Get request body if present
    body = None
    if request.method in ('POST', 'PUT', 'PATCH'):
        body = await request.body()
    
    # Phase 9: Start timing for latency measurement
    start_time = time.time()
    
    # Make request to origin with redirect following disabled
    # Phase 9: Use configurable timeout
    timeout_seconds = settings.REQUEST_TIMEOUT
    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout_seconds) as client:
        try:
            response = await client.request(
                method=request.method,
                url=origin_url,
                headers=forward_headers,
                content=body,
                params=None,  # Query params already in origin_url
            )
        except httpx.RequestError as e:
            # Phase 9: Log error
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Error fetching origin: {str(e)}",
                extra={
                    'client_ip': request.client.host if request.client else 'unknown',
                    'mirror_host': request.headers.get('host', ''),
                    'origin_url': origin_url,
                    'status_code': 502,
                    'latency_ms': latency_ms,
                    'user_agent': request.headers.get('user-agent', '')
                }
            )
            # Return error response
            return Response(
                content=f"Error fetching origin: {str(e)}",
                status_code=502,
                media_type="text/plain"
            )
    
    # Phase 9: Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Phase 9: Check response size for non-media content
    content_type = response.headers.get('content-type', '')
    content_length = response.headers.get('content-length')
    max_size_bytes = settings.MAX_RESPONSE_SIZE_MB * 1024 * 1024
    
    # Only check size for non-media content
    is_media = any(media_type in content_type.lower() for media_type in [
        'image/', 'video/', 'audio/', 'application/octet-stream'
    ])
    
    if not is_media and content_length:
        if int(content_length) > max_size_bytes:
            logger.warning(
                f"Response size exceeds limit: {content_length} bytes",
                extra={
                    'client_ip': request.client.host if request.client else 'unknown',
                    'mirror_host': request.headers.get('host', ''),
                    'origin_url': origin_url,
                    'status_code': 413,
                    'latency_ms': latency_ms,
                }
            )
            return Response(
                content=f"Response too large: {int(content_length) / (1024*1024):.1f}MB exceeds {settings.MAX_RESPONSE_SIZE_MB}MB limit",
                status_code=413,
                media_type="text/plain"
            )
    
    # === PHASE 8: COOKIE JAR - STORE COOKIES ===
    if session_id and effective_config.get('session_mode') == 'cookie_jar':
        # Extract Set-Cookie headers from origin response
        set_cookie_headers = parse_set_cookie_headers(response.headers)
        
        if set_cookie_headers:
            # Store cookies in database
            origin_host = origin_parsed.hostname
            await store_cookies(db, site.id, session_id, origin_host, set_cookie_headers)
    
    # Handle redirects (3xx status codes)
    if 300 <= response.status_code < 400:
        location = response.headers.get('location')
        if location:
            # Normalize to absolute URL
            absolute_location = normalize_redirect_location(location, origin_url)
            
            # Map to mirror URL
            mirror_location = map_origin_url_to_mirror(
                absolute_location,
                site,
                request.headers.get('host', site.mirror_root)
            )
            
            # Return redirect with rewritten Location
            response_headers = {}
            response_headers['Location'] = mirror_location
            
            # Copy some safe headers
            for header_name in ['cache-control', 'expires']:
                if header_name in response.headers:
                    response_headers[header_name] = response.headers[header_name]
            
            redirect_response = Response(
                status_code=response.status_code,
                headers=response_headers
            )
            
            # === PHASE 8: SET SESSION COOKIE ===
            if new_session_created and session_id:
                redirect_response.set_cookie(
                    key=SESSION_COOKIE_NAME,
                    value=signed_session_id,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite='lax',
                    max_age=86400 * 30  # 30 days
                )
            
            # Phase 9: Log redirect
            logger.info(
                f"Proxy redirect: {origin_url} -> {mirror_location}",
                extra={
                    'client_ip': request.client.host if request.client else 'unknown',
                    'mirror_host': request.headers.get('host', ''),
                    'origin_url': origin_url,
                    'status_code': response.status_code,
                    'latency_ms': latency_ms,
                    'user_agent': request.headers.get('user-agent', '')
                }
            )
            
            return redirect_response
    
    # For non-redirect responses, filter headers and return content
    response_headers = {}
    for header_name, header_value in response.headers.items():
        header_lower = header_name.lower()
        if header_lower not in STRIP_HEADERS:
            response_headers[header_name] = header_value
    
    # Get content type
    content_type = response.headers.get('content-type', '')
    
    # For HTML, rewrite links and return
    if 'text/html' in content_type.lower():
        # Decode HTML content
        html_content = response.content.decode('utf-8', errors='ignore')
        
        # Phase 6: HTML Processing Pipeline
        # Step 1: Clean ads/analytics from origin HTML
        cleaned_html = clean_html(html_content, effective_config)
        
        # Step 2: Rewrite URLs for mirror navigation
        rewritten_html = rewrite_html(
            html=cleaned_html,
            mirror_host=request.headers.get('host', site.mirror_root).split(':')[0],
            mirror_root=site.mirror_root,
            site_source_root=site.source_root,
            effective_config=effective_config,
            current_page_origin_url=origin_url
        )
        
        # Step 3: Inject custom ads/trackers
        final_html = inject_ads_and_trackers(rewritten_html, effective_config)
        
        html_response = Response(
            content=final_html,
            status_code=response.status_code,
            headers=response_headers,
            media_type=content_type
        )
        
        # === PHASE 8: SET SESSION COOKIE ===
        if new_session_created and session_id:
            html_response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=signed_session_id,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='lax',
                max_age=86400 * 30  # 30 days
            )
        
        # Phase 9: Log HTML response
        logger.info(
            f"Proxy HTML: {origin_url}",
            extra={
                'client_ip': request.client.host if request.client else 'unknown',
                'mirror_host': request.headers.get('host', ''),
                'origin_url': origin_url,
                'status_code': response.status_code,
                'latency_ms': latency_ms,
                'user_agent': request.headers.get('user-agent', '')
            }
        )
        
        return html_response
    
    # For other content types, stream the response
    other_response = Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers
    )
    
    # === PHASE 8: SET SESSION COOKIE ===
    if new_session_created and session_id:
        other_response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=signed_session_id,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='lax',
            max_age=86400 * 30  # 30 days
        )
    
    # Phase 9: Log other response
    logger.info(
        f"Proxy content: {origin_url}",
        extra={
            'client_ip': request.client.host if request.client else 'unknown',
            'mirror_host': request.headers.get('host', ''),
            'origin_url': origin_url,
            'status_code': response.status_code,
            'latency_ms': latency_ms,
            'user_agent': request.headers.get('user-agent', '')
        }
    )
    
    return other_response


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy_handler(
    request: Request,
    path: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Main proxy handler for all non-admin requests.
    
    Phase 9: Added rate limiting, SSRF protection, and structured logging.
    Matches incoming host against Site mirror_root and proxies to source_root.
    """
    host = request.headers.get('host', '')
    client_ip = request.client.host if request.client else 'unknown'
    
    # Phase 9: Rate limiting check
    if settings.ENABLE_RATE_LIMITING:
        rate_limiter = get_rate_limiter()
        if rate_limiter:
            is_allowed, remaining = rate_limiter.is_allowed(client_ip)
            
            if not is_allowed:
                retry_after = rate_limiter.get_retry_after(client_ip)
                logger.warning(
                    f"Rate limit exceeded for {client_ip}",
                    extra={
                        'client_ip': client_ip,
                        'mirror_host': host,
                        'status_code': 429,
                    }
                )
                return Response(
                    content=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    status_code=429,
                    headers={
                        'Retry-After': str(retry_after),
                        'X-RateLimit-Limit': str(settings.RATE_LIMIT_REQUESTS),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(retry_after)
                    }
                )
    
    # If host is admin host, don't proxy (return 404)
    if host == settings.ADMIN_HOST or host.startswith('0.0.0.0') or host.startswith('localhost'):
        return Response(
            content="Not found",
            status_code=404
        )
    
    # Find matching site
    site = await find_site_by_host(host, db)
    if not site:
        logger.warning(
            f"No site configured for host: {host}",
            extra={'client_ip': client_ip, 'mirror_host': host, 'status_code': 404}
        )
        return Response(
            content=f"No site configured for host: {host}",
            status_code=404
        )
    
    # Build origin URL
    mirror_path = '/' + path if path else '/'
    
    # Add query string if present
    if request.url.query:
        mirror_path += '?' + request.url.query
    
    origin_url = build_origin_url(
        mirror_host=host.split(':')[0],
        mirror_path=mirror_path,
        site_source_root=site.source_root,
        mirror_root=site.mirror_root
    )
    
    # Phase 9: SSRF protection with detailed reason
    is_safe, reason = is_safe_origin_url(origin_url)
    if not is_safe:
        logger.warning(
            f"SSRF blocked: {reason}",
            extra={
                'client_ip': client_ip,
                'mirror_host': host,
                'origin_url': origin_url,
                'status_code': 403
            }
        )
        return Response(
            content=f"Blocked: {reason}",
            status_code=403
        )
    
    # Proxy the request
    return await proxy_request(request, site, origin_url, db)
