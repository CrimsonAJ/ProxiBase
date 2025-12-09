"""
ProxiBase HTML Rewriter - Phase 7
Rewrites HTML content to keep navigation within mirror domains
Includes JS redirect handling and CSS url() rewriting
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict, Set
import re
from app.models.site import Site


# Media and download file extensions that should not be rewritten
MEDIA_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp',
    # Videos
    '.mp4', '.mkv', '.avi', '.mov', '.m3u8', '.webm', '.flv', '.wmv',
    # Audio
    '.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a',
    # Downloads/Archives
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Executables
    '.apk', '.exe', '.dmg', '.deb', '.rpm',
    # Fonts
    '.ttf', '.woff', '.woff2', '.eot', '.otf',
}


def is_media_url(url: str) -> bool:
    """
    Check if a URL points to a media or download resource based on file extension.
    
    Args:
        url: The URL to check
    
    Returns:
        True if it's a media/download URL, False otherwise
    """
    if not url:
        return False
    
    # Parse URL and get path
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    # Check if path ends with a media extension
    for ext in MEDIA_EXTENSIONS:
        if path.endswith(ext):
            return True
    
    return False


def make_absolute_url(url: str, base_url: str) -> str:
    """
    Convert a relative URL to an absolute URL using the base URL.
    
    Args:
        url: The URL to convert (may be relative or absolute)
        base_url: The base URL (origin page URL)
    
    Returns:
        Absolute URL
    """
    if not url or url.startswith('data:') or url.startswith('javascript:') or url.startswith('mailto:') or url.startswith('#'):
        return url
    
    # If already absolute, return as-is
    if url.startswith('http://') or url.startswith('https://') or url.startswith('//'):
        # Handle protocol-relative URLs
        if url.startswith('//'):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"
        return url
    
    # Make relative URL absolute
    return urljoin(base_url, url)


def url_belongs_to_domain(url: str, domain: str) -> bool:
    """
    Check if a URL belongs to a domain or its subdomains.
    
    Args:
        url: The absolute URL to check
        domain: The root domain (e.g., 'example.com')
    
    Returns:
        True if URL belongs to domain or subdomain, False otherwise
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    if not hostname:
        return False
    
    # Exact match
    if hostname == domain:
        return True
    
    # Subdomain match
    if hostname.endswith('.' + domain):
        return True
    
    return False


def map_origin_host_to_mirror_host(origin_host: str, source_root: str, mirror_root: str) -> str:
    """
    Map an origin host to its mirror host equivalent.
    
    Rules:
    - source.com -> mirror.com
    - xyz.source.com -> xyz.mirror.com
    
    Args:
        origin_host: The origin host to map
        source_root: The source root domain
        mirror_root: The mirror root domain
    
    Returns:
        The mirror host
    """
    if origin_host == source_root:
        return mirror_root
    
    # Check if it's a subdomain of source_root
    if origin_host.endswith('.' + source_root):
        # Extract subdomain prefix
        subdomain_prefix = origin_host[:-len(source_root) - 1]
        return f"{subdomain_prefix}.{mirror_root}"
    
    # Not a subdomain, return as-is (shouldn't happen in normal flow)
    return origin_host


def encode_external_url_path(external_host: str, external_path: str) -> str:
    """
    Encode an external URL as a path for the mirror.
    
    Converts https://abc.external.com/path/to into:
    /abc.external.com/path/to
    
    Args:
        external_host: The external host
        external_path: The external path
    
    Returns:
        Encoded path
    """
    if not external_path.startswith('/'):
        external_path = '/' + external_path
    
    return f"/{external_host}{external_path}"


def rewrite_url(
    url: str,
    current_page_origin_url: str,
    mirror_host: str,
    mirror_root: str,
    site_source_root: str,
    effective_config: Dict,
) -> str:
    """
    Rewrite a single URL according to mirror mapping rules.
    
    Rules:
    1. Convert to absolute URL
    2. If media/download based on extension, leave as-is (respect media_policy)
    3. If same domain or subdomain of source_root:
       - Map to mirror equivalent (source.com/path -> mirror.com/path)
    4. If external domain:
       - Encode as mirror.com/external.host/path
    
    Args:
        url: The URL to rewrite
        current_page_origin_url: The origin URL of the current page
        mirror_host: The mirror host serving the request
        mirror_root: The mirror root domain
        site_source_root: The source root domain
        effective_config: Effective configuration dict
    
    Returns:
        Rewritten URL
    """
    # Skip special URLs
    if not url or url.startswith('data:') or url.startswith('javascript:') or url.startswith('mailto:') or url.startswith('#'):
        return url
    
    # Make URL absolute
    absolute_url = make_absolute_url(url, current_page_origin_url)
    
    # Check if it's a media URL
    if is_media_url(absolute_url):
        # Based on media_policy, decide whether to rewrite
        media_policy = effective_config.get('media_policy', 'proxy')
        
        if media_policy == 'bypass':
            # Leave pointing to origin (don't rewrite)
            return absolute_url
        # For 'proxy' or 'size_limited', we continue to rewrite
    
    # Parse the absolute URL
    parsed = urlparse(absolute_url)
    origin_host = parsed.hostname
    origin_path = parsed.path or '/'
    query = parsed.query
    fragment = parsed.fragment
    
    if not origin_host:
        return url
    
    # Check if origin_host is same domain or subdomain of source_root
    is_same_domain = url_belongs_to_domain(absolute_url, site_source_root)
    
    if is_same_domain:
        # Map via host transformation
        new_mirror_host = map_origin_host_to_mirror_host(origin_host, site_source_root, mirror_root)
        
        # Build mirror URL
        scheme = 'https'
        path_with_query = origin_path
        if query:
            path_with_query += '?' + query
        if fragment:
            path_with_query += '#' + fragment
        
        return f"{scheme}://{new_mirror_host}{path_with_query}"
    else:
        # External domain: encode as /external.host/path
        # Check if we should proxy external domains
        proxy_external = effective_config.get('proxy_external_domains', True)
        
        if not proxy_external:
            # Don't rewrite, leave pointing to origin
            return absolute_url
        
        encoded_path = encode_external_url_path(origin_host, origin_path)
        
        # Add query and fragment
        if query:
            encoded_path += '?' + query
        if fragment:
            encoded_path += '#' + fragment
        
        # Use the mirror_root (not mirror_host, to avoid subdomain confusion)
        scheme = 'https'
        return f"{scheme}://{mirror_root}{encoded_path}"


def rewrite_js_redirects(
    js_content: str,
    current_page_origin_url: str,
    mirror_host: str,
    mirror_root: str,
    site_source_root: str,
    effective_config: Dict,
) -> str:
    """
    Rewrite JavaScript redirect patterns to use mirror URLs.
    
    Handles these patterns:
    - window.location.href = "URL"
    - location.href = "URL"
    - location.replace("URL")
    - location = "URL"
    
    Args:
        js_content: The JavaScript content (inline script)
        current_page_origin_url: The origin URL of the current page
        mirror_host: The mirror host serving the request
        mirror_root: The mirror root domain
        site_source_root: The source root domain
        effective_config: Effective configuration dict
    
    Returns:
        Rewritten JavaScript content
    """
    if not js_content:
        return js_content
    
    # Pattern 1: window.location.href = "URL" or window.location.href = 'URL'
    pattern1 = r'window\.location\.href\s*=\s*["\']([^"\']+)["\']'
    
    # Pattern 2: location.href = "URL" or location.href = 'URL'
    pattern2 = r'(?<!window\.)location\.href\s*=\s*["\']([^"\']+)["\']'
    
    # Pattern 3: location.replace("URL") or location.replace('URL')
    pattern3 = r'location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)'
    
    # Pattern 4: location = "URL" or location = 'URL' (but not window.location)
    pattern4 = r'(?<!window\.)location\s*=\s*["\']([^"\']+)["\']'
    
    def replace_url(match):
        """Helper function to replace matched URL"""
        original_url = match.group(1)
        
        # Rewrite the URL
        rewritten_url = rewrite_url(
            original_url,
            current_page_origin_url,
            mirror_host,
            mirror_root,
            site_source_root,
            effective_config
        )
        
        # Return the full match with rewritten URL, preserving quote style
        full_match = match.group(0)
        if '"' in full_match:
            return full_match.replace(original_url, rewritten_url)
        else:
            return full_match.replace(original_url, rewritten_url)
    
    # Apply all patterns
    js_content = re.sub(pattern1, replace_url, js_content)
    js_content = re.sub(pattern2, replace_url, js_content)
    js_content = re.sub(pattern3, replace_url, js_content)
    js_content = re.sub(pattern4, replace_url, js_content)
    
    return js_content


def rewrite_css_urls(
    css_content: str,
    current_page_origin_url: str,
    mirror_host: str,
    mirror_root: str,
    site_source_root: str,
    effective_config: Dict,
) -> str:
    """
    Rewrite url() patterns in CSS content.
    
    Rules:
    - If url() points to media (by extension), leave as origin
    - If url() points to pages (no extension or HTML-like), map through proxy
    
    Args:
        css_content: The CSS content
        current_page_origin_url: The origin URL of the current page
        mirror_host: The mirror host serving the request
        mirror_root: The mirror root domain
        site_source_root: The source root domain
        effective_config: Effective configuration dict
    
    Returns:
        Rewritten CSS content
    """
    if not css_content:
        return css_content
    
    # Pattern to match url() in CSS
    # Matches: url("..."), url('...'), url(...)
    pattern = r'url\s*\(\s*["\']?([^"\')]+)["\']?\s*\)'
    
    def replace_css_url(match):
        """Helper function to replace matched CSS URL"""
        original_url = match.group(1).strip()
        
        # Skip data URLs and special URLs
        if original_url.startswith('data:') or original_url.startswith('#'):
            return match.group(0)
        
        # Make absolute
        absolute_url = make_absolute_url(original_url, current_page_origin_url)
        
        # Check if it's a media URL
        if is_media_url(absolute_url):
            # For media, respect media_policy
            media_policy = effective_config.get('media_policy', 'proxy')
            if media_policy == 'bypass':
                # Leave pointing to origin
                return match.group(0)
        
        # Rewrite the URL
        rewritten_url = rewrite_url(
            original_url,
            current_page_origin_url,
            mirror_host,
            mirror_root,
            site_source_root,
            effective_config
        )
        
        # Return with proper CSS url() format
        # Preserve quote style from original
        full_match = match.group(0)
        if '"' in full_match:
            return f'url("{rewritten_url}")'
        elif "'" in full_match:
            return f"url('{rewritten_url}')"
        else:
            return f'url({rewritten_url})'
    
    # Apply pattern
    css_content = re.sub(pattern, replace_css_url, css_content)
    
    return css_content



def rewrite_html(
    html: str,
    mirror_host: str,
    mirror_root: str,
    site_source_root: str,
    effective_config: Dict,
    current_page_origin_url: str,
) -> str:
    """
    Rewrite HTML content to transform URLs for mirror navigation.
    
    Phase 7: Includes JS redirect and CSS url() rewriting
    
    Rewrites these attributes:
    - <a href>
    - <form action>
    - <iframe src>
    - <link href>
    - <script src>
    - <img src> (optionally, based on media_policy)
    - <source src> (for video/audio)
    - <video src>
    - <audio src>
    
    Phase 7 additions:
    - Inline <script> tags: JS redirect patterns (window.location, location.href, etc.)
    - <style> tags: CSS url() patterns
    - style attributes: CSS url() patterns
    
    Args:
        html: The HTML content to rewrite
        mirror_host: The mirror host serving the request
        mirror_root: The mirror root domain
        site_source_root: The source root domain
        effective_config: Effective configuration dict
        current_page_origin_url: The origin URL of the current page
    
    Returns:
        Rewritten HTML
    """
    if not html:
        return html
    
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Helper function to rewrite a URL
    def rewrite(url: str) -> str:
        return rewrite_url(
            url,
            current_page_origin_url,
            mirror_host,
            mirror_root,
            site_source_root,
            effective_config
        )
    
    # Rewrite <a href>
    for tag in soup.find_all('a', href=True):
        tag['href'] = rewrite(tag['href'])
    
    # Rewrite <form action>
    for tag in soup.find_all('form', action=True):
        tag['action'] = rewrite(tag['action'])
    
    # Rewrite <iframe src>
    for tag in soup.find_all('iframe', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <link href> (stylesheets, icons, etc.)
    for tag in soup.find_all('link', href=True):
        tag['href'] = rewrite(tag['href'])
    
    # Rewrite <script src>
    for tag in soup.find_all('script', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <img src> (based on media_policy)
    for tag in soup.find_all('img', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <img srcset> (responsive images)
    for tag in soup.find_all('img', srcset=True):
        # srcset format: "url1 1x, url2 2x" or "url1 100w, url2 200w"
        srcset = tag['srcset']
        srcset_parts = []
        for part in srcset.split(','):
            part = part.strip()
            if ' ' in part:
                url_part, descriptor = part.rsplit(' ', 1)
                rewritten_url = rewrite(url_part.strip())
                srcset_parts.append(f"{rewritten_url} {descriptor}")
            else:
                srcset_parts.append(rewrite(part))
        tag['srcset'] = ', '.join(srcset_parts)
    
    # Rewrite <source src> (for <video> and <audio>)
    for tag in soup.find_all('source', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <video src>
    for tag in soup.find_all('video', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <audio src>
    for tag in soup.find_all('audio', src=True):
        tag['src'] = rewrite(tag['src'])
    
    # Rewrite <base href> (important for relative URLs)
    for tag in soup.find_all('base', href=True):
        tag['base'] = rewrite(tag['href'])
    
    # Phase 7: JS and CSS URL rewriting
    
    # Rewrite inline JavaScript for redirect patterns
    if effective_config.get('rewrite_js_redirects', False):
        for script_tag in soup.find_all('script'):
            # Only process inline scripts (no src attribute)
            if not script_tag.get('src') and script_tag.string:
                original_js = script_tag.string
                rewritten_js = rewrite_js_redirects(
                    original_js,
                    current_page_origin_url,
                    mirror_host,
                    mirror_root,
                    site_source_root,
                    effective_config
                )
                if rewritten_js != original_js:
                    script_tag.string = rewritten_js
    
    # Rewrite inline CSS <style> tags
    for style_tag in soup.find_all('style'):
        if style_tag.string:
            original_css = style_tag.string
            rewritten_css = rewrite_css_urls(
                original_css,
                current_page_origin_url,
                mirror_host,
                mirror_root,
                site_source_root,
                effective_config
            )
            if rewritten_css != original_css:
                style_tag.string = rewritten_css
    
    # Rewrite inline style attributes
    for tag in soup.find_all(style=True):
        original_style = tag['style']
        if 'url(' in original_style:
            rewritten_style = rewrite_css_urls(
                original_style,
                current_page_origin_url,
                mirror_host,
                mirror_root,
                site_source_root,
                effective_config
            )
            if rewritten_style != original_style:
                tag['style'] = rewritten_style
    
    # Return the rewritten HTML
    # Use .decode() to get string, not .prettify() to preserve formatting
    return str(soup)
