# Phase 5 Implementation - HTML Rewriting

## Overview

Phase 5 implements comprehensive HTML rewriting to keep navigation within mirror domains. All links, forms, iframes, and resource references are rewritten according to the URL mapping rules established in previous phases.

## Implementation Details

### 1. Created `/app/backend/app/proxy/rewriter.py`

This module provides the core HTML rewriting functionality with the following key functions:

#### `rewrite_html(html, mirror_host, mirror_root, site_source_root, effective_config, current_page_origin_url)`
Main function that parses and rewrites HTML content.

**Rewrites these HTML attributes:**
- `<a href>` - Links
- `<form action>` - Form submissions
- `<iframe src>` - Embedded content
- `<link href>` - Stylesheets and resources
- `<script src>` - External scripts
- `<img src>` - Images (based on media_policy)
- `<img srcset>` - Responsive images
- `<source src>` - Video/audio sources
- `<video src>` - Video elements
- `<audio src>` - Audio elements
- `<base href>` - Base URL reference

#### `rewrite_url(url, current_page_origin_url, mirror_host, mirror_root, site_source_root, effective_config)`
Rewrites a single URL according to mapping rules:

1. **Special URLs**: Skips `data:`, `javascript:`, `mailto:`, `#` URLs
2. **Relative to Absolute**: Converts relative URLs to absolute using the current page's origin URL
3. **Media Files**: Based on file extension and `media_policy`:
   - If `media_policy = "bypass"`, leaves media URLs pointing to origin (not rewritten)
   - Otherwise, rewrites like any other URL
4. **Same Domain/Subdomain**: Maps to mirror equivalent
   - `source.com/path` → `mirror.com/path`
   - `xyz.source.com/path` → `xyz.mirror.com/path`
5. **External Domains**: Encodes as mirror path (if `proxy_external_domains = true`)
   - `external.com/path` → `mirror.com/external.com/path`

#### Helper Functions

- `is_media_url(url)`: Checks if URL is a media/download resource based on file extension
- `make_absolute_url(url, base_url)`: Converts relative URLs to absolute
- `url_belongs_to_domain(url, domain)`: Checks if URL belongs to domain or subdomain
- `map_origin_host_to_mirror_host(origin_host, source_root, mirror_root)`: Maps origin host to mirror host
- `encode_external_url_path(external_host, external_path)`: Encodes external URL as path

**Media Extensions Handled:**
```python
Images:   .jpg, .jpeg, .png, .gif, .webp, .svg, .ico, .bmp
Videos:   .mp4, .mkv, .avi, .mov, .m3u8, .webm, .flv, .wmv
Audio:    .mp3, .wav, .ogg, .aac, .flac, .m4a
Archives: .zip, .rar, .7z, .tar, .gz, .bz2
Documents: .pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx
Executables: .apk, .exe, .dmg, .deb, .rpm
Fonts:    .ttf, .woff, .woff2, .eot, .otf
```

### 2. Updated `/app/backend/app/proxy/router.py`

Integrated HTML rewriting into the proxy pipeline:

**Changes:**
1. Added imports:
   ```python
   from app.models.global_config import GlobalConfig
   from app.core.config_helper import get_effective_config
   from app.proxy.rewriter import rewrite_html
   ```

2. Modified the HTML response handling in `proxy_request()`:
   - Fetches GlobalConfig from database
   - Merges site-specific and global configuration
   - Decodes HTML content
   - Calls `rewrite_html()` to rewrite the content
   - Returns rewritten HTML

**Before (lines 325-335):**
```python
# For HTML, return as-is (no rewriting yet)
if 'text/html' in content_type.lower():
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
        media_type=content_type
    )
```

**After:**
```python
# For HTML, rewrite links and return
if 'text/html' in content_type.lower():
    # Get global config and merge with site config
    global_config_result = await db.execute(select(GlobalConfig).where(GlobalConfig.id == 1))
    global_config = global_config_result.scalar_one_or_none()
    
    # Create default global config if not exists
    if not global_config:
        global_config = GlobalConfig(id=1)
        db.add(global_config)
        await db.commit()
        await db.refresh(global_config)
    
    # Get effective configuration
    effective_config = get_effective_config(site, global_config)
    
    # Decode and rewrite HTML
    html_content = response.content.decode('utf-8', errors='ignore')
    rewritten_html = rewrite_html(
        html=html_content,
        mirror_host=request.headers.get('host', site.mirror_root).split(':')[0],
        mirror_root=site.mirror_root,
        site_source_root=site.source_root,
        effective_config=effective_config,
        current_page_origin_url=origin_url
    )
    
    return Response(
        content=rewritten_html,
        status_code=response.status_code,
        headers=response_headers,
        media_type=content_type
    )
```

### 3. Dependencies

Added required libraries for HTML parsing:
- `beautifulsoup4==4.14.3` - HTML parsing and manipulation
- `lxml==6.0.2` - Fast XML/HTML parser (used by BeautifulSoup)
- `soupsieve==2.8` - CSS selector support

## Testing Results

Created test script `/app/backend/test_rewriter.py` to verify functionality.

**Test Results: ✅ ALL PASS**

1. ✅ Internal link rewriting: `/wiki/Python` → `https://wiki.test.local/wiki/Python`
2. ✅ External link encoding (Google): `https://www.google.com/search` → `https://wiki.test.local/www.google.com/search`
3. ✅ External link encoding (GitHub): `https://github.com/test` → `https://wiki.test.local/github.com/test`
4. ✅ Form action rewriting: `/wiki/search` → `https://wiki.test.local/wiki/search`
5. ✅ Script src rewriting: `/js/main.js` → `https://wiki.test.local/js/main.js`
6. ✅ Link href rewriting: `/css/style.css` → `https://wiki.test.local/css/style.css`

Additional elements verified:
- Images (internal and external)
- Iframes
- Responsive images (srcset)
- Video/audio sources
- Subdomain links (e.g., commons.wikimedia.org)

## URL Mapping Rules Implementation

### Rule 1: Same Domain or Subdomain
If the URL belongs to `source_root` or its subdomains:
- Preserve the path structure
- Map the host according to mirror rules

**Examples:**
```
source.com/path           → mirror.com/path
xyz.source.com/path       → xyz.mirror.com/path
a.b.source.com/path       → a.b.mirror.com/path
```

### Rule 2: External Domains
If the URL is from an external domain (not source_root):
- Check `proxy_external_domains` config
- If enabled, encode as: `mirror.com/external.host/path`
- If disabled, leave pointing to origin

**Examples:**
```
external.com/path         → mirror.com/external.com/path
abc.external.com/foo      → mirror.com/abc.external.com/foo
```

### Rule 3: Media Policy
Based on file extension and `media_policy` setting:
- **bypass**: Leave media URLs pointing to origin (no rewriting)
- **proxy**: Rewrite media URLs like any other resource
- **size_limited**: Rewrite media URLs (size limiting handled elsewhere)

## Configuration Respect

The rewriter respects the following configuration options from `EffectiveConfig`:

1. **`proxy_external_domains`**: Controls whether external domain links are rewritten
2. **`media_policy`**: Controls how media files are handled
   - `"bypass"`: Media files point directly to origin
   - `"proxy"`: Media files are proxied through mirror
   - `"size_limited"`: Media files proxied with size limits

Other config options (like `remove_ads`, `inject_ads`, etc.) will be implemented in future phases.

## Integration with Existing Code

The implementation integrates seamlessly with phases 0-4:

1. **Uses existing URL utilities:**
   - `build_origin_url()` from `core/url_utils.py`
   - `encode_external_url_for_mirror()` concept

2. **Uses existing config system:**
   - `get_effective_config()` from `core/config_helper.py`
   - Site and GlobalConfig models

3. **Uses existing proxy infrastructure:**
   - Integrates into `proxy_request()` in `proxy/router.py`
   - Maintains header filtering and redirect handling

## Files Modified

1. **Created:**
   - `/app/backend/app/proxy/rewriter.py` (322 lines)
   - `/app/backend/test_rewriter.py` (test script)

2. **Modified:**
   - `/app/backend/app/proxy/router.py` (added HTML rewriting integration)
   - `/app/backend/requirements.txt` (added beautifulsoup4, lxml)

3. **Configuration:**
   - `/app/backend/.env` (updated to match ProxiBase settings)

## Next Steps (Future Phases)

While Phase 5 is complete, potential enhancements for future phases include:

1. **CSS Rewriting**: Parse and rewrite URLs in stylesheets
2. **JavaScript Rewriting**: Handle JavaScript redirects and dynamic URL construction
3. **Clean HTML**: Implement ad removal and analytics stripping
4. **Ad Injection**: Add custom ads to rewritten pages
5. **Custom Tracking**: Inject custom analytics code

## System Status

✅ Backend running successfully on port 8001
✅ Database initialized with sites and global config
✅ HTML rewriting integrated and tested
✅ All dependencies installed
✅ Ready for end-to-end testing

## Test Configuration

Pre-configured site for testing:
- **Mirror Root**: `wiki.test.local`
- **Source Root**: `en.wikipedia.org`
- **Enabled**: Yes
- **Proxy Subdomains**: Yes

You can test with:
```bash
curl -H "Host: wiki.test.local" -H "User-Agent: Mozilla/5.0" http://0.0.0.0:8001/
```

Note: Wikipedia may rate-limit requests. For full testing, configure a site pointing to a different origin or use the test script.
