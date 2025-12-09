"""
Test script for Phase 6: Ads/Analytics Removal + Optional Injection
"""

from app.proxy.filter_ads import clean_html, inject_ads_and_trackers


# Test HTML with ads and analytics
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <script src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID');
    </script>
</head>
<body>
    <h1>Welcome to Test Page</h1>
    <p>This is some content.</p>
    
    <!-- Ad iframe -->
    <iframe src="https://googleads.g.doubleclick.net/pagead/ads"></iframe>
    
    <!-- Facebook Pixel -->
    <script>
        !function(f,b,e,v,n,t,s)
        {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
        n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];
        s.parentNode.insertBefore(t,s)}(window, document,'script',
        'https://connect.facebook.net/en_US/fbevents.js');
        fbq('init', 'YOUR_PIXEL_ID');
        fbq('track', 'PageView');
    </script>
    
    <script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
</body>
</html>
"""


def test_clean_html_disabled():
    """Test that clean_html returns unchanged HTML when both flags are False."""
    config = {
        'remove_ads': False,
        'remove_analytics': False
    }
    
    result = clean_html(TEST_HTML, config)
    
    # Should contain ads and analytics
    assert 'googletagmanager.com' in result
    assert 'doubleclick.net' in result
    assert 'fbq(' in result
    assert 'googlesyndication.com' in result
    
    print("✅ Test 1 passed: HTML unchanged when both flags are False")


def test_clean_html_enabled():
    """Test that clean_html removes ads and analytics when enabled."""
    config = {
        'remove_ads': True,
        'remove_analytics': True
    }
    
    result = clean_html(TEST_HTML, config)
    
    # Should NOT contain ads and analytics
    assert 'googletagmanager.com' not in result
    assert 'doubleclick.net' not in result
    assert 'fbq(' not in result
    assert 'googlesyndication.com' not in result
    
    # Should still contain main content
    assert 'Welcome to Test Page' in result
    assert 'This is some content' in result
    
    print("✅ Test 2 passed: Ads and analytics removed when enabled")


def test_inject_nothing():
    """Test that inject_ads_and_trackers returns unchanged HTML when nothing to inject."""
    simple_html = "<html><body><h1>Test</h1></body></html>"
    
    config = {
        'inject_ads': False,
        'custom_ad_html': '',
        'custom_tracker_js': ''
    }
    
    result = inject_ads_and_trackers(simple_html, config)
    
    # Should not add anything
    assert '<h1>Test</h1>' in result
    
    print("✅ Test 3 passed: HTML unchanged when nothing to inject")


def test_inject_custom_ad():
    """Test that inject_ads_and_trackers injects custom ad HTML."""
    simple_html = "<html><body><h1>Test</h1></body></html>"
    
    config = {
        'inject_ads': True,
        'custom_ad_html': '<div class="my-ad">Custom Ad Here</div>',
        'custom_tracker_js': ''
    }
    
    result = inject_ads_and_trackers(simple_html, config)
    
    # Should contain custom ad
    assert 'Custom Ad Here' in result
    assert 'my-ad' in result
    
    print("✅ Test 4 passed: Custom ad HTML injected")


def test_inject_custom_tracker():
    """Test that inject_ads_and_trackers injects custom tracker JS."""
    simple_html = "<html><body><h1>Test</h1></body></html>"
    
    config = {
        'inject_ads': False,
        'custom_ad_html': '',
        'custom_tracker_js': 'console.log("Custom tracker loaded");'
    }
    
    result = inject_ads_and_trackers(simple_html, config)
    
    # Should contain custom tracker
    assert 'Custom tracker loaded' in result
    assert '<script>' in result
    
    print("✅ Test 5 passed: Custom tracker JS injected")


def test_full_pipeline():
    """Test the full pipeline: clean -> inject."""
    config = {
        'remove_ads': True,
        'remove_analytics': True,
        'inject_ads': True,
        'custom_ad_html': '<div id="custom-banner">Visit our sponsor!</div>',
        'custom_tracker_js': 'window._customTracker = "enabled";'
    }
    
    # Step 1: Clean
    cleaned = clean_html(TEST_HTML, config)
    
    # Should have removed third-party ads/analytics
    assert 'googletagmanager.com' not in cleaned
    assert 'doubleclick.net' not in cleaned
    
    # Step 2: Inject custom content
    final = inject_ads_and_trackers(cleaned, config)
    
    # Should contain custom ad and tracker
    assert 'Visit our sponsor!' in final
    assert '_customTracker' in final
    
    # Should still have main content
    assert 'Welcome to Test Page' in final
    
    print("✅ Test 6 passed: Full pipeline works correctly")


if __name__ == "__main__":
    print("Testing Phase 6: Ads/Analytics Removal + Optional Injection\n")
    
    try:
        test_clean_html_disabled()
        test_clean_html_enabled()
        test_inject_nothing()
        test_inject_custom_ad()
        test_inject_custom_tracker()
        test_full_pipeline()
        
        print("\n" + "="*60)
        print("🎉 All Phase 6 tests passed!")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
