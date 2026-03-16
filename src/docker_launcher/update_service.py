"""Auto-update service: version checking, download, and state persistence."""

import json
import logging
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

GITHUB_REPO = "bryan-zxc/docker-launcher"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_FILE = Path.home() / ".docker-launcher" / "update.json"
CHECK_INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse version string like 'v0.2.0' or '0.2.0' into a comparable tuple."""
    v = v.lstrip("v")
    parts: list[int] = []
    for part in v.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _current_version() -> str:
    """Return current app version string."""
    try:
        return pkg_version("docker-launcher")
    except Exception:
        logger.warning("Could not determine app version — update checks disabled")
        return "dev"


# ---------------------------------------------------------------------------
# State persistence (atomic JSON, same pattern as database.py)
# ---------------------------------------------------------------------------


def _load_state() -> dict:
    """Load update state from ~/.docker-launcher/update.json."""
    if not UPDATE_FILE.exists():
        return {}
    try:
        with open(UPDATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Corrupt update.json — returning empty state")
        return {}


def _save_state(data: dict) -> None:
    """Atomically save update state."""
    UPDATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=UPDATE_FILE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, UPDATE_FILE)
    except BaseException:
        os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# GitHub Releases API
# ---------------------------------------------------------------------------


def _check_github_releases() -> dict | None:
    """Query GitHub Releases API for the latest release. Returns None on failure."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "docker-launcher",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        release_url = data.get("html_url", "")
        download_url = ""
        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".zip"):
                download_url = asset.get("browser_download_url", "")
                break

        if not tag or not download_url:
            return None

        return {
            "latest_version": tag.lstrip("v"),
            "release_url": release_url,
            "download_url": download_url,
        }
    except Exception:
        logger.warning("GitHub release check failed", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Core update check
# ---------------------------------------------------------------------------


def check_for_update() -> dict:
    """Perform update check against GitHub. Returns the full state dict."""
    current = _current_version()
    state = _load_state()

    release = _check_github_releases()
    if release is None:
        # Network failure: keep existing state, update timestamp
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        state["current_version"] = current
        _save_state(state)
        return state

    latest = release["latest_version"]
    update_available = current != "dev" and _parse_version(current) < _parse_version(
        latest
    )

    state.update(
        {
            "last_check": datetime.now(timezone.utc).isoformat(),
            "current_version": current,
            "latest_version": latest,
            "update_available": update_available,
            "release_url": release["release_url"],
            "download_url": release["download_url"],
        }
    )
    # Preserve existing download_path and downloaded_version
    _save_state(state)
    return state


def get_update_state() -> dict:
    """Return cached update state for the API endpoint."""
    state = _load_state()
    current = _current_version()
    state["current_version"] = current

    downloaded_version = state.get("downloaded_version")
    download_path = state.get("download_path")
    if downloaded_version and download_path:
        if (
            Path(download_path).exists()
            and current != "dev"
            and (_parse_version(current) < _parse_version(downloaded_version))
        ):
            state["download_ready"] = True
        else:
            state["download_ready"] = False
    else:
        state["download_ready"] = False

    return state


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def _get_download_dir() -> Path:
    """Determine directory to save the downloaded update zip.

    PyInstaller: next to the docker-launcher folder (parent of exe's parent).
    Dev mode: ~/.docker-launcher/
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys.executable).resolve().parent.parent
    return Path.home() / ".docker-launcher"


def download_update() -> Generator[str, None, None]:
    """Download the latest release zip. Yields SSE progress lines."""
    state = _load_state()
    download_url = state.get("download_url")
    latest_version = state.get("latest_version")

    if not download_url or not latest_version:
        yield "ERROR: No update available to download"
        return

    download_dir = _get_download_dir()
    download_dir.mkdir(parents=True, exist_ok=True)
    zip_filename = f"docker-launcher-v{latest_version}.zip"
    zip_path = download_dir / zip_filename

    yield f"Downloading v{latest_version}..."

    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "docker-launcher"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            total = resp.headers.get("Content-Length")
            total_bytes = int(total) if total else None
            downloaded = 0
            chunk_size = 64 * 1024

            fd, tmp_path = tempfile.mkstemp(dir=download_dir, suffix=".tmp")
            try:
                with os.fdopen(fd, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_bytes:
                            pct = int(downloaded * 100 / total_bytes)
                            yield f"PROGRESS: {pct}"
                        else:
                            yield f"PROGRESS: {downloaded}"
                os.replace(tmp_path, zip_path)
            except BaseException:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
    except Exception as e:
        yield f"ERROR: Download failed: {e}"
        return

    state["downloaded_version"] = latest_version
    state["download_path"] = str(zip_path)
    _save_state(state)

    yield f"DONE: {zip_path}"


# ---------------------------------------------------------------------------
# Background checker thread
# ---------------------------------------------------------------------------

_bg_thread: threading.Thread | None = None


def start_background_checker() -> None:
    """Start a daemon thread that checks for updates on startup then every 24h."""
    global _bg_thread
    if _bg_thread is not None and _bg_thread.is_alive():
        return

    def _loop() -> None:
        while True:
            try:
                check_for_update()
                logger.info("Update check completed")
            except Exception:
                logger.warning("Background update check failed", exc_info=True)
            time.sleep(CHECK_INTERVAL_SECONDS)

    _bg_thread = threading.Thread(target=_loop, daemon=True, name="update-checker")
    _bg_thread.start()
