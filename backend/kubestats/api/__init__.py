from fastapi import APIRouter

from kubestats.api.routes import (
    admin,
    ecosystem,
    kubernetes,
    login,
    repositories,
    tasks,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["repositories"]
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(ecosystem.router, prefix="/ecosystem", tags=["ecosystem"])
api_router.include_router(kubernetes.router, prefix="/kubernetes", tags=["kubernetes"])
