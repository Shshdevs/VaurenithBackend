from fastapi import APIRouter


def build_router(
    prefix: str,
    health_router: APIRouter,
    identity_router: APIRouter,
    projects_router: APIRouter,
    infrastructure_router: APIRouter,
    synchronization_router: APIRouter,
) -> APIRouter:
    router = APIRouter()
    router.include_router(health_router, prefix=prefix)
    router.include_router(identity_router, prefix=prefix)
    router.include_router(projects_router, prefix=prefix)
    router.include_router(infrastructure_router, prefix=prefix)
    router.include_router(synchronization_router, prefix=prefix)
    return router
