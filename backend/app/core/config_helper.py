from app.models.site import Site
from app.models.global_config import GlobalConfig


def get_effective_config(site: Site, global_config: GlobalConfig) -> dict:
    """
    Get the effective configuration for a site by merging site-specific
    config with global config defaults.
    
    Any None value in Site config falls back to GlobalConfig value.
    
    Args:
        site: The Site instance
        global_config: The GlobalConfig instance
    
    Returns:
        Dictionary with effective configuration
    """
    return {
        "proxy_subdomains": site.proxy_subdomains if site.proxy_subdomains is not None else global_config.proxy_subdomains,
        "proxy_external_domains": site.proxy_external_domains if site.proxy_external_domains is not None else global_config.proxy_external_domains,
        "rewrite_js_redirects": site.rewrite_js_redirects if site.rewrite_js_redirects is not None else global_config.rewrite_js_redirects,
        "remove_ads": site.remove_ads if site.remove_ads is not None else global_config.remove_ads,
        "inject_ads": site.inject_ads if site.inject_ads is not None else global_config.inject_ads,
        "remove_analytics": site.remove_analytics if site.remove_analytics is not None else global_config.remove_analytics,
        "media_policy": site.media_policy if site.media_policy is not None else global_config.media_policy,
        "session_mode": site.session_mode if site.session_mode is not None else global_config.session_mode,
        "custom_ad_html": site.custom_ad_html if site.custom_ad_html is not None else global_config.custom_ad_html,
        "custom_tracker_js": site.custom_tracker_js if site.custom_tracker_js is not None else global_config.custom_tracker_js,
    }
