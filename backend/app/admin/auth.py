from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Cookie, HTTPException, status
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session settings
SESSION_COOKIE_NAME = "admin_session"
SESSION_EXPIRE_HOURS = 24
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_session_token(username: str, role: str = "superadmin") -> str:
    """Create a signed session token (JWT).
    
    Args:
        username: The username
        role: The user role (default: "superadmin")
    
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    to_encode = {
        "sub": username,
        "role": role,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_session_token(token: str) -> Optional[dict]:
    """Verify and decode a session token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None


def verify_superadmin_credentials(username: str, password: str) -> bool:
    """Verify credentials against env-based superadmin.
    
    Args:
        username: Username to verify
        password: Plain password to verify
    
    Returns:
        True if credentials match env superadmin, False otherwise
    """
    return (
        username == settings.ADMIN_USERNAME and
        password == settings.ADMIN_PASSWORD
    )


def get_current_admin(admin_session: Optional[str] = Cookie(None)) -> dict:
    """Dependency to get current admin from session cookie.
    
    Args:
        admin_session: Session cookie value
    
    Returns:
        User info dict
    
    Raises:
        HTTPException: If not authenticated
    """
    if not admin_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_info = verify_session_token(admin_session)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return user_info
