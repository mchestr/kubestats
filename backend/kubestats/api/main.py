from fastapi import APIRouter

from kubestats.api.routes import admin, login, repositories, tasks

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(admin.router)
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["repositories"]
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
