# PR Review Result — v0.2.0

**PR**: #7 Release v0.2.0
**Branch**: develop -> main
**Date**: 2026-03-16
**Commits**: 5

## 1. Lint Suite

**Auto-fixed**: 1 issue (ruff f-string) + 42 files reformatted

**Manual fixes**: No manual fixes needed

## 2. Tests

| Suite | Result | Details |
|-------|--------|---------|
| pytest | pass | 53/53 passed, 0 skipped |

## 3. ADR Compliance

| ADR | Relevant? | Status | Findings |
|-----|-----------|--------|----------|
| 0001 — FastAPI + single HTML frontend | Yes | Pass | All new endpoints follow SSE streaming pattern. Frontend remains single HTML file with vanilla JS. |
| 0002 — Local Docker images from Dockerfiles | Yes | Pass | Dockerfile in `images/base/`, tagged `docker-launcher/<name>:latest`, cache-skip logic intact. |
| 0003 — LLM Gateway proxy (Superseded) | Yes | Pass | Proxy correctly absent. Direct OAuth token injection used. |
| 0004 — JSON file for container metadata | Yes | Pass | New `update.json` follows same atomic-write pattern in `~/.docker-launcher/`. |

## 4. Bug Detection

| File | Issue | Severity | Confidence | Source |
|------|-------|----------|------------|--------|
| `docker_service.py:586` | Host-side command injection via `repo_url` in `open_in_vscode` — `shell=True` with unsanitised input, exploitable via CORS `allow_origins=["*"]` | Critical | 95 | diff |
| `docker_service.py:472` | Container-side command injection via `repo_url` in template seeding `bash -c` strings | High | 90 | diff |
| `docker_service.py:216` | Path traversal in `get_image`/`build_image` via `name` parameter (`..` not validated) | Medium | 80 | diff |

## 5. Git History Context

No historical concerns

## 6. Error Handling

| File | Issue | Severity | Confidence |
|------|-------|----------|------------|
| `docker_service.py:472` | `; true` makes template seeding exit code always 0 — error handling on lines 476-483 is dead code | High | 91 |
| `main.py:218-229` | `api_shutdown` has no error handling around `os.kill`; silent thread failure | Medium | 95 |
| `main.py:201-203` | `api_update_check` has no try/except — inconsistent with all other endpoints | Medium | 92 |
| `docker_service.py:497-502` | `devcontainer-start.sh` exec_run is fire-and-forget with no error handling | Medium | 90 |
| `update_service.py:103` | Direct key access `asset["browser_download_url"]` vs `.get()` used elsewhere | Low | 88 |
| `update_service.py:42-47` | `_current_version` silently returns "dev", disabling update checks with no log | Medium | 87 |

## 7. Code Simplification

No suggestions

## Summary

- **Critical**: 1
- **High**: 2
- **Medium**: 5
- **Historical concerns**: 0
- **Suggestions**: 0
- **Status**: Needs fixes
