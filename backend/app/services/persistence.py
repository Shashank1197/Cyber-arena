#!/usr/bin/env python3
"""Persistence layer for players and match history.

Real-time game state lives in server memory only. MongoDB is used purely for
long-lived records (players, matches, per-player results). When MongoDB is not
configured/available the service transparently falls back to an in-memory
repository so the game still runs locally with zero setup.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from ..config.settings import get_settings

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PersistenceService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._mongo = None
        self._db = None
        self._mem_players: dict[str, dict] = {}
        self._mem_matches: list[dict] = []
        self._mem_results: list[dict] = []
        self.available = self._connect()

    def _connect(self) -> bool:
        if not self.settings.mongo_enabled:
            log.info("MongoDB not configured - using in-memory persistence")
            return False
        try:
            import motor.motor_asyncio as motor  # noqa: PLC0415

            self._mongo = motor.AsyncIOMotorClient(
                self.settings.mongodb_url, serverSelectionTimeoutMS=1500
            )
            self._db = self._mongo[self.settings.mongodb_db]
            return True
        except Exception as exc:  # pragma: no cover - depends on runtime env
            log.warning("Failed to connect to MongoDB (%s); using in-memory", exc)
            return False

    # ------------------------------------------------------------- players
    async def upsert_player(self, player_id: str, name: str) -> None:
        doc = {
            "player_id": player_id,
            "name": name,
            "updated_at": _now(),
        }
        if self.available:
            await self._db["players"].update_one(
                {"player_id": player_id}, {"$set": doc}, upsert=True
            )
        else:
            self._mem_players[player_id] = doc

    # ------------------------------------------------------------- results
    async def record_match_result(self, room_code: str, result: dict) -> None:
        now = _now()
        match_doc = {
            "room_code": room_code,
            "started_at": now,
            "duration": result.get("match_duration", 0),
        }
        result_doc = {
            "room_code": room_code,
            "player_id": result.get("player_id"),
            "player_name": result.get("player_name"),
            "score": result.get("score"),
            "kills": result.get("kills"),
            "deaths": result.get("deaths"),
            "nodes_captured": result.get("nodes_captured"),
            "match_duration": result.get("match_duration"),
            "created_at": now,
        }
        if self.available:
            await self._db["matches"].insert_one(match_doc)
            await self._db["match_results"].insert_one(result_doc)
        else:
            self._mem_matches.append(match_doc)
            self._mem_results.append(result_doc)

    # ------------------------------------------------------------- history
    async def get_match_history(self, player_id: Optional[str] = None) -> list[dict]:
        if self.available:
            q = {} if player_id is None else {"player_id": player_id}
            cursor = (
                self._db["match_results"].find(q).sort("created_at", -1).limit(50)
            )
            out = []
            async for doc in cursor:
                doc.pop("_id", None)
                out.append(doc)
            return out
        results = list(self._mem_results)
        if player_id is not None:
            results = [r for r in results if r.get("player_id") == player_id]
        results.sort(key=lambda r: r.get("created_at", datetime.min), reverse=True)
        return results[:50]

    async def get_leaderboard(self, limit: int = 10) -> list[dict]:
        if self.available:
            pipeline = [
                {
                    "$group": {
                        "_id": "$player_name",
                        "player_id": {"$last": "$player_id"},
                        "matches": {"$sum": 1},
                        "score": {"$sum": "$score"},
                        "kills": {"$sum": "$kills"},
                        "deaths": {"$sum": "$deaths"},
                    }
                },
                {"$sort": {"score": -1}},
                {"$limit": limit},
            ]
            out = []
            async for doc in self._db["match_results"].aggregate(pipeline):
                out.append(
                    {
                        "player_name": doc["_id"],
                        "player_id": doc.get("player_id"),
                        "matches": doc["matches"],
                        "score": doc["score"],
                        "kills": doc["kills"],
                        "deaths": doc["deaths"],
                    }
                )
            return out
        agg: dict[str, dict] = {}
        for r in self._mem_results:
            key = r.get("player_name")
            entry = agg.setdefault(
                key,
                {
                    "player_name": key,
                    "player_id": r.get("player_id"),
                    "matches": 0,
                    "score": 0,
                    "kills": 0,
                    "deaths": 0,
                },
            )
            entry["matches"] += 1
            entry["score"] += r.get("score", 0)
            entry["kills"] += r.get("kills", 0)
            entry["deaths"] += r.get("deaths", 0)
        ranked = sorted(agg.values(), key=lambda e: e["score"], reverse=True)[:limit]
        return ranked


persistence = PersistenceService()
