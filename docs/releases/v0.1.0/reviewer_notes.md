# Reviewer Notes — v0.1.0

**PR**: #1 Release v0.1.0
**Reviewer session date**: 2026-03-10

## Review walkthrough

### Category 1: Backend API & Services

Files: `main.py`, `docker_service.py`, `database.py`, `prerequisites.py`

Reviewed the FastAPI app structure, Docker SDK wrapper, JSON metadata store, and prerequisites module. The reviewer asked to verify whether three flagged issues had been fixed:

1. **`subprocess.Popen` with `shell=True`** — Confirmed removed. Current code at `docker_service.py:526` passes a list without `shell=True`.
2. **`importlib.metadata.version` unhandled** — Confirmed fixed. Now wrapped in try/except with `"dev"` fallback (`main.py:61-64`).
3. **`raise ValueError` missing `from e`** — Confirmed fixed. All `raise ValueError` inside `except` blocks now chain with `from e`.

The `_client` race condition (Medium) was acknowledged as acceptable for v0.1.0 given single-threaded async execution.

### Category 2: Docker Image Definition

Files: `Dockerfile`, `start.sh`, `statusline.sh`, `claude-install.sh`, `metadata.json`

Reviewed the base image (node:24), system dependencies, Claude Code installation, history persistence, startup script, and statusline. No questions raised. Suggested questions about shared bash/zsh history file and Playwright cache in `/tmp` were noted but not pursued.

### Category 3: Frontend

File: `index.html` (~1950 lines)

Reviewed the single-page app: glass-morphism design, container/image/prerequisites pages, SSE streaming, XSS protection, polling, theme toggle. The reviewer identified a cosmetic issue:

- **Duplicate image description**: `img.description` rendered twice — once as subtitle in the image card header and again as a standalone styled block. Reviewer asked to remove one; the standalone `image-description` block was removed.

### Category 4: Build, Packaging & CI

Files: `pyproject.toml`, `boot.py`, `docker-launcher.spec`, `release.yml`, `.gitattributes`

Reviewed PyInstaller config, CI pipeline (test on ubuntu, build on windows), and line-ending enforcement. No questions raised.

### Category 5: Project Configuration & Documentation

Files: `CHANGELOG.md`, `README.md`, `vulture_whitelist.py`, `docs/adr/*`, `.claude/*`, `tests/*`

Reviewed changelog, README, ADR compliance, vulture whitelist, and test coverage (37/37). No questions raised.

### Automated review outcomes

Both review artifacts (`pr_review_result.md`, `pr_review_response.md`) presented in full. All 2 Critical and 4 High issues were fixed in commit `dcfd09e`. Remaining Medium items and code simplification suggestions deferred. Re-run passed clean. No concerns raised.

## Changes made during review

| File | Change |
|------|--------|
| `src/docker_launcher/static/index.html` | Removed duplicate `image-description` block in `renderImages()` |

## Deferred

- `_client` TOCTOU race condition (Medium) — acceptable given single-threaded async
- `_read_metadata` silent failure on corrupt metadata.json (Medium)
- Unchecked `exec_run` results for git credentials and devcontainer-start (Medium)
- VS Code `Popen` result not checked (Medium)
- Code simplification suggestions (redundant Docker API calls, duplicated patterns)
- Placeholder repo URL in README.md
- No lint/type-check step in CI (enforced locally by release skill)
