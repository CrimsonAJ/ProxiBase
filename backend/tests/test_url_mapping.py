import pytest
from app.core.domain_mapping import map_mirror_host_to_origin_host
from app.core.url_utils import (
    build_origin_url,
    encode_external_url_for_mirror,
    is_encoded_external_domain,
)


class TestDomainMapping:
    """Test domain mapping utilities."""
    
    def test_exact_mirror_root_mapping(self):
        """Test exact match: mirror.com -> source.com"""
        result = map_mirror_host_to_origin_host(
            mirror_host="mirror.com",
            mirror_root="mirror.com",
            source_root="source.com"
        )
        assert result == "source.com"
    
    def test_subdomain_mapping_single(self):
        """Test single subdomain: xyz.mirror.com -> xyz.source.com"""
        result = map_mirror_host_to_origin_host(
            mirror_host="xyz.mirror.com",
            mirror_root="mirror.com",
            source_root="source.com"
        )
        assert result == "xyz.source.com"
    
    def test_subdomain_mapping_multiple(self):
        """Test multiple subdomains: xyz.abc.mirror.com -> xyz.abc.source.com"""
        result = map_mirror_host_to_origin_host(
            mirror_host="xyz.abc.mirror.com",
            mirror_root="mirror.com",
            source_root="source.com"
        )
        assert result == "xyz.abc.source.com"


class TestExternalDomainDetection:
    """Test external domain detection."""
    
    def test_is_external_domain_valid(self):
        """Test valid external domain detection."""
        assert is_encoded_external_domain("abc.external.com") is True
        assert is_encoded_external_domain("subdomain.example.org") is True
    
    def test_is_external_domain_invalid(self):
        """Test invalid external domain detection."""
        assert is_encoded_external_domain("foo") is False
        assert is_encoded_external_domain("abc") is False
        assert is_encoded_external_domain("has space.com") is False


class TestBuildOriginUrl:
    """Test building origin URLs from mirror requests."""
    
    def test_simple_path_exact_mirror(self):
        """Test mirror.com/foo -> https://source.com/foo"""
        result = build_origin_url(
            mirror_host="mirror.com",
            mirror_path="/foo",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://source.com/foo"
    
    def test_nested_path_exact_mirror(self):
        """Test mirror.com/foo/bar -> https://source.com/foo/bar"""
        result = build_origin_url(
            mirror_host="mirror.com",
            mirror_path="/foo/bar",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://source.com/foo/bar"
    
    def test_subdomain_with_path(self):
        """Test xyz.mirror.com/abc -> https://xyz.source.com/abc"""
        result = build_origin_url(
            mirror_host="xyz.mirror.com",
            mirror_path="/abc",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://xyz.source.com/abc"
    
    def test_multiple_subdomains_with_path(self):
        """Test xyz.abc.mirror.com/foo -> https://xyz.abc.source.com/foo"""
        result = build_origin_url(
            mirror_host="xyz.abc.mirror.com",
            mirror_path="/foo",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://xyz.abc.source.com/foo"
    
    def test_external_domain_encoding(self):
        """Test mirror.com/abc.external.com/path/to -> https://abc.external.com/path/to"""
        result = build_origin_url(
            mirror_host="mirror.com",
            mirror_path="/abc.external.com/path/to",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://abc.external.com/path/to"
    
    def test_external_domain_no_trailing_path(self):
        """Test mirror.com/abc.external.com -> https://abc.external.com/"""
        result = build_origin_url(
            mirror_host="mirror.com",
            mirror_path="/abc.external.com",
            site_source_root="source.com",
            mirror_root="mirror.com"
        )
        assert result == "https://abc.external.com/"


class TestEncodeExternalUrl:
    """Test encoding external URLs for mirror."""
    
    def test_encode_with_path(self):
        """Test encoding https://abc.external.com/path/to -> /abc.external.com/path/to"""
        result = encode_external_url_for_mirror(
            mirror_root="mirror.com",
            external_host="abc.external.com",
            external_path="/path/to"
        )
        assert result == "/abc.external.com/path/to"
    
    def test_encode_root_path(self):
        """Test encoding https://example.com/ -> /example.com/"""
        result = encode_external_url_for_mirror(
            mirror_root="mirror.com",
            external_host="example.com",
            external_path="/"
        )
        assert result == "/example.com/"
    
    def test_encode_without_leading_slash(self):
        """Test encoding with path missing leading slash."""
        result = encode_external_url_for_mirror(
            mirror_root="mirror.com",
            external_host="test.com",
            external_path="foo/bar"
        )
        assert result == "/test.com/foo/bar"
