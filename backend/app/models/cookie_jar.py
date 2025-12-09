from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import Base


class CookieJar(Base):
    """Cookie storage model for per-user, per-origin cookie jars.
    
    Stores cookies from origin responses and makes them available
    for subsequent requests from the same session to the same origin.
    
    Each row represents all cookies for a specific combination of:
    - site_id: Which mirror site
    - session_id: Which user session (from px_session_id cookie)
    - origin_host: Which origin domain
    """
    __tablename__ = "cookie_jars"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)
    origin_host = Column(String(255), nullable=False, index=True)
    cookie_data = Column(Text, nullable=True)  # JSON string of cookies
    
    # Relationship to Site
    site = relationship("Site", backref="cookie_jars")
    
    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_cookie_jar_lookup', 'site_id', 'session_id', 'origin_host'),
    )
