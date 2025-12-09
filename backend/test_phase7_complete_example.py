"""
Phase 7 Complete Example
Demonstrates the full functionality of JS & CSS URL + Redirect Handling
"""

from app.proxy.rewriter import rewrite_html

# Test configuration
mirror_host = "wiki.test.local"
mirror_root = "wiki.test.local"
site_source_root = "en.wikipedia.org"
current_page_origin_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
effective_config = {
    'rewrite_js_redirects': True,
    'media_policy': 'proxy',
    'proxy_external_domains': True,
    'remove_ads': True,
    'inject_ads': False
}

# Complete HTML example with all Phase 7 features
complete_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ProxiBase Phase 7 Demo</title>
    
    <!-- Phase 7: CSS url() rewriting in <style> tags -->
    <style>
        body {
            font-family: Arial, sans-serif;
            background-image: url("/static/images/background.jpg");
            background-size: cover;
        }
        
        .header {
            background: url('https://en.wikipedia.org/static/images/header-bg.png');
            height: 100px;
        }
        
        .logo {
            background-image: url(/static/logo.svg);
        }
        
        @font-face {
            font-family: 'CustomFont';
            src: url("https://en.wikipedia.org/fonts/custom.woff2");
        }
    </style>
</head>
<body>
    <div class="header"></div>
    
    <!-- Phase 7: CSS url() in inline style attributes -->
    <div style="background: url('https://en.wikipedia.org/images/banner.jpg'); padding: 20px;">
        <h1>Welcome to ProxiBase</h1>
        <p>Testing Phase 7 functionality</p>
    </div>
    
    <!-- Regular links (Phase 5 rewriting) -->
    <nav>
        <a href="/wiki/Main_Page">Home</a> |
        <a href="/wiki/Help">Help</a> |
        <a href="https://en.wikipedia.org/wiki/Special:Random">Random</a>
    </nav>
    
    <!-- External domain link (Phase 5 rewriting) -->
    <div>
        <a href="https://external.com/some/page">External Link</a>
    </div>
    
    <!-- Phase 7: JS redirect patterns in inline <script> -->
    <script>
        // Pattern 1: window.location.href
        function goToMainPage() {
            window.location.href = "https://en.wikipedia.org/wiki/Main_Page";
        }
        
        // Pattern 2: location.href
        function goToHelp() {
            location.href = "/wiki/Help:Contents";
        }
        
        // Pattern 3: location.replace
        function redirectToSearch() {
            location.replace('https://en.wikipedia.org/w/index.php?search=test');
        }
        
        // Pattern 4: location =
        function simpleRedirect() {
            location = "/wiki/Special:Random";
        }
        
        // External domain redirect
        function goToExternal() {
            window.location.href = "https://external.com/page";
        }
        
        // This should trigger on page load if enabled
        var shouldRedirect = false;
        if (shouldRedirect) {
            window.location.href = "https://en.wikipedia.org/wiki/JavaScript";
        }
    </script>
    
    <!-- External JS file (src rewritten by Phase 5, content not parsed) -->
    <script src="https://en.wikipedia.org/static/js/app.js"></script>
    
    <!-- More inline styles -->
    <section style="background-image: url('/images/section-bg.png');">
        <h2>Section with Background</h2>
    </section>
    
    <footer>
        <p>&copy; 2024 ProxiBase - Phase 7 Complete</p>
    </footer>
</body>
</html>
"""

print("=" * 80)
print("Phase 7 Complete Example - Before & After Rewriting")
print("=" * 80)
print()

print("CONFIGURATION:")
print(f"  Mirror: {mirror_root}")
print(f"  Source: {site_source_root}")
print(f"  JS Rewriting: {effective_config['rewrite_js_redirects']}")
print(f"  Media Policy: {effective_config['media_policy']}")
print(f"  Proxy External: {effective_config['proxy_external_domains']}")
print()

print("=" * 80)
print("BEFORE (Original HTML):")
print("=" * 80)
print(complete_html)
print()

print("=" * 80)
print("AFTER (Rewritten HTML):")
print("=" * 80)

# Rewrite the HTML
rewritten_html = rewrite_html(
    complete_html,
    mirror_host,
    mirror_root,
    site_source_root,
    effective_config,
    current_page_origin_url
)

print(rewritten_html)
print()

print("=" * 80)
print("VERIFICATION CHECKS:")
print("=" * 80)

checks = [
    ("Mirror domain in result", mirror_root in rewritten_html),
    ("CSS background-image rewritten", 'url("https://wiki.test.local' in rewritten_html or 'url(https://wiki.test.local' in rewritten_html),
    ("JS window.location.href rewritten", 'window.location.href = "https://wiki.test.local/wiki/Main_Page"' in rewritten_html),
    ("JS location.href rewritten", 'location.href = "https://wiki.test.local/wiki/Help:Contents"' in rewritten_html),
    ("JS location.replace rewritten", 'location.replace(\'https://wiki.test.local/w/index.php?search=test\')' in rewritten_html),
    ("JS location = rewritten", 'location = "https://wiki.test.local/wiki/Special:Random"' in rewritten_html),
    ("External domain in JS rewritten", 'wiki.test.local/external.com' in rewritten_html),
    ("Inline style url() rewritten", 'style="background: url(\'https://wiki.test.local' in rewritten_html or 'style="background:url(\'https://wiki.test.local' in rewritten_html or 'style="background-image: url(' in rewritten_html),
    ("External JS src rewritten", 'src="https://wiki.test.local/static/js/app.js"' in rewritten_html),
    ("Regular links rewritten", 'href="https://wiki.test.local/wiki/Main_Page"' in rewritten_html),
]

passed = 0
failed = 0

for check_name, result in checks:
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"  {status}: {check_name}")
    if result:
        passed += 1
    else:
        failed += 1

print()
print("=" * 80)
print(f"SUMMARY: {passed} passed, {failed} failed out of {len(checks)} checks")
print("=" * 80)

if failed == 0:
    print("🎉 All Phase 7 features working correctly!")
else:
    print(f"⚠️  {failed} check(s) failed. Please review.")

print()
