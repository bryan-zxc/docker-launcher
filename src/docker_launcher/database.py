"""JSON metadata store for container history."""

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_FILE = Path.home() / ".docker-launcher" / "containers.json"
SETTINGS_FILE = Path.home() / ".docker-launcher" / "settings.json"


def _load() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning("Corrupt containers.json — returning empty store")
        return {}
    except OSError:
        logger.warning("Could not read containers.json", exc_info=True)
        return {}


def _save(data: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, DATA_FILE)
    except BaseException:
        os.unlink(tmp_path)
        raise


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


# --- Settings ---


def _load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupt settings.json — returning empty")
        return {}


def _save_settings(data: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=SETTINGS_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, SETTINGS_FILE)
    except BaseException:
        os.unlink(tmp_path)
        raise


def get_settings() -> dict:
    return _load_settings()


def save_settings(settings: dict) -> dict:
    current = _load_settings()
    current.update(settings)
    _save_settings(current)
    return current


def get_git_identity() -> tuple[str, str] | None:
    """Return (name, email) if configured, else None."""
    s = _load_settings()
    name = s.get("git_name", "").strip()
    email = s.get("git_email", "").strip()
    if name and email:
        return (name, email)
    return None
