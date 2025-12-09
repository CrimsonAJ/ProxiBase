"""
ProxiBase Security Module - Phase 9
SSRF protection and target validation utilities
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple


def is_safe_origin_url(url: str) -> Tuple[bool, str]:
    """
    SSRF protection: Check if the origin URL is safe to fetch.
    
    Blocks:
    - localhost, 127.0.0.0/8 (loopback)
    - 10.0.0.0/8 (private)
    - 172.16.0.0/12 (private)
    - 192.168.0.0/16 (private)
    - 169.254.0.0/16 (link-local)
    - Non-HTTP(S) schemes
    
    Args:
        url: The origin URL to check
    
    Returns:
        Tuple of (is_safe: bool, reason: str)
    """
    try:
        parsed = urlparse(url)
        
        # Only allow HTTP and HTTPS
        if parsed.scheme not in ('http', 'https'):
            return False, f"Invalid scheme: {parsed.scheme}. Only HTTP/HTTPS allowed"
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname"
        
        # Block localhost explicitly
        if hostname.lower() in ('localhost', '127.0.0.1', '::1'):
            return False, f"Blocked: localhost access not allowed"
        
        # Try to resolve and check if it's a private/reserved IP
        try:
            # Get IP address
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            
            # Check against specific blocked ranges
            if ip.is_loopback:
                return False, f"Blocked: loopback address {ip_str}"
            
            if ip.is_private:
                return False, f"Blocked: private IP address {ip_str}"
            
            if ip.is_reserved:
                return False, f"Blocked: reserved IP address {ip_str}"
            
            if ip.is_link_local:
                return False, f"Blocked: link-local address {ip_str}"
            
            # Additional explicit checks for the required ranges
            # 127.0.0.0/8
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network('127.0.0.0/8'):
                return False, f"Blocked: 127.0.0.0/8 range {ip_str}"
            
            # 10.0.0.0/8
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network('10.0.0.0/8'):
                return False, f"Blocked: 10.0.0.0/8 range {ip_str}"
            
            # 172.16.0.0/12
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network('172.16.0.0/12'):
                return False, f"Blocked: 172.16.0.0/12 range {ip_str}"
            
            # 192.168.0.0/16
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network('192.168.0.0/16'):
                return False, f"Blocked: 192.168.0.0/16 range {ip_str}"
            
            # 169.254.0.0/16
            if ipaddress.ip_address(ip_str) in ipaddress.ip_network('169.254.0.0/16'):
                return False, f"Blocked: 169.254.0.0/16 range {ip_str}"
                
        except (socket.gaierror, ValueError) as e:
            # If we can't resolve, allow it (will fail later in httpx)
            # This prevents DNS errors from blocking legitimate requests
            pass
        
        return True, "OK"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def validate_target_url(url: str) -> None:
    """
    Validate a target URL for SSRF protection.
    Raises an exception if the URL is not safe.
    
    Args:
        url: The URL to validate
    
    Raises:
        ValueError: If the URL is not safe
    """
    is_safe, reason = is_safe_origin_url(url)
    if not is_safe:
        raise ValueError(f"Unsafe URL: {reason}")
