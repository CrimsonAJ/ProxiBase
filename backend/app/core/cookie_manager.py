"""
Cookie Management for Cookie Jar Feature (Phase 8)

Handles parsing, storing, and retrieving cookies for the cookie jar.
"""

import json
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import urlparse

from app.models.cookie_jar import CookieJar


def parse_set_cookie_headers(headers: Dict[str, str]) -> List[str]:
    """
    Extract all Set-Cookie headers from response headers.
    
    httpx returns multi-value headers as a Headers object.
    We need to get all Set-Cookie headers.
    
    Args:
        headers: httpx response headers
        
    Returns:
        List of Set-Cookie header values
    """
    set_cookie_headers = []
    
    # httpx.Headers allows get_list() to get all values for a header
    if hasattr(headers, 'get_list'):
        set_cookie_headers = headers.get_list('set-cookie')
    else:
        # Fallback for dict-like headers
        if 'set-cookie' in headers:
            value = headers['set-cookie']
            if isinstance(value, list):
                set_cookie_headers = value
            else:
                set_cookie_headers = [value]
    
    return set_cookie_headers


def parse_cookie_header(cookie_string: str) -> Dict[str, str]:
    """
    Parse a Cookie header string into a dictionary.
    
    Args:
        cookie_string: Cookie header value (e.g., "name1=value1; name2=value2")
        
    Returns:
        Dictionary of cookie name -> value
    """
    cookies = {}
    if not cookie_string:
        return cookies
    
    for cookie in cookie_string.split(';'):
        cookie = cookie.strip()
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    return cookies


def build_cookie_header(cookies: Dict[str, str]) -> str:
    """
    Build a Cookie header string from a dictionary.
    
    Args:
        cookies: Dictionary of cookie name -> value
        
    Returns:
        Cookie header string (e.g., "name1=value1; name2=value2")
    """
    if not cookies:
        return ""
    
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


async def store_cookies(
    db: AsyncSession,
    site_id: int,
    session_id: str,
    origin_host: str,
    set_cookie_headers: List[str]
) -> None:
    """
    Store cookies from Set-Cookie headers into the cookie jar.
    
    Updates existing cookie jar entry or creates a new one.
    
    Args:
        db: Database session
        site_id: Site ID
        session_id: Session ID (unsigned)
        origin_host: Origin hostname
        set_cookie_headers: List of Set-Cookie header values
    """
    if not set_cookie_headers:
        return
    
    # Parse Set-Cookie headers to extract cookie names and values
    # Set-Cookie format: name=value; Path=/; Domain=.example.com; Secure; HttpOnly
    # We'll store just the name=value part
    cookies = {}
    
    for set_cookie in set_cookie_headers:
        # Extract the name=value part (before first semicolon)
        cookie_pair = set_cookie.split(';')[0].strip()
        if '=' in cookie_pair:
            name, value = cookie_pair.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    if not cookies:
        return
    
    # Look up existing cookie jar entry
    result = await db.execute(
        select(CookieJar).where(
            CookieJar.site_id == site_id,
            CookieJar.session_id == session_id,
            CookieJar.origin_host == origin_host
        )
    )
    cookie_jar = result.scalar_one_or_none()
    
    if cookie_jar:
        # Update existing entry - merge with existing cookies
        existing_cookies = {}
        if cookie_jar.cookie_data:
            try:
                existing_cookies = json.loads(cookie_jar.cookie_data)
            except json.JSONDecodeError:
                pass
        
        # Merge new cookies (overwrites existing with same name)
        existing_cookies.update(cookies)
        cookie_jar.cookie_data = json.dumps(existing_cookies)
    else:
        # Create new entry
        cookie_jar = CookieJar(
            site_id=site_id,
            session_id=session_id,
            origin_host=origin_host,
            cookie_data=json.dumps(cookies)
        )
        db.add(cookie_jar)
    
    await db.commit()


async def get_cookies(
    db: AsyncSession,
    site_id: int,
    session_id: str,
    origin_host: str
) -> Dict[str, str]:
    """
    Retrieve cookies from the cookie jar for a specific origin.
    
    Args:
        db: Database session
        site_id: Site ID
        session_id: Session ID (unsigned)
        origin_host: Origin hostname
        
    Returns:
        Dictionary of cookie name -> value
    """
    result = await db.execute(
        select(CookieJar).where(
            CookieJar.site_id == site_id,
            CookieJar.session_id == session_id,
            CookieJar.origin_host == origin_host
        )
    )
    cookie_jar = result.scalar_one_or_none()
    
    if not cookie_jar or not cookie_jar.cookie_data:
        return {}
    
    try:
        return json.loads(cookie_jar.cookie_data)
    except json.JSONDecodeError:
        return {}
