#!/usr/bin/env python3
"""Cyber Arena backend entrypoint (FastAPI + WebSockets)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .config.settings import get_settings
from .websocket.endpoint import router as ws_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Cyber Arena backend starting (mongo=%s)", settings.mongo_enabled)
    yield
    log.info("Cyber Arena backend shutting down")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
async def root() -> dict:
    return {"app": settings.app_name, "status": "online"}
