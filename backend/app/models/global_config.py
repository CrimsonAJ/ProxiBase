from sqlalchemy import Column, Integer, Boolean, String, Text
from app.models.base import Base


class GlobalConfig(Base):
    """Global configuration model (single row, id=1).
    
    Provides default configuration values for all sites.
    """
    __tablename__ = "global_config"
    
    id = Column(Integer, primary_key=True, default=1)
    
    # Configuration defaults (non-nullable)
    proxy_subdomains = Column(Boolean, default=True, nullable=False)
    proxy_external_domains = Column(Boolean, default=True, nullable=False)
    rewrite_js_redirects = Column(Boolean, default=False, nullable=False)
    remove_ads = Column(Boolean, default=False, nullable=False)
    inject_ads = Column(Boolean, default=False, nullable=False)
    remove_analytics = Column(Boolean, default=False, nullable=False)
    media_policy = Column(String, default="proxy", nullable=False)  # "bypass", "proxy", "size_limited"
    session_mode = Column(String, default="stateless", nullable=False)  # "stateless", "cookie_jar"
    custom_ad_html = Column(Text, nullable=True)
    custom_tracker_js = Column(Text, nullable=True)
