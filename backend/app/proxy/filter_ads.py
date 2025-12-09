"""
ProxiBase Ads/Analytics Filter - Phase 6
Cleans HTML of ads/analytics and optionally injects custom content
"""

from bs4 import BeautifulSoup
from typing import Dict
import re


# Common ad/analytics patterns to match in src attributes
AD_PATTERNS = [
    'doubleclick',
    'googlesyndication',
    'adsystem',
    'adservice',
    'adsbygoogle',
    'googletagmanager',
    'google-analytics',
    'googleadservices',
]

# Patterns to match in inline script content
INLINE_SCRIPT_PATTERNS = [
    'gtag(',
    'ga(',
    'GoogleAnalyticsObject',
    'fbq(',
    '_gaq',
    'dataLayer',
]


def clean_html(html: str, site_config: Dict) -> str:
    """
    Remove ads and analytics from HTML content.
    
    If both remove_ads and remove_analytics are False, returns HTML unchanged.
    Otherwise, removes:
    - <script> and <iframe> tags with ad/analytics patterns in src
    - Inline <script> tags containing tracking code
    
    Args:
        html: The HTML content to clean
        site_config: Effective configuration dict with keys:
                     - remove_ads (bool)
                     - remove_analytics (bool)
    
    Returns:
        Cleaned HTML string
    """
    # Check if we should do any cleaning
    remove_ads = site_config.get('remove_ads', False)
    remove_analytics = site_config.get('remove_analytics', False)
    
    # If both are False, return unchanged
    if not remove_ads and not remove_analytics:
        return html
    
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove <script> tags with ad/analytics patterns in src
    for script in soup.find_all('script', src=True):
        src = script.get('src', '').lower()
        
        # Check if src matches any ad/analytics pattern
        should_remove = False
        for pattern in AD_PATTERNS:
            if pattern in src:
                should_remove = True
                break
        
        if should_remove:
            script.decompose()  # Remove from tree
    
    # Remove <script> tags with inline tracking code
    for script in soup.find_all('script'):
        # Skip if it has src (already handled above)
        if script.get('src'):
            continue
        
        # Get script content
        script_content = script.string
        if not script_content:
            continue
        
        # Check if content matches any inline script pattern
        should_remove = False
        for pattern in INLINE_SCRIPT_PATTERNS:
            if pattern in script_content:
                should_remove = True
                break
        
        if should_remove:
            script.decompose()
    
    # Remove <iframe> tags with ad/analytics patterns in src
    for iframe in soup.find_all('iframe', src=True):
        src = iframe.get('src', '').lower()
        
        # Check if src matches any ad/analytics pattern
        should_remove = False
        for pattern in AD_PATTERNS:
            if pattern in src:
                should_remove = True
                break
        
        if should_remove:
            iframe.decompose()
    
    # Return cleaned HTML
    return str(soup)


def inject_ads_and_trackers(html: str, site_config: Dict) -> str:
    """
    Inject custom ads and tracking scripts into HTML.
    
    If inject_ads is True and custom_ad_html is not empty:
    - Inject custom_ad_html before </body>
    
    If custom_tracker_js is not empty:
    - Inject <script>custom_tracker_js</script> before </body> or in <head>
    
    Args:
        html: The HTML content to inject into
        site_config: Effective configuration dict with keys:
                     - inject_ads (bool)
                     - custom_ad_html (str)
                     - custom_tracker_js (str)
    
    Returns:
        HTML string with injected content
    """
    inject_ads = site_config.get('inject_ads', False)
    custom_ad_html = site_config.get('custom_ad_html', '')
    custom_tracker_js = site_config.get('custom_tracker_js', '')
    
    # If nothing to inject, return unchanged
    if not custom_ad_html and not custom_tracker_js:
        return html
    
    # Parse HTML
    soup = BeautifulSoup(html, 'lxml')
    
    # Find the body tag
    body = soup.find('body')
    
    # Inject custom ad HTML before </body> if enabled
    if inject_ads and custom_ad_html:
        if body:
            # Create a new tag from the custom HTML
            ad_soup = BeautifulSoup(custom_ad_html, 'lxml')
            # Extract the body content if it was wrapped
            if ad_soup.body:
                for child in ad_soup.body.children:
                    if child.name or (isinstance(child, str) and child.strip()):
                        body.append(child)
            else:
                # Just append the parsed content
                for child in ad_soup.children:
                    if child.name or (isinstance(child, str) and child.strip()):
                        body.append(child)
    
    # Inject custom tracker JS before </body> or in <head>
    if custom_tracker_js:
        # Create script tag
        script_tag = soup.new_tag('script')
        script_tag.string = custom_tracker_js
        
        # Try to inject before </body>
        if body:
            body.append(script_tag)
        else:
            # Fallback: inject in <head>
            head = soup.find('head')
            if head:
                head.append(script_tag)
            else:
                # Last resort: just append to html
                if soup.html:
                    soup.html.append(script_tag)
    
    # Return modified HTML
    return str(soup)
