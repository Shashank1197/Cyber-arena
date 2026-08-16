#!/usr/bin/env python3
"""Sanitize user-supplied display names."""
from __future__ import annotations

import re

MAX_NAME_LENGTH = 16
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_name(raw) -> str:
    if not isinstance(raw, str):
        return "Player"
    name = _CTRL.sub("", raw).strip()
    name = " ".join(name.split())
    if not name:
        return "Player"
    return name[:MAX_NAME_LENGTH]
