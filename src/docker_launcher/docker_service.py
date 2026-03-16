"""Docker image and container management via Docker SDK."""

import hashlib
import json
import logging
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import docker
import docker.errors
import docker.types

from docker_launcher.database import (
    cleanup_orphans,
    delete_metadata,
    get_git_identity,
    get_metadata,
    update_last_opened,
)

# In a PyInstaller bundle, data files are extracted to sys._MEIPASS
_BASE_DIR = Path(
    getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent.parent)
)
IMAGES_DIR = _BASE_DIR / "images"

logger = logging.getLogger(__name__)


def _get_gh_token() -> str | None:
    """Extract the GitHub token from the host's gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _get_gh_username() -> str | None:
    """Get the authenticated GitHub username from the host's gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _get_claude_oauth_token() -> str | None:
    """Resolve the Claude Code OAuth token.

    Priority:
      1. Host env var CLAUDE_CODE_OAUTH_TOKEN (power-user override)
      2. Build-time default baked into the exe by CI
      3. None (container will require interactive login)
    """
    import os

    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if token:
        return token

    try:
        from docker_launcher._auth_defaults import (
            CLAUDE_CODE_OAUTH_TOKEN,
        )

        if CLAUDE_CODE_OAUTH_TOKEN:
            return CLAUDE_CODE_OAUTH_TOKEN
    except ImportError:
        pass

    return None


IMAGE_PREFIX = "docker-launcher"
CONTAINER_LABEL = "docker-launcher"

CONTAINER_ENV = {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/node/.claude",
    "POWERLEVEL9K_DISABLE_GITSTATUS": "true",
}


class DockerNotAvailableError(Exception):
    pass


_client: docker.DockerClient | None = None


def _get_client() -> docker.DockerClient:
    global _client
    if _client is not None:
        try:
            _client.ping()
        except Exception:
            logger.info("Docker connection stale, reconnecting")
            _client = None
    if _client is None:
        try:
            _client = docker.from_env()
            _client.ping()
        except docker.errors.DockerException as e:
            _client = None
            raise DockerNotAvailableError(
                "Docker Desktop is not running. Please start Docker Desktop and try again."
            ) from e
    return _client


CONTEXT_HASH_LABEL = f"{CONTAINER_LABEL}.context-hash"


def _build_context_hash(image_dir: Path) -> str:
    """Hash all files in the build context to detect changes."""
    h = hashlib.sha256()
    for f in sorted(image_dir.rglob("*")):
        if not f.is_file():
            continue
        h.update(str(f.relative_to(image_dir)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def _image_built_at(name: str) -> str | None:
    """Return ISO timestamp of when the image was created, or None if not built."""
    tag = f"{IMAGE_PREFIX}/{name}:latest"
    try:
        img = _get_client().images.get(tag)
        return img.attrs.get("Created", "")
    except docker.errors.ImageNotFound:
        return None


def container_name_available(name: str) -> bool:
    """Check if a container name is available (not already in use)."""
    container_name = f"docker-launcher-{name}"
    try:
        _get_client().containers.get(container_name)
        return False
    except docker.errors.NotFound:
        return True
    except docker.errors.APIError:
        return True


def _image_is_built(name: str) -> bool:
    """Check if a Docker image tag exists locally."""
    tag = f"{IMAGE_PREFIX}/{name}:latest"
    try:
        _get_client().images.get(tag)
        return True
    except docker.errors.ImageNotFound:
        return False


def _image_needs_rebuild(name: str) -> bool:
    """Check if the image needs rebuilding due to context changes or age."""
    tag = f"{IMAGE_PREFIX}/{name}:latest"
    try:
        img = _get_client().images.get(tag)
    except docker.errors.ImageNotFound:
        return True

    # Check if build context has changed
    image_dir = IMAGES_DIR / name
    if image_dir.is_dir():
        current_hash = _build_context_hash(image_dir)
        labels = img.labels or {}
        stored_hash = labels.get(CONTEXT_HASH_LABEL, "")
        if current_hash != stored_hash:
            return True

    # Check age (>7 days)
    created = img.attrs.get("Created", "")
    if created:
        try:
            built_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - built_dt).days
            if age_days > 7:
                return True
        except (ValueError, TypeError):
            return True

    return False


def _read_metadata(image_dir: Path) -> dict | None:
    """Read and parse metadata.json from an image directory."""
    metadata_path = image_dir / "metadata.json"
    if not metadata_path.exists():
        return None
    try:
        with open(metadata_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read %s", metadata_path, exc_info=True)
        return None


def list_images() -> list[dict]:
    """Scan images/ directory and return available image definitions."""
    results = []
    if not IMAGES_DIR.exists():
        return results
    for entry in sorted(IMAGES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        metadata = _read_metadata(entry)
        if metadata is None:
            continue
        results.append(
            {
                "id": entry.name,
                **metadata,
                "built": _image_is_built(entry.name),
                "built_at": _image_built_at(entry.name),
                "needs_rebuild": _image_needs_rebuild(entry.name),
            }
        )
    return results


def get_image(name: str) -> dict | None:
    """Get a single image definition by name."""
    image_dir = IMAGES_DIR / name
    if not image_dir.is_dir():
        return None
    metadata = _read_metadata(image_dir)
    if metadata is None:
        return None
    return {
        "id": name,
        **metadata,
        "built": _image_is_built(name),
        "built_at": _image_built_at(name),
        "needs_rebuild": _image_needs_rebuild(name),
    }


def _ensure_installer(name: str) -> None:
    """Ensure claude-install.sh is present before Docker build.

    .exe: installer is bundled at release time, nothing to do.
    Source: always try to download fresh; fall back to existing copy.
    """
    if getattr(sys, "_MEIPASS", None):
        return
    image_dir = IMAGES_DIR / name
    installer = image_dir / "assets" / "claude-install.sh"
    fetch_script = image_dir / "assets" / "fetch-claude-installer.ps1"
    if not fetch_script.exists():
        return
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(fetch_script),
            ],
            check=True,
        )
    except subprocess.CalledProcessError:
        if installer.exists():
            return
        raise


def build_image(name: str, force: bool = False) -> Generator[str, None, None]:
    """Build a Docker image, yielding log lines for streaming."""
    image_dir = IMAGES_DIR / name
    if not image_dir.is_dir():
        yield f"ERROR: Image definition '{name}' not found"
        return

    tag = f"{IMAGE_PREFIX}/{name}:latest"

    if not force and _image_is_built(name):
        yield f"Image {tag} already built. Use force=true to rebuild."
        return

    try:
        _ensure_installer(name)
    except subprocess.CalledProcessError as e:
        yield f"ERROR: Failed to download installer: {e}"
        return

    context_hash = _build_context_hash(image_dir)

    yield f"Building {tag} from {image_dir}..."

    try:
        resp = _get_client().api.build(
            path=str(image_dir),
            tag=tag,
            labels={CONTEXT_HASH_LABEL: context_hash},
            decode=True,
            rm=True,
        )
        for chunk in resp:
            if "stream" in chunk:
                line = chunk["stream"].rstrip("\n")
                if line:
                    yield line
            elif "status" in chunk:
                msg = chunk["status"]
                if "progress" in chunk:
                    msg += f" {chunk['progress']}"
                yield msg
            elif "error" in chunk:
                yield f"ERROR: {chunk['error']}"
                return
    except docker.errors.BuildError as e:
        yield f"ERROR: Build failed: {e}"
        return
    except docker.errors.APIError as e:
        yield f"ERROR: Docker API error: {e}"
        return

    yield f"Build complete: {tag}"


# ---------------------------------------------------------------------------
# Container management
# ---------------------------------------------------------------------------


def _container_info(container) -> dict:
    """Extract info dict from a Docker container object."""
    labels = container.labels or {}
    return {
        "id": container.short_id,
        "full_id": container.id,
        "name": container.name,
        "image": labels.get(f"{CONTAINER_LABEL}.image", ""),
        "repo_url": labels.get(f"{CONTAINER_LABEL}.repo", ""),
        "created_at": labels.get(f"{CONTAINER_LABEL}.created", ""),
        "status": container.status,
    }


def list_containers() -> list[dict]:
    """List all containers managed by this app."""
    containers = _get_client().containers.list(
        all=True, filters={"label": CONTAINER_LABEL}
    )
    results = [_container_info(c) for c in containers]

    live_ids = {r["full_id"] for r in results}
    cleanup_orphans(live_ids)

    for r in results:
        meta = get_metadata(r["full_id"])
        r["last_opened_at"] = meta.get("last_opened_at") if meta else None

    return results


def create_container(
    image_name: str,
    repo_url: str | None = None,
    name: str | None = None,
) -> dict:
    """Create and start a new container from a built image."""
    tag = f"{IMAGE_PREFIX}/{image_name}:latest"

    git_identity = get_git_identity()
    if not git_identity:
        raise ValueError(
            "Git identity not configured."
            " Go to Prerequisites and set your name and email."
        )

    if _get_gh_token() is None:
        raise ValueError("GitHub not authenticated. Go to Prerequisites and sign in.")

    if not _image_is_built(image_name):
        raise ValueError(f"Image '{image_name}' is not built. Build it first.")

    # Derive name from repo URL if not provided (clone mode)
    if not name and repo_url:
        name = repo_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    if not name:
        raise ValueError("Project name is required.")

    # Sanitise name for use as container name and repo name
    sanitised_name = "".join(c for c in name if c.isalnum() or c in "-_.")
    if not sanitised_name:
        sanitised_name = "project"

    # If no repo_url, auto-create a private GitHub repo
    auto_created_repo = False
    if not repo_url:
        gh_user = _get_gh_username()
        if not gh_user:
            raise ValueError(
                "Could not determine GitHub username. Ensure gh is authenticated."
            )

        create_result = subprocess.run(
            ["gh", "repo", "create", sanitised_name, "--private"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if create_result.returncode != 0:
            err_msg = (
                create_result.stderr.strip()
                or create_result.stdout.strip()
                or "Unknown error"
            )
            raise ValueError(f"Failed to create GitHub repo: {err_msg}")

        repo_url = f"https://github.com/{gh_user}/{sanitised_name}.git"
        auto_created_repo = True
        logger.info("Auto-created GitHub repo: %s", repo_url)

    # Derive workspace dir from repo URL
    repo_name = repo_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    repo_name = "".join(c for c in repo_name if c.isalnum() or c in "-_.")
    if not repo_name:
        repo_name = "repo"
    workspace_dir = f"/workspaces/{repo_name}"

    container_name = f"docker-launcher-{sanitised_name}"

    mounts = [
        docker.types.Mount(
            target="/home/node/.claude",
            source=f"{container_name}-claude-config",
            type="volume",
        ),
        docker.types.Mount(
            target="/commandhistory",
            source=f"{container_name}-history",
            type="volume",
        ),
    ]

    env = dict(CONTAINER_ENV)
    claude_token = _get_claude_oauth_token()
    if claude_token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = claude_token
        logger.info(
            "Claude Code OAuth token will be injected into container %s",
            container_name,
        )

    labels = {
        CONTAINER_LABEL: "true",
        f"{CONTAINER_LABEL}.image": image_name,
        f"{CONTAINER_LABEL}.repo": repo_url or "",
        f"{CONTAINER_LABEL}.created": datetime.now(timezone.utc).isoformat(),
        f"{CONTAINER_LABEL}.workspace": workspace_dir,
    }

    try:
        container = _get_client().containers.create(
            image=tag,
            name=container_name,
            command="sleep infinity",
            user="node",
            working_dir="/workspaces",
            environment=env,
            mounts=mounts,
            labels=labels,
            detach=True,
        )
    except docker.errors.APIError as e:
        if e.status_code == 409:
            raise ValueError(
                f"A container named '{container_name}' already exists."
                " Delete it first or use a different name."
            ) from e
        raise

    container.start()

    # Inject host gh token for git and gh CLI authentication
    gh_token = _get_gh_token()
    if gh_token:
        safe_token = shlex.quote(gh_token)
        cred_exit, cred_out = container.exec_run(
            [
                "bash",
                "-c",
                f"echo https://x-access-token:{safe_token}@github.com > /home/node/.git-credentials"
                " && git config --global credential.helper 'store'"
                " && mkdir -p /home/node/.config/gh"
                f" && printf 'github.com:\\n  oauth_token: %s\\n  user: \\n  git_protocol: https\\n' {safe_token}"
                " > /home/node/.config/gh/hosts.yml",
            ],
            user="node",
        )
        if cred_exit != 0:
            logger.warning(
                "Credential setup failed (exit %d): %s",
                cred_exit,
                cred_out.decode("utf-8", errors="replace") if cred_out else "",
            )

    # Inject git identity
    git_name, git_email = git_identity
    safe_git_name = shlex.quote(git_name)
    safe_git_email = shlex.quote(git_email)
    container.exec_run(
        [
            "bash",
            "-c",
            f"git config --global user.name {safe_git_name}"
            f" && git config --global user.email {safe_git_email}",
        ],
        user="node",
    )

    warnings: list[str] = []

    if not claude_token:
        warnings.append(
            "No Claude Code OAuth token available — interactive login will be required."
        )

    # Clone repo
    clone_succeeded = False
    exit_code, output = container.exec_run(
        ["git", "clone", repo_url, workspace_dir],
        user="node",
    )
    if exit_code != 0:
        msg = output.decode("utf-8", errors="replace") if output else "unknown error"
        logger.error("git clone failed (exit %d): %s", exit_code, msg)
        warnings.append(f"Git clone failed: {msg.strip()}")
    else:
        clone_succeeded = True

    # Seed project templates into workspace (skills, CLAUDE.md, pyproject.toml)
    if clone_succeeded:
        safe_dir = shlex.quote(workspace_dir)
        seed_exit, seed_out = container.exec_run(
            [
                "bash",
                "-c",
                f"cp -rn /opt/templates/. {safe_dir}/ 2>&1",
            ],
            user="node",
        )
        if seed_exit != 0:
            msg = (
                seed_out.decode("utf-8", errors="replace")
                if seed_out
                else "unknown error"
            )
            logger.warning("Template seeding failed (exit %d): %s", seed_exit, msg)
            warnings.append(f"Template seeding failed: {msg.strip()}")

        # Install Python dependencies with uv
        uv_exit, uv_out = container.exec_run(
            ["bash", "-c", f"cd {safe_dir} && uv sync 2>&1"],
            user="node",
        )
        if uv_exit != 0:
            msg = (
                uv_out.decode("utf-8", errors="replace") if uv_out else "unknown error"
            )
            logger.warning("uv sync failed (exit %d): %s", uv_exit, msg)
            warnings.append(f"Python dependency install failed: {msg.strip()}")

        # For auto-created repos: commit templates and push
        if auto_created_repo:
            commit_exit, commit_out = container.exec_run(
                [
                    "bash",
                    "-c",
                    f"cd {safe_dir} && git add -A"
                    " && git commit -m 'Initial commit with project templates'"
                    " && git push 2>&1",
                ],
                user="node",
            )
            if commit_exit != 0:
                msg = (
                    commit_out.decode("utf-8", errors="replace")
                    if commit_out
                    else "unknown error"
                )
                logger.warning(
                    "Initial commit/push failed (exit %d): %s", commit_exit, msg
                )
                warnings.append(f"Initial commit/push failed: {msg.strip()}")

    container.exec_run(
        ["/usr/local/bin/devcontainer-start.sh"],
        workdir=workspace_dir,
        user="node",
        detach=True,
    )

    container.reload()
    info = _container_info(container)
    if warnings:
        info["warnings"] = warnings
    return info


def start_container(container_id: str) -> dict:
    """Start a stopped container."""
    try:
        container = _get_client().containers.get(container_id)
    except docker.errors.NotFound as e:
        raise ValueError(f"Container '{container_id}' not found") from e
    try:
        container.start()
    except docker.errors.APIError as e:
        raise ValueError(f"Failed to start container: {e.explanation or e}") from e
    container.reload()
    return _container_info(container)


def stop_container(container_id: str) -> dict:
    """Stop a running container."""
    try:
        container = _get_client().containers.get(container_id)
    except docker.errors.NotFound as e:
        raise ValueError(f"Container '{container_id}' not found") from e
    try:
        container.stop()
    except docker.errors.APIError as e:
        raise ValueError(f"Failed to stop container: {e.explanation or e}") from e
    container.reload()
    return _container_info(container)


def delete_container(container_id: str) -> dict:
    """Delete a container and its associated volumes."""
    try:
        container = _get_client().containers.get(container_id)
    except docker.errors.NotFound as e:
        raise ValueError(f"Container '{container_id}' not found") from e

    info = _container_info(container)
    container_name = container.name

    try:
        container.remove(force=True)
    except docker.errors.APIError as e:
        raise ValueError(f"Failed to delete container: {e.explanation or e}") from e
    delete_metadata(info["full_id"])

    # Clean up named volumes
    for suffix in ("claude-config", "history"):
        vol_name = f"{container_name}-{suffix}"
        try:
            vol = _get_client().volumes.get(vol_name)
            vol.remove()
        except docker.errors.NotFound:
            pass

    return info


def open_in_vscode(container_id: str) -> dict:
    """Open VS Code in a new window attached to a container."""
    try:
        container = _get_client().containers.get(container_id)
    except docker.errors.NotFound as e:
        raise ValueError(f"Container '{container_id}' not found") from e

    cid = container.id or ""
    hex_id = cid.encode().hex()
    workspace = (container.labels or {}).get(
        f"{CONTAINER_LABEL}.workspace", "/workspaces"
    )
    uri = f"vscode-remote://attached-container+{hex_id}{workspace}"

    if not shutil.which("code"):
        raise ValueError("VS Code ('code') not found on PATH")

    update_last_opened(cid)

    # Windows requires shell=True for code.cmd; URI is safe
    # (hex-encoded container ID + sanitised repo name).
    if sys.platform == "win32":
        subprocess.Popen(f'code --new-window --folder-uri "{uri}"', shell=True)
    else:
        subprocess.Popen(["code", "--new-window", "--folder-uri", uri])

    return {"status": "opened"}
