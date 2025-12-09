"""
ProxiBase Server Entry Point

This module imports the FastAPI application from app.main and makes it
available for uvicorn to run.
"""

from app.main import app

# This allows uvicorn to run the app with: uvicorn server:app
__all__ = ["app"]