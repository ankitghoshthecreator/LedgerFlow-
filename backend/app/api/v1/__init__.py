"""V1 API Package."""
from fastapi import APIRouter

from app.api.v1.applications import router as applications_router
from app.api.v1.rules import router as rules_router
from app.api.v1.status import router as status_router
from app.api.websocket import router as websocket_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(applications_router)
v1_router.include_router(status_router)
v1_router.include_router(rules_router)
v1_router.include_router(websocket_router)
