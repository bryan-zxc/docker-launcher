# ADR-0001: FastAPI backend with single HTML frontend

## Context

The app needs a web backend to wrap the Docker SDK and a frontend for users to manage containers. The frontend requirements are modest — a dashboard with container list, create form, and action buttons.

## Alternatives Considered

- **Node.js/Express + React** — familiar to some, but adds a build step, node_modules, and a separate dev server. Overkill for a local tool.
- **Django** — heavier than needed. No ORM requirements beyond SQLite, no auth framework needed.
- **Flask** — viable, but lacks native async support and built-in OpenAPI docs.

## Decision

Use **FastAPI** for the backend with a **single `index.html` file** served as a static asset. The frontend uses vanilla JS (or htmx) with inline CSS — no build step, no bundler, no node_modules.

FastAPI provides async support, automatic OpenAPI docs, SSE streaming via `StreamingResponse`, and static file serving. The single HTML file keeps deployment trivial — just `uv run python run.py`.

## Consequences

- No frontend build pipeline to maintain. The entire app is `pip install` and run.
- Frontend capabilities are limited to what vanilla JS can do — no component framework, no type checking, no hot module reload.
- Adding complex UI interactions later may require migrating to a framework, but the backend API layer remains unchanged.
