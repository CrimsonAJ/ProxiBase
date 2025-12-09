"""
Phase 8 Integration Test
Tests the complete cookie jar flow with actual proxy requests
"""

import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.site import Site
from app.models.cookie_jar import CookieJar

async def test_cookie_jar_flow():
    """
    Test the complete cookie jar flow:
    1. Make first request without session cookie
    2. Verify px_session_id cookie is set
    3. Make second request with session cookie
    4. Verify cookies persist
    """
    print("=" * 60)
    print("Phase 8 Integration Test: Cookie Jar Flow")
    print("=" * 60)
    print()
    
    # Connect to database
    engine = create_async_engine('sqlite+aiosqlite:///./app.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get wiki.test.local site
        result = await session.execute(select(Site).where(Site.id == 4))
        site = result.scalar_one_or_none()
        
        if not site:
            print("❌ Test site not found")
            return False
        
        print(f"✓ Using test site: {site.mirror_root} -> {site.source_root}")
        print(f"  Session mode: {site.session_mode or 'using global default'}")
        print()
        
        # Clear any existing test cookies
        await session.execute(
            CookieJar.__table__.delete().where(
                CookieJar.origin_host == 'en.wikipedia.org'
            )
        )
        await session.commit()
        print("✓ Cleared existing test cookies")
        print()
    
    # Test 1: First request without cookies
    print("Test 1: First request (no session cookie)")
    print("-" * 60)
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            # Make request to proxy with wiki.test.local host header
            response = await client.get(
                "http://localhost:8001/wiki/Main_Page",
                headers={
                    "Host": "wiki.test.local",
                    "User-Agent": "ProxiBase-Test/1.0"
                },
                timeout=30.0
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # Check for px_session_id cookie
            px_session_id = response.cookies.get('px_session_id')
            if px_session_id:
                print(f"  ✓ px_session_id cookie set: {px_session_id[:20]}...")
            else:
                print("  ❌ px_session_id cookie NOT set")
                return False
            
            # Check if we got content
            if response.status_code == 200 or response.status_code == 301:
                print(f"  ✓ Got response from origin")
            else:
                print(f"  ⚠ Unexpected status code: {response.status_code}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            return False
    
    # Test 2: Check database for stored cookies (if Wikipedia set any)
    print("Test 2: Check database for stored cookies")
    print("-" * 60)
    
    async with async_session() as session:
        result = await session.execute(
            select(CookieJar).where(
                CookieJar.site_id == 4,
                CookieJar.origin_host == 'en.wikipedia.org'
            )
        )
        cookie_jars = result.scalars().all()
        
        print(f"  Found {len(cookie_jars)} cookie jar entries for en.wikipedia.org")
        
        for jar in cookie_jars:
            print(f"  - Session ID: {jar.session_id[:20]}...")
            print(f"    Cookie data: {jar.cookie_data[:100] if jar.cookie_data else 'None'}...")
        
        if len(cookie_jars) > 0:
            print("  ✓ Cookies stored in database")
        else:
            print("  ℹ No cookies stored (origin may not have set cookies)")
        
        print()
    
    # Test 3: Second request with session cookie
    print("Test 3: Second request (with session cookie)")
    print("-" * 60)
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            # Make second request with the session cookie
            cookies = {"px_session_id": px_session_id}
            
            response = await client.get(
                "http://localhost:8001/wiki/Python_(programming_language)",
                headers={
                    "Host": "wiki.test.local",
                    "User-Agent": "ProxiBase-Test/1.0"
                },
                cookies=cookies,
                timeout=30.0
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # Check that session cookie is still present
            px_session_id_2 = response.cookies.get('px_session_id')
            if px_session_id_2:
                print(f"  ℹ px_session_id cookie updated/refreshed")
            else:
                print(f"  ✓ px_session_id not re-set (good, using existing session)")
            
            if response.status_code == 200 or response.status_code == 301:
                print(f"  ✓ Got response from origin")
            else:
                print(f"  ⚠ Unexpected status code: {response.status_code}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            return False
    
    # Test 4: Verify stateless mode works
    print("Test 4: Verify stateless mode")
    print("-" * 60)
    
    async with async_session() as session:
        # Change site to stateless mode
        result = await session.execute(select(Site).where(Site.id == 4))
        site = result.scalar_one()
        site.session_mode = "stateless"
        await session.commit()
        print("  Set wiki.test.local to stateless mode")
    
    # Wait for hot reload
    await asyncio.sleep(2)
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        try:
            response = await client.get(
                "http://localhost:8001/wiki/Computer",
                headers={
                    "Host": "wiki.test.local",
                    "User-Agent": "ProxiBase-Test/1.0"
                },
                timeout=30.0
            )
            
            print(f"  Status: {response.status_code}")
            
            # In stateless mode, no session cookie should be set
            px_session_id_3 = response.cookies.get('px_session_id')
            if px_session_id_3:
                print(f"  ❌ px_session_id cookie set in stateless mode (should not be)")
                # Restore cookie_jar mode
                async with async_session() as session:
                    result = await session.execute(select(Site).where(Site.id == 4))
                    site = result.scalar_one()
                    site.session_mode = "cookie_jar"
                    await session.commit()
                return False
            else:
                print(f"  ✓ No px_session_id cookie in stateless mode (correct)")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Request failed: {e}")
            # Restore cookie_jar mode
            async with async_session() as session:
                result = await session.execute(select(Site).where(Site.id == 4))
                site = result.scalar_one()
                site.session_mode = "cookie_jar"
                await session.commit()
            return False
    
    # Restore cookie_jar mode
    async with async_session() as session:
        result = await session.execute(select(Site).where(Site.id == 4))
        site = result.scalar_one()
        site.session_mode = "cookie_jar"
        await session.commit()
        print("  ✓ Restored cookie_jar mode")
    
    print()
    print("=" * 60)
    print("✓ All integration tests passed!")
    print("=" * 60)
    
    await engine.dispose()
    return True


if __name__ == "__main__":
    result = asyncio.run(test_cookie_jar_flow())
    exit(0 if result else 1)
