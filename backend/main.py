"""Orion AI Full-Stack Backend - Main entry point."""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import init_db, close_db
from app.api import api_router
from app.websockets import websocket_chat

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OrionAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield
    await close_db()
    logger.info("Database closed")


app = FastAPI(
    title="Orion AI API",
    description="Multi-Agent AI Business Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}

# WebSocket
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket_chat(websocket, token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=not settings.is_production)
