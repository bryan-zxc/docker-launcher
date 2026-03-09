"""JSON metadata store for container history."""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path.home() / ".docker-launcher" / "containers.json"


def _load() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_last_opened(container_id: str) -> None:
    data = _load()
    if container_id not in data:
        data[container_id] = {}
    data[container_id]["last_opened_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)


def get_metadata(container_id: str) -> dict | None:
    data = _load()
    return data.get(container_id)


def delete_metadata(container_id: str) -> None:
    data = _load()
    if container_id in data:
        del data[container_id]
        _save(data)


def cleanup_orphans(live_ids: set[str]) -> None:
    data = _load()
    orphans = [k for k in data if k not in live_ids]
    if not orphans:
        return
    for k in orphans:
        del data[k]
    _save(data)
