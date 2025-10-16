from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Updated default path as per requirements
DEFAULT_DIR = Path.home() / ".calctl"
DEFAULT_DB = DEFAULT_DIR / "events.json"


def _db_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = os.getenv("CALCTL_DB")  # Updated env var name
    if env:
        return Path(env).expanduser()
    return DEFAULT_DB


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def load_events(db_path: str | None = None) -> List[Dict[str, Any]]:
    p = _db_path(db_path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # Ensure each event is a dict
        return [e for e in data if isinstance(e, dict)]
    except json.JSONDecodeError:
        return []


def save_events(events: List[Dict[str, Any]], db_path: str | None = None) -> None:
    p = _db_path(db_path)
    _ensure_parent(p)
    with p.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
