from fastapi import APIRouter

from .health import router as health_router


def build_router(prefix: str) -> APIRouter:
    router = APIRouter()
    router.include_router(health_router, prefix=prefix)
    return router
