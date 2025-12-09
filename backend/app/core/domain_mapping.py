def map_mirror_host_to_origin_host(mirror_host: str, mirror_root: str, source_root: str) -> str:
    """
    Maps a mirror host to its origin host.
    
    Rules:
    - If mirror_host equals mirror_root exactly, return source_root
    - If mirror_host ends with '.' + mirror_root, extract the subdomain prefix
      and prepend it to source_root
    
    Examples:
        mirror.com, mirror.com, source.com -> source.com
        xyz.abc.mirror.com, mirror.com, source.com -> xyz.abc.source.com
    
    Args:
        mirror_host: The incoming host (e.g., 'xyz.abc.mirror.com')
        mirror_root: The mirror root domain (e.g., 'mirror.com')
        source_root: The source root domain (e.g., 'source.com')
    
    Returns:
        The mapped origin host
    """
    # Exact match: mirror.com -> source.com
    if mirror_host == mirror_root:
        return source_root
    
    # Check if mirror_host ends with '.' + mirror_root
    suffix = '.' + mirror_root
    if mirror_host.endswith(suffix):
        # Extract subdomain prefix
        subdomain = mirror_host[:-len(suffix)]
        # Prepend to source_root
        return f"{subdomain}.{source_root}"
    
    # If no match, return mirror_host as-is (edge case)
    return mirror_host
