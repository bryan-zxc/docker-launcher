# Project Conventions

## Dependencies
- Always use `uv add <package>` to add dependencies — never edit `pyproject.toml` directly.

## Project Structure
```
src/docker_launcher/       Python package (FastAPI backend)
  main.py                  FastAPI app, all API routes, uvicorn entry
  docker_service.py        Docker SDK wrapper — images, containers, builds
  database.py              JSON file store for container metadata
  prerequisites.py         gh CLI detection and install helpers
  static/index.html        Single-page frontend (Option A Midnight theme)
images/base/               Docker image definition (Dockerfile + assets)
tests/                     pytest test suite
docs/adr/                  Architecture Decision Records
```

## Data Directory
All persistent data lives in `~/.docker-launcher/`:
- `containers.json` — container metadata store
- `launcher.log` — application log (rotated, 5 MB)

## Running
```bash
uv run docker-launcher      # starts on http://localhost:3000
uv run pytest                # run tests
uv run ruff check .          # lint
uv run pyright src/          # type check
```

## Docker Naming
- Image prefix: `docker-launcher-`
- Container label namespace: `docker-launcher`
- Container name format: `docker-launcher-{uuid}`

## Frontend
- Single HTML file: `src/docker_launcher/static/index.html`
- Design: Option A Midnight — Outfit font (300-800), glass-morphism, dark/light themes
- Monospace only for: log output, container IDs, image tags, code snippets
- API calls go to `/api/*` endpoints on same origin
- SSE streaming for build logs and prerequisite install actions

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/version | App version |
| GET | /api/images | List image templates |
| GET | /api/images/{name} | Get single image |
| POST | /api/images/{name}/build | Build image (SSE stream) |
| GET | /api/containers | List containers |
| POST | /api/containers | Create container |
| POST | /api/containers/{id}/start | Start container |
| POST | /api/containers/{id}/stop | Stop container |
| POST | /api/containers/{id}/vscode | Open in VS Code |
| DELETE | /api/containers/{id} | Delete container |
| GET | /api/prerequisites | Check prerequisites |
| POST | /api/prerequisites/install-gh | Install gh CLI (SSE) |
| POST | /api/prerequisites/gh-login | GitHub login (SSE) |
