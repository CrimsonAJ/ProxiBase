#!/bin/bash

# ProxiBase Phase 9 - End-to-End Test Script
# Tests: SSRF protection, rate limiting, response limits, timeouts, and logging

set -e

echo "================================================"
echo "ProxiBase Phase 9 - End-to-End Testing"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ INFO:${NC} $1"
}

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
HEALTH=$(curl -s http://localhost:8001/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    pass "Backend health check"
else
    fail "Backend health check - got: $HEALTH"
fi
echo ""

# Test 2: SSRF Protection
echo "Test 2: SSRF Protection"
echo "----------------------"
info "Testing SSRF protection with Python script..."

cat > /tmp/test_ssrf.py << 'EOF'
import sys
sys.path.insert(0, '/app/backend')
from app.core.security import is_safe_origin_url

test_cases = [
    ("https://example.com/", True, "Public domain"),
    ("http://localhost:8080/", False, "Localhost"),
    ("http://127.0.0.1/", False, "Loopback IP"),
    ("http://10.0.0.1/", False, "Private 10.x"),
    ("http://192.168.1.1/", False, "Private 192.168.x"),
    ("http://172.16.0.1/", False, "Private 172.16.x"),
    ("http://169.254.0.1/", False, "Link-local"),
    ("ftp://example.com/", False, "Non-HTTP scheme"),
]

passed = 0
failed = 0

for url, should_be_safe, description in test_cases:
    is_safe, reason = is_safe_origin_url(url)
    if is_safe == should_be_safe:
        print(f"✓ {description}: {url}")
        passed += 1
    else:
        print(f"✗ {description}: {url} - Expected safe={should_be_safe}, got safe={is_safe}")
        print(f"  Reason: {reason}")
        failed += 1

print(f"\nSSRF Tests: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
EOF

if python3 /tmp/test_ssrf.py; then
    pass "SSRF protection tests"
else
    fail "SSRF protection tests"
fi
rm /tmp/test_ssrf.py
echo ""

# Test 3: Configuration Check
echo "Test 3: Configuration Check"
echo "---------------------------"
info "Checking Phase 9 configuration..."

cat > /tmp/test_config.py << 'EOF'
import sys
sys.path.insert(0, '/app/backend')
from app.config import settings

print(f"Rate Limit: {settings.RATE_LIMIT_REQUESTS} requests per {settings.RATE_LIMIT_WINDOW}s")
print(f"Max Response Size: {settings.MAX_RESPONSE_SIZE_MB} MB")
print(f"Request Timeout: {settings.REQUEST_TIMEOUT}s")
print(f"Rate Limiting Enabled: {settings.ENABLE_RATE_LIMITING}")

# Validate expected values
errors = []
if settings.RATE_LIMIT_REQUESTS != 60:
    errors.append(f"Expected RATE_LIMIT_REQUESTS=60, got {settings.RATE_LIMIT_REQUESTS}")
if settings.RATE_LIMIT_WINDOW != 60:
    errors.append(f"Expected RATE_LIMIT_WINDOW=60, got {settings.RATE_LIMIT_WINDOW}")
if settings.MAX_RESPONSE_SIZE_MB != 15:
    errors.append(f"Expected MAX_RESPONSE_SIZE_MB=15, got {settings.MAX_RESPONSE_SIZE_MB}")
if settings.REQUEST_TIMEOUT != 15:
    errors.append(f"Expected REQUEST_TIMEOUT=15, got {settings.REQUEST_TIMEOUT}")

if errors:
    print("\nConfiguration errors:")
    for error in errors:
        print(f"  ✗ {error}")
    sys.exit(1)
else:
    print("\n✓ All configuration values correct")
    sys.exit(0)
EOF

if python3 /tmp/test_config.py; then
    pass "Configuration values"
else
    fail "Configuration values"
fi
rm /tmp/test_config.py
echo ""

# Test 4: Rate Limiting
echo "Test 4: Rate Limiting"
echo "--------------------"
info "Making 65 rapid requests to test rate limiting..."

# Reset rate limiter by waiting a bit
sleep 2

# Make requests and count status codes
STATUS_200_COUNT=0
STATUS_403_COUNT=0
STATUS_429_COUNT=0

for i in {1..65}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: wiki.test.local" http://localhost:8001/ 2>/dev/null)
    
    case $HTTP_CODE in
        200)
            ((STATUS_200_COUNT++))
            ;;
        403)
            ((STATUS_403_COUNT++))
            ;;
        429)
            ((STATUS_429_COUNT++))
            ;;
    esac
    
    # Small delay to avoid overwhelming the system
    sleep 0.01
done

info "Results: 200=$STATUS_200_COUNT, 403=$STATUS_403_COUNT, 429=$STATUS_429_COUNT"

# We expect some 429 responses (rate limited)
if [ $STATUS_429_COUNT -gt 0 ]; then
    pass "Rate limiting activated (got $STATUS_429_COUNT rate limit responses)"
else
    fail "Rate limiting not working (expected 429 responses, got 0)"
fi
echo ""

# Test 5: Structured Logging
echo "Test 5: Structured Logging"
echo "-------------------------"
info "Checking for JSON-formatted logs..."

# Make a test request
curl -s -H "Host: wiki.test.local" http://localhost:8001/ > /dev/null 2>&1
sleep 1

# Check for JSON logs
JSON_LOG_COUNT=$(tail -50 /var/log/supervisor/backend.err.log | grep -c '^{' || true)

if [ $JSON_LOG_COUNT -gt 0 ]; then
    pass "JSON-formatted logs detected ($JSON_LOG_COUNT entries)"
    
    # Verify log structure
    LATEST_LOG=$(tail -50 /var/log/supervisor/backend.err.log | grep '^{' | tail -1)
    
    if echo "$LATEST_LOG" | grep -q '"timestamp"' && \
       echo "$LATEST_LOG" | grep -q '"level"' && \
       echo "$LATEST_LOG" | grep -q '"logger"' && \
       echo "$LATEST_LOG" | grep -q '"message"'; then
        pass "Log structure contains required fields"
    else
        fail "Log structure missing required fields"
    fi
else
    fail "No JSON-formatted logs found"
fi
echo ""

# Test 6: Proxy Functionality
echo "Test 6: Proxy Functionality"
echo "--------------------------"
info "Testing basic proxy with wikipedia..."

# Wait for rate limit to reset
info "Waiting 5 seconds for rate limit reset..."
sleep 5

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: wiki.test.local" http://localhost:8001/ 2>/dev/null)

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "403" ]; then
    pass "Proxy request completed (status: $HTTP_CODE)"
else
    fail "Proxy request failed (status: $HTTP_CODE)"
fi
echo ""

# Test 7: Log Analysis
echo "Test 7: Log Analysis"
echo "-------------------"
info "Analyzing recent logs for key metrics..."

# Check for latency measurements
LATENCY_LOGS=$(tail -100 /var/log/supervisor/backend.err.log | grep -c '"latency_ms"' || true)
if [ $LATENCY_LOGS -gt 0 ]; then
    pass "Latency measurements in logs ($LATENCY_LOGS entries)"
else
    fail "No latency measurements found in logs"
fi

# Check for client IP logging
CLIENT_IP_LOGS=$(tail -100 /var/log/supervisor/backend.err.log | grep -c '"client_ip"' || true)
if [ $CLIENT_IP_LOGS -gt 0 ]; then
    pass "Client IP logging ($CLIENT_IP_LOGS entries)"
else
    fail "No client IP found in logs"
fi

# Check for rate limit warnings
RATE_LIMIT_LOGS=$(tail -200 /var/log/supervisor/backend.err.log | grep -c 'Rate limit exceeded' || true)
if [ $RATE_LIMIT_LOGS -gt 0 ]; then
    pass "Rate limit warnings logged ($RATE_LIMIT_LOGS entries)"
else
    info "No rate limit warnings (this is OK if tests didn't trigger rate limits)"
fi
echo ""

# Test 8: Module Imports
echo "Test 8: Module Imports"
echo "---------------------"
info "Verifying Phase 9 modules can be imported..."

cat > /tmp/test_imports.py << 'EOF'
import sys
sys.path.insert(0, '/app/backend')

try:
    from app.core.security import is_safe_origin_url, validate_target_url
    print("✓ security module")
    
    from app.core.rate_limiter import InMemoryRateLimiter, get_rate_limiter, init_rate_limiter
    print("✓ rate_limiter module")
    
    # Test rate limiter functionality
    test_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=10)
    
    # Make 6 requests
    results = []
    for i in range(6):
        allowed, remaining = test_limiter.is_allowed("test_ip")
        results.append(allowed)
    
    # First 5 should be allowed, 6th should be denied
    if all(results[:5]) and not results[5]:
        print("✓ rate limiter logic")
    else:
        print(f"✗ rate limiter logic - results: {results}")
        sys.exit(1)
    
    print("\n✓ All imports and basic functionality working")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if python3 /tmp/test_imports.py; then
    pass "Module imports and functionality"
else
    fail "Module imports or functionality"
fi
rm /tmp/test_imports.py
echo ""

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Phase 9 implementation is working correctly:"
    echo "  ✓ SSRF protection blocking private IPs"
    echo "  ✓ Rate limiting active (60 req/min)"
    echo "  ✓ Structured JSON logging enabled"
    echo "  ✓ Configuration correct"
    echo "  ✓ Proxy functionality intact"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo "Please review the errors above and check:"
    echo "  - Backend logs: /var/log/supervisor/backend.err.log"
    echo "  - Configuration: /app/backend/.env"
    echo "  - Service status: sudo supervisorctl status"
    exit 1
fi
