# Reviewer Notes — v0.2.0

## Review Walkthrough

### Category 1: Auto-update system
Reviewed `update_service.py` (background checker, version comparison, download, state persistence) and 3 new endpoints in `main.py` (`/api/update-check`, `/api/update-download`, `/api/shutdown`).

Reviewer asked about **double-click on the download button** — whether `streamSSE` guards against concurrent downloads. Analysis showed the download banner hides the button visually, and atomic `os.replace` prevents file corruption, but there was no formal guard. Added `if (state.activeSSE) return;` at the top of the click handler.

### Category 2: Container template seeding
Reviewed template folder structure (6 skills, CLAUDE.md, pyproject.toml), Dockerfile additions (uv, npm packages, COPY templates), and `create_container()` seeding logic (`cp -rn` + `uv sync`). Reviewer accepted without questions.

### Category 3: OAuth token injection
Reviewed `_auth_defaults.py`, token injection into container environment, and CI workflow changes. Reviewer accepted without questions.

### Category 4: Frontend update UI + release skill + packaging
Reviewed ~400 lines of frontend additions (banner, progress bar, blocking overlay, dismiss confirm), release skill renumbering, PyInstaller spec, and vulture whitelist.

Reviewer asked about **z-index stacking** between the update overlay (400) and delete confirmation (300). Confirmed no conflict is possible — the update overlay blocks interaction with the container list, and `fetchUpdateCheck()` is never called during polling, so the overlay can't appear while a delete confirmation is open.

### Automated review outcomes
Reviewer reviewed both `pr_review_result.md` (1 Critical, 2 High, 5 Medium findings) and `pr_review_response.md` (5 fixes applied). Accepted the deferred Medium items (shutdown error handling, update-check try/except, start.sh fire-and-forget, path traversal) as low-risk for this release.

## Changes Made During Review

| File | Change |
|------|--------|
| `src/docker_launcher/static/index.html` | Added `if (state.activeSSE) return;` guard to download button click handler |

## Deferred

- `api_shutdown` error handling around `os.kill` — benign in a terminating process
- `api_update_check` missing try/except — safe function, frontend catches 500
- `devcontainer-start.sh` fire-and-forget exec_run — pre-existing intentional pattern
- Path traversal in `get_image` — FastAPI params can't contain `/`, `..` fails safely
