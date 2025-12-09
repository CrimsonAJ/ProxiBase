from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.admin.auth import (
    verify_superadmin_credentials,
    create_session_token,
    get_current_admin,
    SESSION_COOKIE_NAME,
)
from app.config import settings
from app.db.session import get_db
from app.models.site import Site
from app.models.global_config import GlobalConfig

# Phase 9: Get logger for recent errors
logger = logging.getLogger("proxibase")

router = APIRouter()

# Templates
template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
templates = Jinja2Templates(directory=template_path)


def check_admin_host(request: Request):
    """Check if request is from admin host."""
    if request.headers.get("host") != settings.ADMIN_HOST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin panel not available on this host"
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login form."""
    check_admin_host(request)
    
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Process login form."""
    check_admin_host(request)
    
    # Verify credentials against env superadmin
    if not verify_superadmin_credentials(username, password):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Create session token
    token = create_session_token(username, role="superadmin")
    
    # Redirect to admin panel with session cookie
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400  # 24 hours
    )
    
    return response


@router.get("/logout")
async def logout():
    """Logout and clear session."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin panel home page (requires authentication)."""
    check_admin_host(request)
    
    # Get stats
    sites_count = await db.scalar(select(func.count(Site.id)))
    active_sites_count = await db.scalar(select(func.count(Site.id)).where(Site.enabled == True))
    
    return templates.TemplateResponse(
        "admin/panel.html",
        {
            "request": request,
            "admin": current_admin,
            "sites_count": sites_count or 0,
            "active_sites_count": active_sites_count or 0
        }
    )


# ==================== SITE MANAGEMENT ROUTES ====================

@router.get("/admin/sites", response_class=HTMLResponse)
async def list_sites(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all sites."""
    check_admin_host(request)
    
    # Get all sites
    result = await db.execute(select(Site).order_by(Site.id))
    sites = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/sites_list.html",
        {
            "request": request,
            "admin": current_admin,
            "sites": sites
        }
    )


@router.get("/admin/sites/create", response_class=HTMLResponse)
async def create_site_form(
    request: Request,
    current_admin: dict = Depends(get_current_admin)
):
    """Display create site form."""
    check_admin_host(request)
    
    return templates.TemplateResponse(
        "admin/site_form.html",
        {
            "request": request,
            "admin": current_admin,
            "site": None,
            "action": "create"
        }
    )


@router.post("/admin/sites/create")
async def create_site(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    mirror_root: str = Form(...),
    source_root: str = Form(...),
    enabled: bool = Form(True),
    proxy_subdomains: Optional[bool] = Form(None),
    proxy_external_domains: Optional[bool] = Form(None),
    rewrite_js_redirects: Optional[bool] = Form(None),
    remove_ads: Optional[bool] = Form(None),
    inject_ads: Optional[bool] = Form(None),
    remove_analytics: Optional[bool] = Form(None),
    media_policy: Optional[str] = Form(None),
    session_mode: Optional[str] = Form(None),
    custom_ad_html: Optional[str] = Form(None),
    custom_tracker_js: Optional[str] = Form(None)
):
    """Create a new site."""
    check_admin_host(request)
    
    # Check if mirror_root already exists
    result = await db.execute(select(Site).where(Site.mirror_root == mirror_root))
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "admin/site_form.html",
            {
                "request": request,
                "admin": current_admin,
                "site": None,
                "action": "create",
                "error": f"Site with mirror root '{mirror_root}' already exists"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new site
    new_site = Site(
        mirror_root=mirror_root,
        source_root=source_root,
        enabled=enabled,
        proxy_subdomains=proxy_subdomains,
        proxy_external_domains=proxy_external_domains,
        rewrite_js_redirects=rewrite_js_redirects,
        remove_ads=remove_ads,
        inject_ads=inject_ads,
        remove_analytics=remove_analytics,
        media_policy=media_policy if media_policy else None,
        session_mode=session_mode if session_mode else None,
        custom_ad_html=custom_ad_html if custom_ad_html else None,
        custom_tracker_js=custom_tracker_js if custom_tracker_js else None
    )
    
    db.add(new_site)
    await db.commit()
    await db.refresh(new_site)
    
    return RedirectResponse(url="/admin/sites", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/sites/{site_id}/edit", response_class=HTMLResponse)
async def edit_site_form(
    request: Request,
    site_id: int,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Display edit site form."""
    check_admin_host(request)
    
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return templates.TemplateResponse(
        "admin/site_form.html",
        {
            "request": request,
            "admin": current_admin,
            "site": site,
            "action": "edit"
        }
    )


@router.post("/admin/sites/{site_id}/edit")
async def update_site(
    request: Request,
    site_id: int,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    mirror_root: str = Form(...),
    source_root: str = Form(...),
    enabled: bool = Form(True),
    proxy_subdomains: Optional[bool] = Form(None),
    proxy_external_domains: Optional[bool] = Form(None),
    rewrite_js_redirects: Optional[bool] = Form(None),
    remove_ads: Optional[bool] = Form(None),
    inject_ads: Optional[bool] = Form(None),
    remove_analytics: Optional[bool] = Form(None),
    media_policy: Optional[str] = Form(None),
    session_mode: Optional[str] = Form(None),
    custom_ad_html: Optional[str] = Form(None),
    custom_tracker_js: Optional[str] = Form(None)
):
    """Update an existing site."""
    check_admin_host(request)
    
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Check if mirror_root is being changed and if it conflicts
    if site.mirror_root != mirror_root:
        result = await db.execute(select(Site).where(Site.mirror_root == mirror_root))
        if result.scalar_one_or_none():
            return templates.TemplateResponse(
                "admin/site_form.html",
                {
                    "request": request,
                    "admin": current_admin,
                    "site": site,
                    "action": "edit",
                    "error": f"Site with mirror root '{mirror_root}' already exists"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # Update site
    site.mirror_root = mirror_root
    site.source_root = source_root
    site.enabled = enabled
    site.proxy_subdomains = proxy_subdomains
    site.proxy_external_domains = proxy_external_domains
    site.rewrite_js_redirects = rewrite_js_redirects
    site.remove_ads = remove_ads
    site.inject_ads = inject_ads
    site.remove_analytics = remove_analytics
    site.media_policy = media_policy if media_policy else None
    site.session_mode = session_mode if session_mode else None
    site.custom_ad_html = custom_ad_html if custom_ad_html else None
    site.custom_tracker_js = custom_tracker_js if custom_tracker_js else None
    
    await db.commit()
    
    return RedirectResponse(url="/admin/sites", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/sites/{site_id}/delete")
async def delete_site(
    site_id: int,
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a site."""
    check_admin_host(request)
    
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await db.delete(site)
    await db.commit()
    
    return RedirectResponse(url="/admin/sites", status_code=status.HTTP_303_SEE_OTHER)


# ==================== GLOBAL CONFIG ROUTES ====================

@router.get("/admin/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Display global config settings."""
    check_admin_host(request)
    
    # Get or create GlobalConfig (id=1)
    result = await db.execute(select(GlobalConfig).where(GlobalConfig.id == 1))
    config = result.scalar_one_or_none()
    
    if not config:
        # Create default global config if it doesn't exist
        config = GlobalConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "admin": current_admin,
            "config": config
        }
    )


@router.post("/admin/settings")
async def update_settings(
    request: Request,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    proxy_subdomains: bool = Form(False),
    proxy_external_domains: bool = Form(False),
    rewrite_js_redirects: bool = Form(False),
    remove_ads: bool = Form(False),
    inject_ads: bool = Form(False),
    remove_analytics: bool = Form(False),
    media_policy: str = Form("proxy"),
    session_mode: str = Form("stateless"),
    custom_ad_html: Optional[str] = Form(None),
    custom_tracker_js: Optional[str] = Form(None)
):
    """Update global config settings."""
    check_admin_host(request)
    
    # Get or create GlobalConfig
    result = await db.execute(select(GlobalConfig).where(GlobalConfig.id == 1))
    config = result.scalar_one_or_none()
    
    if not config:
        config = GlobalConfig(id=1)
        db.add(config)
    
    # Update settings
    config.proxy_subdomains = proxy_subdomains
    config.proxy_external_domains = proxy_external_domains
    config.rewrite_js_redirects = rewrite_js_redirects
    config.remove_ads = remove_ads
    config.inject_ads = inject_ads
    config.remove_analytics = remove_analytics
    config.media_policy = media_policy
    config.session_mode = session_mode
    config.custom_ad_html = custom_ad_html if custom_ad_html else None
    config.custom_tracker_js = custom_tracker_js if custom_tracker_js else None
    
    await db.commit()
    
    return RedirectResponse(url="/admin/settings", status_code=status.HTTP_303_SEE_OTHER)


# ==================== PHASE 9: DASHBOARD STATISTICS API ====================

@router.get("/admin/api/stats")
async def get_dashboard_stats(
    current_admin: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 9: API endpoint for dashboard statistics.
    Returns total sites, active sites, and system configuration.
    """
    # Get site counts
    total_sites = await db.scalar(select(func.count(Site.id)))
    active_sites = await db.scalar(select(func.count(Site.id)).where(Site.enabled == True))
    
    # Get all sites for detailed view
    result = await db.execute(select(Site).order_by(Site.id))
    sites = result.scalars().all()
    
    # Get global config
    config_result = await db.execute(select(GlobalConfig).where(GlobalConfig.id == 1))
    global_config = config_result.scalar_one_or_none()
    
    # Build response
    return JSONResponse({
        "total_sites": total_sites or 0,
        "active_sites": active_sites or 0,
        "inactive_sites": (total_sites or 0) - (active_sites or 0),
        "rate_limit_config": {
            "enabled": settings.ENABLE_RATE_LIMITING,
            "max_requests": settings.RATE_LIMIT_REQUESTS,
            "window_seconds": settings.RATE_LIMIT_WINDOW
        },
        "limits": {
            "max_response_size_mb": settings.MAX_RESPONSE_SIZE_MB,
            "request_timeout_seconds": settings.REQUEST_TIMEOUT
        },
        "sites": [
            {
                "id": site.id,
                "mirror_root": site.mirror_root,
                "source_root": site.source_root,
                "enabled": site.enabled,
                "session_mode": site.session_mode
            }
            for site in sites
        ],
        "global_config": {
            "proxy_subdomains": global_config.proxy_subdomains if global_config else None,
            "remove_ads": global_config.remove_ads if global_config else None,
            "session_mode": global_config.session_mode if global_config else None
        } if global_config else None
    })
