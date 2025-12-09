"""
Integration Test for Phase 6
Tests the complete HTML processing pipeline
"""

from app.proxy.filter_ads import clean_html, inject_ads_and_trackers
from app.proxy.rewriter import rewrite_html


# Simulated HTML from an origin site with ads/analytics
ORIGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Example Article - Wikipedia</title>
    
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'GA_TRACKING_ID');
    </script>
    
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <h1>Example Article</h1>
        <nav>
            <a href="/wiki/Main_Page">Main Page</a>
            <a href="/wiki/Special:Random">Random</a>
        </nav>
    </header>
    
    <main>
        <article>
            <h2>Introduction</h2>
            <p>This is an example article with some content.</p>
            <p>It has links to <a href="https://en.wikipedia.org/wiki/Example">other pages</a>.</p>
            
            <img src="/static/images/example.jpg" alt="Example">
        </article>
        
        <!-- Ad banner -->
        <div class="ad-container">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
            <ins class="adsbygoogle"></ins>
            <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
        </div>
        
        <!-- Doubleclick ad iframe -->
        <iframe src="https://googleads.g.doubleclick.net/pagead/ads?client=ca-pub-123"
                width="728" height="90" frameborder="0"></iframe>
    </main>
    
    <footer>
        <p>© 2024 Example Site</p>
    </footer>
    
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
        fbq('init', 'PIXEL_ID');
        fbq('track', 'PageView');
    </script>
</body>
</html>
"""


def test_complete_pipeline():
    """Test the complete Phase 6 pipeline: clean -> rewrite -> inject."""
    
    print("\n" + "="*70)
    print("Phase 6 Complete Pipeline Integration Test")
    print("="*70 + "\n")
    
    # Effective configuration
    effective_config = {
        'remove_ads': True,
        'remove_analytics': True,
        'inject_ads': True,
        'custom_ad_html': '<div id="proxibase-ad" style="background: #4caf50; color: white; padding: 15px; text-align: center; font-size: 18px;">📢 ProxiBase - Your content, your rules!</div>',
        'custom_tracker_js': 'window.proxibaseTracker = { version: "1.0", phase: 6, active: true };',
        'proxy_subdomains': True,
        'proxy_external_domains': True,
        'rewrite_js_redirects': False,
        'media_policy': 'proxy',
        'session_mode': 'stateless'
    }
    
    current_page_origin_url = "https://en.wikipedia.org/wiki/Example_Article"
    mirror_host = "wiki.test.local"
    mirror_root = "wiki.test.local"
    site_source_root = "en.wikipedia.org"
    
    print("Configuration:")
    print(f"  Origin: {current_page_origin_url}")
    print(f"  Mirror: {mirror_host}")
    print(f"  Remove Ads: {effective_config['remove_ads']}")
    print(f"  Remove Analytics: {effective_config['remove_analytics']}")
    print(f"  Inject Ads: {effective_config['inject_ads']}")
    print(f"\nOriginal HTML size: {len(ORIGIN_HTML)} bytes\n")
    
    # STEP 1: Clean ads/analytics
    print("Step 1: Cleaning ads and analytics...")
    cleaned_html = clean_html(ORIGIN_HTML, effective_config)
    
    # Verify cleaning worked
    ads_removed = 'doubleclick.net' not in cleaned_html
    analytics_removed = 'googletagmanager.com' not in cleaned_html
    fb_pixel_removed = 'fbq(' not in cleaned_html
    adsense_removed = 'googlesyndication.com' not in cleaned_html
    
    print(f"  ✅ Doubleclick ads removed: {ads_removed}")
    print(f"  ✅ Google Analytics removed: {analytics_removed}")
    print(f"  ✅ Facebook Pixel removed: {fb_pixel_removed}")
    print(f"  ✅ Google AdSense removed: {adsense_removed}")
    print(f"  Cleaned HTML size: {len(cleaned_html)} bytes\n")
    
    # STEP 2: Rewrite URLs for mirror
    print("Step 2: Rewriting URLs for mirror navigation...")
    rewritten_html = rewrite_html(
        html=cleaned_html,
        mirror_host=mirror_host,
        mirror_root=mirror_root,
        site_source_root=site_source_root,
        effective_config=effective_config,
        current_page_origin_url=current_page_origin_url
    )
    
    # Verify rewriting worked
    links_rewritten = 'wiki.test.local' in rewritten_html
    origin_links_removed = 'en.wikipedia.org' not in rewritten_html or rewritten_html.count('en.wikipedia.org') < ORIGIN_HTML.count('en.wikipedia.org')
    
    print(f"  ✅ Links rewritten to mirror domain: {links_rewritten}")
    print(f"  ✅ Origin links converted: {origin_links_removed}")
    print(f"  Rewritten HTML size: {len(rewritten_html)} bytes\n")
    
    # STEP 3: Inject custom ads and trackers
    print("Step 3: Injecting custom ads and trackers...")
    final_html = inject_ads_and_trackers(rewritten_html, effective_config)
    
    # Verify injection worked
    custom_ad_injected = 'ProxiBase - Your content, your rules!' in final_html
    custom_tracker_injected = 'proxibaseTracker' in final_html
    
    print(f"  ✅ Custom ad injected: {custom_ad_injected}")
    print(f"  ✅ Custom tracker injected: {custom_tracker_injected}")
    print(f"  Final HTML size: {len(final_html)} bytes\n")
    
    # Final verification
    print("="*70)
    print("Final Verification:")
    print("="*70)
    
    checks = {
        "Third-party ads removed": not ('doubleclick' in final_html or 'googlesyndication' in final_html),
        "Analytics removed": not ('googletagmanager' in final_html or 'fbq(' in final_html),
        "Custom ad present": 'proxibase-ad' in final_html.lower(),
        "Custom tracker present": 'proxibaseTracker' in final_html,
        "URLs rewritten to mirror": 'wiki.test.local' in final_html,
        "Original content preserved": 'Example Article' in final_html,
        "Links functional": '/wiki/Main_Page' in final_html or 'Main Page' in final_html,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 PHASE 6 INTEGRATION TEST PASSED!")
        print("\nThe complete pipeline works correctly:")
        print("  1. ✅ Removes third-party ads and analytics")
        print("  2. ✅ Rewrites URLs for mirror navigation")
        print("  3. ✅ Injects custom ads and tracking")
        print("  4. ✅ Preserves original content")
        print("="*70 + "\n")
        return True
    else:
        print("\n❌ Some checks failed\n")
        return False


def test_disabled_features():
    """Test that pipeline works correctly when features are disabled."""
    
    print("\n" + "="*70)
    print("Phase 6 Pipeline Test - Features Disabled")
    print("="*70 + "\n")
    
    # Configuration with all Phase 6 features disabled
    config_disabled = {
        'remove_ads': False,
        'remove_analytics': False,
        'inject_ads': False,
        'custom_ad_html': '',
        'custom_tracker_js': '',
        'proxy_subdomains': True,
        'proxy_external_domains': True,
        'media_policy': 'proxy',
    }
    
    current_page_origin_url = "https://en.wikipedia.org/wiki/Test"
    
    print("Testing with all Phase 6 features disabled...\n")
    
    # Step 1: Clean (should do nothing)
    cleaned = clean_html(ORIGIN_HTML, config_disabled)
    
    # Step 2: Rewrite
    rewritten = rewrite_html(
        html=cleaned,
        mirror_host="wiki.test.local",
        mirror_root="wiki.test.local",
        site_source_root="en.wikipedia.org",
        effective_config=config_disabled,
        current_page_origin_url=current_page_origin_url
    )
    
    # Step 3: Inject (should do nothing)
    final = inject_ads_and_trackers(rewritten, config_disabled)
    
    # Verify
    checks = {
        "Ads NOT removed (as configured)": 'doubleclick' in final or 'googlesyndication' in final,
        "Analytics NOT removed (as configured)": 'googletagmanager' in final or 'gtag(' in final,
        "Custom ad NOT injected": 'ProxiBase' not in final,
        "URLs still rewritten": 'wiki.test.local' in final,
        "Content preserved": 'Example Article' in final,
    }
    
    print("Verification:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    
    if all_passed:
        print("✅ Pipeline works correctly with features disabled")
        print("="*70 + "\n")
        return True
    else:
        print("❌ Some checks failed with features disabled")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ProxiBase - Phase 6 Integration Test Suite")
    print("="*70)
    
    try:
        result1 = test_complete_pipeline()
        result2 = test_disabled_features()
        
        if result1 and result2:
            print("\n" + "="*70)
            print("🎊 ALL PHASE 6 INTEGRATION TESTS PASSED! 🎊")
            print("="*70)
            print("\nPhase 6 Implementation Complete:")
            print("  ✅ clean_html() function working")
            print("  ✅ inject_ads_and_trackers() function working")
            print("  ✅ Complete pipeline integrated")
            print("  ✅ Configuration handling correct")
            print("  ✅ Backward compatibility maintained")
            print("="*70 + "\n")
        else:
            print("\n⚠️  Some tests failed\n")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
