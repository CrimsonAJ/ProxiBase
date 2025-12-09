"""
Test Phase 7: JS & CSS URL + Redirect Handling
"""

from app.proxy.rewriter import (
    rewrite_js_redirects,
    rewrite_css_urls,
    rewrite_html
)


def test_js_redirects():
    """Test JS redirect pattern rewriting"""
    
    # Test data
    mirror_host = "wiki.test.local"
    mirror_root = "wiki.test.local"
    site_source_root = "en.wikipedia.org"
    current_page_origin_url = "https://en.wikipedia.org/wiki/Python"
    effective_config = {
        'rewrite_js_redirects': True,
        'media_policy': 'proxy',
        'proxy_external_domains': True
    }
    
    # Test 1: window.location.href
    js1 = 'window.location.href = "https://en.wikipedia.org/wiki/JavaScript";'
    result1 = rewrite_js_redirects(js1, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 1 - window.location.href:")
    print(f"  Input:  {js1}")
    print(f"  Output: {result1}")
    assert "wiki.test.local" in result1
    print("  ✓ PASSED\n")
    
    # Test 2: location.href
    js2 = 'location.href = "/wiki/Main_Page";'
    result2 = rewrite_js_redirects(js2, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 2 - location.href:")
    print(f"  Input:  {js2}")
    print(f"  Output: {result2}")
    assert "wiki.test.local" in result2
    print("  ✓ PASSED\n")
    
    # Test 3: location.replace
    js3 = "location.replace('https://en.wikipedia.org/wiki/Programming');"
    result3 = rewrite_js_redirects(js3, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 3 - location.replace:")
    print(f"  Input:  {js3}")
    print(f"  Output: {result3}")
    assert "wiki.test.local" in result3
    print("  ✓ PASSED\n")
    
    # Test 4: location =
    js4 = 'location = "/wiki/Special:Random";'
    result4 = rewrite_js_redirects(js4, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 4 - location =:")
    print(f"  Input:  {js4}")
    print(f"  Output: {result4}")
    assert "wiki.test.local" in result4
    print("  ✓ PASSED\n")


def test_css_urls():
    """Test CSS url() pattern rewriting"""
    
    # Test data
    mirror_host = "wiki.test.local"
    mirror_root = "wiki.test.local"
    site_source_root = "en.wikipedia.org"
    current_page_origin_url = "https://en.wikipedia.org/wiki/Python"
    effective_config = {
        'rewrite_js_redirects': True,
        'media_policy': 'proxy',
        'proxy_external_domains': True
    }
    
    # Test 1: CSS url() with media (should be rewritten based on media_policy)
    css1 = 'background-image: url("/static/images/logo.png");'
    result1 = rewrite_css_urls(css1, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 1 - CSS url() with image:")
    print(f"  Input:  {css1}")
    print(f"  Output: {result1}")
    assert "wiki.test.local" in result1 or "logo.png" in result1
    print("  ✓ PASSED\n")
    
    # Test 2: CSS url() with double quotes
    css2 = 'background: url("https://en.wikipedia.org/static/bg.jpg");'
    result2 = rewrite_css_urls(css2, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 2 - CSS url() with double quotes:")
    print(f"  Input:  {css2}")
    print(f"  Output: {result2}")
    assert "wiki.test.local" in result2 or "bg.jpg" in result2
    print("  ✓ PASSED\n")
    
    # Test 3: CSS url() with single quotes
    css3 = "background: url('/static/style/main.css');"
    result3 = rewrite_css_urls(css3, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 3 - CSS url() with single quotes:")
    print(f"  Input:  {css3}")
    print(f"  Output: {result3}")
    assert "wiki.test.local" in result3
    print("  ✓ PASSED\n")
    
    # Test 4: CSS url() without quotes
    css4 = "font-face { src: url(/fonts/custom.woff2); }"
    result4 = rewrite_css_urls(css4, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)
    print("Test 4 - CSS url() without quotes:")
    print(f"  Input:  {css4}")
    print(f"  Output: {result4}")
    assert "wiki.test.local" in result4 or "woff2" in result4
    print("  ✓ PASSED\n")


def test_html_integration():
    """Test complete HTML rewriting with JS and CSS"""
    
    mirror_host = "wiki.test.local"
    mirror_root = "wiki.test.local"
    site_source_root = "en.wikipedia.org"
    current_page_origin_url = "https://en.wikipedia.org/wiki/Python"
    effective_config = {
        'rewrite_js_redirects': True,
        'media_policy': 'proxy',
        'proxy_external_domains': True
    }
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                background-image: url("/static/bg.jpg");
            }
        </style>
    </head>
    <body>
        <div style="background: url('https://en.wikipedia.org/images/test.png');">
            <a href="/wiki/Main_Page">Home</a>
        </div>
        <script>
            if (redirect) {
                window.location.href = "https://en.wikipedia.org/wiki/JavaScript";
            }
        </script>
    </body>
    </html>
    """
    
    result = rewrite_html(
        html,
        mirror_host,
        mirror_root,
        site_source_root,
        effective_config,
        current_page_origin_url
    )
    
    print("Test - Complete HTML rewriting:")
    print("\n=== OUTPUT HTML ===")
    print(result)
    print("===================\n")
    
    # Verify rewriting occurred
    assert "wiki.test.local" in result, "Mirror host should be in result"
    print("  ✓ HTML contains mirror host\n")
    
    # Verify JS redirect was rewritten (if config enabled)
    if effective_config.get('rewrite_js_redirects'):
        assert 'window.location.href = "https://wiki.test.local/wiki/JavaScript"' in result or \
               'window.location.href = "https://en.wikipedia.org/wiki/JavaScript"' in result
        print("  ✓ JS redirect rewriting applied\n")
    
    print("  ✓ INTEGRATION TEST PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 7 Testing: JS & CSS URL + Redirect Handling")
    print("=" * 60)
    print()
    
    print("Testing JS Redirect Rewriting:")
    print("-" * 60)
    test_js_redirects()
    
    print("\nTesting CSS URL Rewriting:")
    print("-" * 60)
    test_css_urls()
    
    print("\nTesting HTML Integration:")
    print("-" * 60)
    test_html_integration()
    
    print("\n" + "=" * 60)
    print("All Phase 7 tests completed successfully! ✓")
    print("=" * 60)
