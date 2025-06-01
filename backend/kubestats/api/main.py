from fastapi import APIRouter

from kubestats.api.routes import login, repositories, tasks, users, utils

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["repositories"]
)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
