# Changelog

## [0.1.1] - 2026-03-10

### Fixed

- CI release workflow now has `permissions: contents: write` so it can create GitHub Releases

## [0.1.0] - 2026-03-09

### Added

**Dashboard & UI**
- FastAPI backend with single-page HTML dashboard
- Dark/light theme toggle with localStorage persistence (Option A Midnight design)
- Docker status banner with error messaging when Docker Desktop is not running
- Streaming build log drawer with SSE progress

**Container Management**
- Create, start, stop, delete containers from the dashboard
- One-click "Open in VS Code" attached to running containers
- `/workspaces/<repo-name>` convention matching Codespaces/devcontainer standard
- Git clone with authentication using host gh credentials
- Container metadata tracking with last-opened timestamps in JSON store
- Docker image auto-rebuild when Dockerfile content changes via context hash
- Streaming Docker build logs with progress to the frontend via SSE

**Container Environment**
- Persistent command history across container restarts
- Per-container Claude Code configuration volume
- gh CLI credential injection from host
- Claude Code statusline showing model, workspace, git branch, context, and token costs
- Default editor set to `code --wait` for VS Code integration
- Git line-ending configuration for cross-platform compatibility

**Prerequisites & Onboarding**
- Prerequisites panel: gh CLI install check and auth status with install/login buttons

**Packaging & CI**
- PyInstaller packaging for standalone `.exe` distribution
- Auto-open browser on exe launch
- GitHub Actions release workflow: pytest on Linux, PyInstaller build on Windows, upload zip to GitHub Release on version tag
- Pytest test suite covering database, docker service, prerequisites, and API endpoints
