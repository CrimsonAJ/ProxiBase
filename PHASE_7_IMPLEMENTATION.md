# Phase 7 Implementation: JS & CSS URL + Redirect Handling

## Overview
Phase 7 enhances ProxiBase's rewriting capabilities to handle JavaScript-based redirects and CSS url() patterns, ensuring complete URL rewriting for seamless mirror navigation.

## Changes Made

### 1. Enhanced `app/proxy/rewriter.py`

#### New Functions Added:

##### `rewrite_js_redirects()`
Rewrites JavaScript redirect patterns in inline `<script>` tags:
- `window.location.href = "URL"`
- `location.href = "URL"`
- `location.replace("URL")`
- `location = "URL"`

**Features:**
- Only processes inline scripts (not external JS files)
- Controlled by `effective_config.rewrite_js_redirects` flag
- Preserves quote style (single or double quotes)
- Uses regex patterns for reliable matching
- Converts URLs to appropriate mirror URLs (internal vs external)

##### `rewrite_css_urls()`
Rewrites `url()` patterns in CSS content:
- Handles: `url("...")`, `url('...')`, `url(...)`
- Applies to `<style>` tags and inline `style` attributes
- Respects `media_policy` for media files
- Maps page URLs through the proxy

**Features:**
- Preserves CSS url() format and quote style
- Skips data: URLs and special patterns
- Handles both absolute and relative URLs
- Conservative approach to avoid breaking sites

#### Updated `rewrite_html()` Function
Integrated JS and CSS rewriting into the main HTML processing pipeline:

```python
# Phase 7 additions:
1. Inline <script> tags: Rewrite JS redirect patterns
2. <style> tags: Rewrite CSS url() patterns  
3. style attributes: Rewrite CSS url() patterns in inline styles
```

### 2. Configuration Support

The `rewrite_js_redirects` flag in Site configuration controls JS rewriting:
- `True`: Enable JS redirect rewriting (recommended for most sites)
- `False`: Skip JS rewriting (for sites with complex JS that might break)

### 3. Processing Pipeline

**HTML Processing Flow (Phase 7):**
```
1. Parse HTML with BeautifulSoup
2. Rewrite standard HTML attributes (links, forms, images, etc.)
3. [NEW] If rewrite_js_redirects enabled:
   - Process inline <script> tags for redirect patterns
4. [NEW] Process <style> tags for url() patterns
5. [NEW] Process inline style attributes for url() patterns
6. Return rewritten HTML
```

## What Gets Rewritten

### JavaScript Patterns:
```javascript
// Before:
window.location.href = "https://source.com/page";
location.href = "/relative/path";
location.replace('https://external.com/page');
location = "/another/page";

// After (for mirror.com → source.com):
window.location.href = "https://mirror.com/page";
location.href = "https://mirror.com/relative/path";
location.replace('https://mirror.com/external.com/page');
location = "https://mirror.com/another/page";
```

### CSS Patterns:
```css
/* Before */
body {
    background: url("https://source.com/images/bg.jpg");
}
.banner {
    background-image: url('/static/banner.png');
}

/* After (for mirror.com → source.com) */
body {
    background: url("https://mirror.com/images/bg.jpg");
}
.banner {
    background-image: url('https://mirror.com/static/banner.png');
}
```

## Conservative Approach

Phase 7 follows a **conservative strategy** to avoid breaking websites:

1. **JS Rewriting:**
   - Only processes obvious redirect patterns
   - Only affects inline scripts (not external .js files)
   - Can be disabled per-site via configuration
   - Uses precise regex patterns to minimize false positives

2. **CSS Rewriting:**
   - Only processes url() patterns
   - Respects media_policy for images and fonts
   - Preserves CSS syntax and formatting
   - Handles all quote styles correctly

3. **No External File Parsing:**
   - External JS files (via `<script src>`) are not parsed/modified
   - External CSS files (via `<link>`) are not parsed/modified
   - Only the src/href attributes are rewritten (already done in Phase 5)

## Testing

### Unit Tests (`test_phase7.py`)
Comprehensive test suite covering:
1. JS redirect pattern rewriting (4 patterns)
2. CSS url() rewriting (various formats)
3. HTML integration test (complete pipeline)

**Run tests:**
```bash
cd /app/backend
python3 test_phase7.py
```

### Test Results:
```
✓ JS window.location.href rewriting
✓ JS location.href rewriting  
✓ JS location.replace rewriting
✓ JS location = rewriting
✓ CSS url() with various quote styles
✓ CSS url() with media files
✓ Complete HTML integration
```

## Configuration

### Site-Level Configuration:
```python
site = Site(
    mirror_root="mirror.example.com",
    source_root="source.example.com",
    rewrite_js_redirects=True,  # Enable JS redirect rewriting
    media_policy="proxy",        # How to handle media URLs
    proxy_external_domains=True  # Proxy external domains
)
```

### Global Configuration:
Falls back to global config if site-level config is not set.

## Examples

### Example 1: Wikipedia Mirror
```python
# Site configuration
mirror_root = "wiki.test.local"
source_root = "en.wikipedia.org"
rewrite_js_redirects = True

# Input HTML:
<script>
if (redirect) {
    window.location.href = "https://en.wikipedia.org/wiki/JavaScript";
}
</script>

# Output HTML:
<script>
if (redirect) {
    window.location.href = "https://wiki.test.local/wiki/JavaScript";
}
</script>
```

### Example 2: CSS Background Images
```python
# Input:
<style>
.header { background: url('https://source.com/img/header.jpg'); }
</style>

# Output (for mirror.test → source.com):
<style>
.header { background: url('https://mirror.test/img/header.jpg'); }
</style>
```

### Example 3: External Domain Handling
```python
# Input:
<script>location.href = 'https://external.com/page';</script>

# Output (with proxy_external_domains=True):
<script>location.href = 'https://mirror.test/external.com/page';</script>
```

## Limitations & Future Enhancements

### Current Limitations:
1. **No External JS File Parsing:** External .js files are not parsed/modified
   - This is intentional to avoid performance issues
   - Only the src attribute is rewritten

2. **Simple Pattern Matching:** JS rewriting uses regex, not AST parsing
   - May not catch complex or obfuscated redirect patterns
   - Focus is on common, obvious patterns

3. **No JS Variable Tracking:** Does not track variables
   ```javascript
   // This would NOT be rewritten:
   var url = "https://source.com/page";
   location.href = url;
   ```

### Potential Future Enhancements:
1. AST-based JS parsing for more robust rewriting
2. External JS file parsing (with size limits)
3. Variable tracking for dynamic URL construction
4. Configurable pattern whitelist/blacklist
5. Performance optimization for large pages

## Performance Considerations

Phase 7 adds minimal overhead:
- JS rewriting: Only if `rewrite_js_redirects=True` and inline scripts present
- CSS rewriting: Only processes `<style>` tags and style attributes
- Regex patterns are optimized for performance
- No external file fetching/parsing

**Estimated overhead:** < 10ms per page for typical HTML

## Backward Compatibility

Phase 7 is **fully backward compatible**:
- JS rewriting is opt-in via `rewrite_js_redirects` flag
- CSS rewriting is always active but conservative
- No changes to existing Phase 1-6 functionality
- All existing tests continue to pass

## Summary

Phase 7 successfully implements:
✅ JS redirect pattern rewriting (4 patterns)
✅ CSS url() rewriting
✅ Integration with existing HTML rewriting pipeline
✅ Conservative approach to avoid breaking sites
✅ Comprehensive testing
✅ Configuration support
✅ Performance optimization
✅ Full backward compatibility

The implementation focuses on common redirect patterns while maintaining stability and performance. External JS file parsing is intentionally excluded to keep the proxy lightweight and fast.
