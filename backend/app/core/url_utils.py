from app.core.domain_mapping import map_mirror_host_to_origin_host


def is_encoded_external_domain(path_segment: str) -> bool:
    """
    Check if a path segment looks like an encoded external domain.
    A segment is considered a domain if it contains at least one dot and no spaces.
    
    Args:
        path_segment: The first segment of the path
    
    Returns:
        True if it looks like a domain, False otherwise
    """
    return '.' in path_segment and ' ' not in path_segment


def build_origin_url(mirror_host: str, mirror_path: str, site_source_root: str, mirror_root: str = None) -> str:
    """
    Build the origin URL from mirror host and path.
    
    Rules:
    1. If the first path segment looks like a domain (external encoding),
       treat it as https://domain/rest/of/path
    2. Otherwise, map the mirror host to origin host and append the path
    
    Examples:
        mirror.com, /foo/bar, source.com -> https://source.com/foo/bar
        xyz.mirror.com, /abc, source.com -> https://xyz.source.com/abc
        mirror.com, /abc.external.com/path/to, source.com -> https://abc.external.com/path/to
    
    Args:
        mirror_host: The incoming mirror host
        mirror_path: The incoming path
        site_source_root: The source root domain
        mirror_root: The mirror root domain (defaults to mirror_host if not provided)
    
    Returns:
        The origin URL
    """
    # Ensure path starts with /
    if not mirror_path.startswith('/'):
        mirror_path = '/' + mirror_path
    
    # Split path into segments
    path_parts = mirror_path.lstrip('/').split('/', 1)
    
    if not path_parts or not path_parts[0]:
        # Empty path
        if mirror_root:
            origin_host = map_mirror_host_to_origin_host(mirror_host, mirror_root, site_source_root)
        else:
            origin_host = site_source_root
        return f"https://{origin_host}/"
    
    first_segment = path_parts[0]
    remaining_path = '/' + path_parts[1] if len(path_parts) > 1 else '/'
    
    # Check if first segment is an encoded external domain
    if is_encoded_external_domain(first_segment):
        # Decode external URL: /abc.external.com/path/to -> https://abc.external.com/path/to
        # If no remaining path, use '/' as default
        if remaining_path == '/':
            return f"https://{first_segment}/"
        return f"https://{first_segment}{remaining_path}"
    
    # Normal mirror mapping
    if mirror_root:
        origin_host = map_mirror_host_to_origin_host(mirror_host, mirror_root, site_source_root)
    else:
        origin_host = site_source_root
    
    return f"https://{origin_host}{mirror_path}"


def encode_external_url_for_mirror(mirror_root: str, external_host: str, external_path: str) -> str:
    """
    Encode an external URL for the mirror.
    
    Converts https://abc.external.com/path/to into a mirror path:
    /abc.external.com/path/to
    
    Args:
        mirror_root: The mirror root domain (not used in path encoding)
        external_host: The external host (e.g., 'abc.external.com')
        external_path: The external path (e.g., '/path/to')
    
    Returns:
        The encoded mirror path
    """
    # Ensure path starts with /
    if not external_path.startswith('/'):
        external_path = '/' + external_path
    
    # Encode as: /external_host/path
    return f"/{external_host}{external_path}"
