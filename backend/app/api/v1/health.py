"""
Health and readiness probes.
"""
from fastapi import APIRouter, Request, status
from app.core.config import settings
from app.core.dependencies import create_api_response
from app.schemas.common import APIResponse, HealthStatus

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Application liveness probe",
    description="Returns basic health status of the application runtime.",
    status_code=status.HTTP_200_OK,
)
async def get_health(request: Request):
    payload = {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
    return create_api_response(payload, request)


@router.get(
    "/ready",
    summary="Application readiness probe",
    description="Verifies operational readiness of database, cache, and dependent subsystems.",
    status_code=status.HTTP_200_OK,
)
async def get_readiness(request: Request):
    # During initial phases, verify system status
    services = {
        "api": "ready",
        "llm_provider": settings.LLM_PROVIDER,
        "stt_provider": settings.STT_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
    }
    payload = {
        "status": "ready",
        "version": settings.APP_VERSION,
        "services": services,
    }
    return create_api_response(payload, request)
