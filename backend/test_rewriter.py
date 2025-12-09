"""
Test script to verify HTML rewriting functionality
"""

from app.proxy.rewriter import rewrite_html

# Sample HTML with various elements
sample_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <link href="/css/style.css" rel="stylesheet">
    <link href="https://en.wikipedia.org/wiki/style.css" rel="stylesheet">
    <script src="/js/main.js"></script>
    <script src="https://en.wikipedia.org/static/script.js"></script>
</head>
<body>
    <h1>Test Page</h1>
    
    <!-- Internal links -->
    <a href="/wiki/Python">Python Article</a>
    <a href="/wiki/JavaScript">JavaScript Article</a>
    
    <!-- External links -->
    <a href="https://www.google.com/search">Google Search</a>
    <a href="https://github.com/test">GitHub</a>
    
    <!-- Form -->
    <form action="/wiki/search" method="post">
        <input type="text" name="q">
        <button type="submit">Search</button>
    </form>
    
    <!-- Images -->
    <img src="/images/logo.png" alt="Logo">
    <img src="https://en.wikipedia.org/static/images/banner.jpg" alt="Banner">
    
    <!-- External image -->
    <img src="https://cdn.example.com/photo.jpg" alt="External">
    
    <!-- Iframe -->
    <iframe src="/wiki/embed"></iframe>
    
    <!-- Subdomain link -->
    <a href="https://commons.wikimedia.org/wiki/File:Example.jpg">Commons File</a>
</body>
</html>
"""

# Configuration
mirror_host = "wiki.test.local"
mirror_root = "wiki.test.local"
site_source_root = "en.wikipedia.org"
effective_config = {
    "proxy_subdomains": True,
    "proxy_external_domains": True,
    "media_policy": "proxy",
}
current_page_origin_url = "https://en.wikipedia.org/"

# Rewrite HTML
rewritten = rewrite_html(
    html=sample_html,
    mirror_host=mirror_host,
    mirror_root=mirror_root,
    site_source_root=site_source_root,
    effective_config=effective_config,
    current_page_origin_url=current_page_origin_url
)

print("=" * 80)
print("ORIGINAL HTML:")
print("=" * 80)
print(sample_html)
print("\n" + "=" * 80)
print("REWRITTEN HTML:")
print("=" * 80)
print(rewritten)
print("\n" + "=" * 80)
print("VERIFICATION:")
print("=" * 80)

# Verify specific rewrites
checks = [
    ('Internal link', 'href="/wiki/Python"', 'href="https://wiki.test.local/wiki/Python"'),
    ('External link (Google)', 'href="https://www.google.com/search"', 'href="https://wiki.test.local/www.google.com/search"'),
    ('External link (GitHub)', 'href="https://github.com/test"', 'href="https://wiki.test.local/github.com/test"'),
    ('Form action', 'action="/wiki/search"', 'action="https://wiki.test.local/wiki/search"'),
    ('Script src', 'src="/js/main.js"', 'src="https://wiki.test.local/js/main.js"'),
    ('Link href', 'href="/css/style.css"', 'href="https://wiki.test.local/css/style.css"'),
]

for name, original, expected in checks:
    if expected in rewritten:
        print(f"✅ {name}: PASS")
    else:
        print(f"❌ {name}: FAIL")
        print(f"   Expected: {expected}")
        # Find what it actually became
        import re
        # Extract the attribute value from rewritten HTML
        match = re.search(original.split('=')[0] + r'="([^"]*)"', rewritten)
        if match:
            print(f"   Got: {original.split('=')[0]}=\"{match.group(1)}\"")

print("=" * 80)
