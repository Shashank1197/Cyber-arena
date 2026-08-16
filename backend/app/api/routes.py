#!/usr/bin/env python3
"""REST endpoints for health, leaderboard and match history.

All real-time gameplay goes over the WebSocket; REST is only used for
persistence-facing reads and health checks.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..services.persistence import persistence

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": "Cyber Arena",
        "mongo": persistence.available,
    }


@router.get("/leaderboard")
async def leaderboard() -> dict:
    rows = await persistence.get_leaderboard()
    return {"leaderboard": rows}


@router.get("/players/{player_id}/history")
async def player_history(player_id: str) -> dict:
    rows = await persistence.get_match_history(player_id)
    return {"history": rows}
