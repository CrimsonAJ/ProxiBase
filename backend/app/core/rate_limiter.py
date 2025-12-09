"""
ProxiBase Rate Limiter - Phase 9
Simple in-memory rate limiter per client IP
"""

import time
from collections import defaultdict
from typing import Dict, Tuple
from threading import Lock


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.
    Tracks requests per IP address within a time window.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # Store timestamps of requests per IP
        # Format: {ip: [timestamp1, timestamp2, ...]}
        self.request_log: Dict[str, list] = defaultdict(list)
        
        # Lock for thread safety
        self.lock = Lock()
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if a request from the given IP is allowed.
        
        Args:
            client_ip: The client IP address
        
        Returns:
            Tuple of (is_allowed: bool, remaining_requests: int)
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Get request history for this IP
            requests = self.request_log[client_ip]
            
            # Remove old requests outside the window
            self.request_log[client_ip] = [
                ts for ts in requests if ts > cutoff_time
            ]
            
            # Check if limit is exceeded
            current_count = len(self.request_log[client_ip])
            
            if current_count >= self.max_requests:
                # Rate limit exceeded
                return False, 0
            
            # Add current request timestamp
            self.request_log[client_ip].append(current_time)
            
            # Calculate remaining requests
            remaining = self.max_requests - (current_count + 1)
            
            return True, remaining
    
    def get_retry_after(self, client_ip: str) -> int:
        """
        Get the number of seconds until the client can retry.
        
        Args:
            client_ip: The client IP address
        
        Returns:
            Seconds until retry is allowed
        """
        with self.lock:
            requests = self.request_log.get(client_ip, [])
            
            if not requests:
                return 0
            
            # Oldest request in the window
            oldest_request = min(requests)
            current_time = time.time()
            
            # Time until oldest request expires
            retry_after = self.window_seconds - (current_time - oldest_request)
            
            return max(0, int(retry_after))
    
    def reset(self, client_ip: str = None):
        """
        Reset rate limit tracking.
        
        Args:
            client_ip: If provided, reset only for this IP. Otherwise reset all.
        """
        with self.lock:
            if client_ip:
                self.request_log.pop(client_ip, None)
            else:
                self.request_log.clear()
    
    def cleanup_old_entries(self):
        """
        Cleanup old entries to prevent memory bloat.
        Should be called periodically.
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            # Remove IPs with no recent requests
            ips_to_remove = []
            for ip, requests in self.request_log.items():
                # Filter old requests
                recent_requests = [ts for ts in requests if ts > cutoff_time]
                
                if not recent_requests:
                    ips_to_remove.append(ip)
                else:
                    self.request_log[ip] = recent_requests
            
            for ip in ips_to_remove:
                del self.request_log[ip]


# Global rate limiter instance
# Will be configured from settings
rate_limiter: InMemoryRateLimiter = None


def init_rate_limiter(max_requests: int, window_seconds: int):
    """
    Initialize the global rate limiter.
    
    Args:
        max_requests: Maximum requests per window
        window_seconds: Window size in seconds
    """
    global rate_limiter
    rate_limiter = InMemoryRateLimiter(max_requests, window_seconds)


def get_rate_limiter() -> InMemoryRateLimiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        InMemoryRateLimiter instance
    """
    return rate_limiter
