from fastapi import APIRouter
from app.routes.health import router as health_router
from app.routes.tasks import router as tasks_router
from app.routes.gmail import router as gmail_router
from app.routes.tools import router as tools_router
from app.routes.approvals import router as approvals_router

__all__ = ["health_router", "tasks_router", "gmail_router", "tools_router", "approvals_router"]

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(tasks_router)
api_router.include_router(gmail_router)
api_router.include_router(tools_router)
api_router.include_router(approvals_router)
