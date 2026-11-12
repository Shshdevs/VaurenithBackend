from collections.abc import Sequence

from fastapi import APIRouter


def build_development_entity_router(entity_routers: Sequence[APIRouter]) -> APIRouter:
    router = APIRouter()
    for entity_router in entity_routers:
        router.include_router(entity_router)
    return router


__all__ = ["build_development_entity_router"]
