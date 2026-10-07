from fastapi import APIRouter

from .health import router as health_router
from .dashboard import router as dashboard_router
from .search_profiles import router as profiles_router
from .leads import router as leads_router
from .scan import router as scan_router
from .drafts import router as drafts_router
from .settings import router as settings_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(profiles_router, prefix="/profiles", tags=["Search Profiles"])
api_router.include_router(leads_router, prefix="/leads", tags=["Leads"])
api_router.include_router(scan_router, prefix="/scan", tags=["Scanning"])
api_router.include_router(drafts_router, prefix="/drafts", tags=["AI Drafts"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
