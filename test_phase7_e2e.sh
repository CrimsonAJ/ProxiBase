#!/bin/bash

# Phase 7 End-to-End Test Script
# Tests JS & CSS URL + Redirect Handling

echo "============================================================"
echo "Phase 7 E2E Test: JS & CSS URL + Redirect Handling"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo "Test: $test_name"
    echo "Command: $test_command"
    
    result=$(eval "$test_command" 2>&1)
    
    if echo "$result" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "Expected pattern: $expected_pattern"
        echo "Result: $result"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

echo "1. Testing Backend Health"
echo "----------------------------"
run_test "Backend Health Check" \
    "curl -s http://localhost:8001/health" \
    "ok"

echo "2. Testing Rewriter Module Import"
echo "-----------------------------------"
run_test "Import rewriter functions" \
    "cd /app/backend && python3 -c 'from app.proxy.rewriter import rewrite_js_redirects, rewrite_css_urls; print(\"success\")'" \
    "success"

echo "3. Testing JS Redirect Rewriting"
echo "----------------------------------"
run_test "JS window.location.href rewriting" \
    "cd /app/backend && python3 -c \"from app.proxy.rewriter import rewrite_js_redirects; js='window.location.href=\\\"https://en.wikipedia.org/test\\\";'; result=rewrite_js_redirects(js, 'https://en.wikipedia.org/', 'wiki.test.local', 'wiki.test.local', 'en.wikipedia.org', {'rewrite_js_redirects': True}); print(result)\"" \
    "wiki.test.local"

run_test "JS location.replace rewriting" \
    "cd /app/backend && python3 -c \"from app.proxy.rewriter import rewrite_js_redirects; js='location.replace(\\\"https://en.wikipedia.org/test\\\");'; result=rewrite_js_redirects(js, 'https://en.wikipedia.org/', 'wiki.test.local', 'wiki.test.local', 'en.wikipedia.org', {'rewrite_js_redirects': True}); print(result)\"" \
    "wiki.test.local"

echo "4. Testing CSS URL Rewriting"
echo "------------------------------"
run_test "CSS url() rewriting" \
    "cd /app/backend && python3 -c \"from app.proxy.rewriter import rewrite_css_urls; css='background: url(\\\"/images/bg.jpg\\\");'; result=rewrite_css_urls(css, 'https://en.wikipedia.org/', 'wiki.test.local', 'wiki.test.local', 'en.wikipedia.org', {'media_policy': 'proxy'}); print(result)\"" \
    "wiki.test.local"

echo "5. Testing HTML Integration"
echo "----------------------------"
run_test "Complete HTML rewriting with JS and CSS" \
    "cd /app/backend && python3 -c \"from app.proxy.rewriter import rewrite_html; html='<script>window.location.href=\\\"/test\\\";</script><style>body{background:url(\\\"/bg.jpg\\\");}</style>'; result=rewrite_html(html, 'wiki.test.local', 'wiki.test.local', 'en.wikipedia.org', {'rewrite_js_redirects': True, 'media_policy': 'proxy', 'proxy_external_domains': True}, 'https://en.wikipedia.org/'); print(result)\"" \
    "wiki.test.local"

echo "6. Testing Configuration Flag"
echo "-------------------------------"
run_test "JS rewriting disabled when config is False" \
    "cd /app/backend && python3 -c \"from app.proxy.rewriter import rewrite_html; html='<script>window.location.href=\\\"https://en.wikipedia.org/test\\\";</script>'; result=rewrite_html(html, 'wiki.test.local', 'wiki.test.local', 'en.wikipedia.org', {'rewrite_js_redirects': False}, 'https://en.wikipedia.org/'); success='yes' if 'en.wikipedia.org/test' in result else 'no'; print(success)\"" \
    "yes"

echo "7. Running Unit Tests"
echo "----------------------"
run_test "Phase 7 unit test suite" \
    "cd /app/backend && python3 test_phase7.py 2>&1" \
    "All Phase 7 tests completed successfully"

echo "============================================================"
echo "Test Summary"
echo "============================================================"
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All Phase 7 tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review.${NC}"
    exit 1
fi
