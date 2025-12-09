from sqlalchemy import Column, Integer, String, Boolean, Text
from app.models.base import Base


class Site(Base):
    """Site configuration model.
    
    Each site represents a mirror domain mapping to a source domain,
    with optional configuration overrides.
    """
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    mirror_root = Column(String, unique=True, nullable=False, index=True)
    source_root = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Configuration options (nullable for fallback to global defaults)
    proxy_subdomains = Column(Boolean, nullable=True)
    proxy_external_domains = Column(Boolean, nullable=True)
    rewrite_js_redirects = Column(Boolean, nullable=True)
    remove_ads = Column(Boolean, nullable=True)
    inject_ads = Column(Boolean, nullable=True)
    remove_analytics = Column(Boolean, nullable=True)
    media_policy = Column(String, nullable=True)  # "bypass", "proxy", "size_limited"
    session_mode = Column(String, nullable=True)  # "stateless", "cookie_jar"
    custom_ad_html = Column(Text, nullable=True)
    custom_tracker_js = Column(Text, nullable=True)
