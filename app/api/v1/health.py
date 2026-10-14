"""Health check endpoint.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> Dict[str, Any]:
    """Return health status, project metadata, and server timestamp."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
