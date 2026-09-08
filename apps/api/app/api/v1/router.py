from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    debug,
    demo,
    health,
    investigations,
    orchestration,
    rag,
    reports,
)

api_router = APIRouter()

# Include auth endpoints (Phase 17)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])



# Include health check endpoints
api_router.include_router(health.router, tags=["health"])

# Include demo endpoints
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])

# Include investigations endpoints
api_router.include_router(investigations.router, prefix="/investigations", tags=["investigations"])
api_router.include_router(orchestration.router, prefix="/investigations", tags=["orchestration"])
api_router.include_router(reports.router, prefix="/investigations", tags=["reports"])

# Include RAG threat intelligence endpoints
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])

# Include debug endpoints
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])



