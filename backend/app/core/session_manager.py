"""
Session Management for Cookie Jar Feature (Phase 8)

Handles creation and verification of signed session cookies (px_session_id).
"""

import secrets
import hmac
import hashlib
from typing import Optional
from app.config import settings

# Cookie name for session identification
SESSION_COOKIE_NAME = "px_session_id"


def generate_session_id() -> str:
    """
    Generate a random session ID.
    
    Returns:
        A URL-safe random string (32 bytes = 64 hex chars)
    """
    return secrets.token_urlsafe(32)


def sign_session_id(session_id: str) -> str:
    """
    Sign a session ID using HMAC-SHA256 with SECRET_KEY.
    
    Format: {session_id}.{signature}
    
    Args:
        session_id: The session ID to sign
        
    Returns:
        Signed session ID string
    """
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        session_id.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{session_id}.{signature}"


def verify_session_id(signed_session_id: str) -> Optional[str]:
    """
    Verify a signed session ID and extract the session ID.
    
    Args:
        signed_session_id: The signed session ID from cookie
        
    Returns:
        The session ID if valid, None otherwise
    """
    try:
        if '.' not in signed_session_id:
            return None
        
        session_id, provided_signature = signed_session_id.rsplit('.', 1)
        
        # Compute expected signature
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            session_id.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Constant-time comparison
        if hmac.compare_digest(expected_signature, provided_signature):
            return session_id
        
        return None
    except Exception:
        return None


def create_signed_session_cookie() -> str:
    """
    Create a new signed session cookie value.
    
    Returns:
        Signed session cookie value ready to be set
    """
    session_id = generate_session_id()
    return sign_session_id(session_id)
