from fastapi import APIRouter
from .auth import router as auth_router
from .conversations import router as conversations_router
from .reports import router as reports_router
from .payments import router as payments_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(conversations_router)
api_router.include_router(reports_router)
api_router.include_router(payments_router)
