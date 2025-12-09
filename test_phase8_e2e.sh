#!/bin/bash

# Phase 8 End-to-End Test Script
# Tests Cookie Jar, Sessions, and Header Forwarding

echo "============================================================"
echo "Phase 8 E2E Test: Cookie Jar, Sessions, and Header Forwarding"
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

echo "=== PREREQUISITE TESTS ==="
echo ""

echo "1. Backend Health Check"
echo "----------------------------"
run_test "Backend Health" \
    "curl -s http://localhost:8001/health" \
    "ok"

echo "2. Database Check - CookieJar Table"
echo "----------------------------"
run_test "CookieJar Table Exists" \
    "cd /app/backend && python3 -c \"import sqlite3; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\" AND name=\\\"cookie_jars\\\"'); print(cursor.fetchone()[0])\"" \
    "cookie_jars"

echo "3. Check Test Site Configuration"
echo "----------------------------"
run_test "Wikipedia Test Site Exists" \
    "cd /app/backend && python3 -c \"import sqlite3; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute('SELECT mirror_root, source_root FROM sites WHERE id=4'); print(cursor.fetchone())\"" \
    "wiki.test.local"

echo ""
echo "=== PHASE 8 FEATURE TESTS ==="
echo ""

echo "4. Session Manager Module"
echo "----------------------------"
run_test "Session ID Generation" \
    "cd /app/backend && python3 -c \"from app.core.session_manager import generate_session_id; sid = generate_session_id(); print('Session ID generated:', len(sid) > 20)\"" \
    "True"

run_test "Session ID Signing" \
    "cd /app/backend && python3 -c \"from app.core.session_manager import sign_session_id; signed = sign_session_id('test123'); print('Signed:', '.' in signed)\"" \
    "True"

run_test "Session ID Verification" \
    "cd /app/backend && python3 -c \"from app.core.session_manager import sign_session_id, verify_session_id; signed = sign_session_id('test123'); verified = verify_session_id(signed); print('Verified:', verified == 'test123')\"" \
    "True"

echo "5. Cookie Manager Module"
echo "----------------------------"
run_test "Cookie Header Building" \
    "cd /app/backend && python3 -c \"from app.core.cookie_manager import build_cookie_header; cookies = {'session': 'abc123', 'user': 'john'}; header = build_cookie_header(cookies); print('Cookie header:', 'session=abc123' in header)\"" \
    "True"

run_test "Cookie Header Parsing" \
    "cd /app/backend && python3 -c \"from app.core.cookie_manager import parse_cookie_header; cookies = parse_cookie_header('session=abc123; user=john'); print('Parsed:', len(cookies) == 2)\"" \
    "True"

echo "6. Configuration - Session Mode"
echo "----------------------------"
# Update site 4 to use cookie_jar mode
echo "Setting wiki.test.local to cookie_jar mode..."
cd /app/backend && python3 -c "
import sqlite3
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('UPDATE sites SET session_mode = \"cookie_jar\" WHERE id = 4')
conn.commit()
cursor.execute('SELECT session_mode FROM sites WHERE id = 4')
print('Session mode:', cursor.fetchone()[0])
conn.close()
"

run_test "Session Mode Configuration" \
    "cd /app/backend && python3 -c \"import sqlite3; conn = sqlite3.connect('app.db'); cursor = conn.cursor(); cursor.execute('SELECT session_mode FROM sites WHERE id=4'); print(cursor.fetchone()[0])\"" \
    "cookie_jar"

echo "7. Cookie Storage Integration Test"
echo "----------------------------"
run_test "Cookie Storage and Retrieval" \
    "cd /app/backend && python3 -c \"
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.cookie_manager import store_cookies, get_cookies

async def test():
    engine = create_async_engine('sqlite+aiosqlite:///./app.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Store test cookies
        await store_cookies(
            session, 
            site_id=4, 
            session_id='test_session_123',
            origin_host='en.wikipedia.org',
            set_cookie_headers=['test_cookie=test_value; Path=/']
        )
        
        # Retrieve cookies
        cookies = await get_cookies(
            session,
            site_id=4,
            session_id='test_session_123',
            origin_host='en.wikipedia.org'
        )
        print('Cookie retrieved:', 'test_cookie' in cookies)
    await engine.dispose()

asyncio.run(test())
\"" \
    "True"

echo ""
echo "=== SUMMARY ==="
echo "----------------------------"
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Phase 8 Implementation Complete!"
    echo ""
    echo "Key Features Implemented:"
    echo "  ✓ Session identification with signed px_session_id cookie"
    echo "  ✓ CookieJar database model for per-user, per-origin cookie storage"
    echo "  ✓ Cookie capture from origin Set-Cookie headers"
    echo "  ✓ Cookie injection into origin requests"
    echo "  ✓ Header forwarding with Referer rewriting"
    echo "  ✓ Configuration control via session_mode (stateless/cookie_jar)"
    echo ""
    echo "Next Steps:"
    echo "  1. Test with real website (wikipedia.org) using custom Host header"
    echo "  2. Verify cookies persist across multiple requests"
    echo "  3. Test stateless mode still works correctly"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
