# Architecture Decision Records

Active design decisions for the docker-launcher project. Newest first. When a decision is superseded, its entry and file are both deleted — the replacement ADR captures historical context.

| # | Date | Title | Status | Description | Link |
|---|------|-------|--------|-------------|------|
| 0004 | 2026-03-05 | JSON file for container metadata | Active | Single JSON file stores app-side container metadata like last_opened_at, cleaned up on list | [ADR-0004](0004-json-file-for-container-metadata.md) |
| 0003 | 2026-03-05 | LLM Gateway proxy baked into container image | Superseded | proxy.py COPY'd into the Docker image at build time — no longer applies, direct authentication is used instead | [ADR-0003](0003-llm-gateway-proxy-baked-into-image.md) |
| 0002 | 2026-03-05 | Local Docker images from Dockerfiles in git | Active | No container registry — images defined as Dockerfiles in the repo and built locally on demand | [ADR-0002](0002-local-docker-images-from-dockerfiles-in-git.md) |
| 0001 | 2026-03-05 | FastAPI backend with single HTML frontend | Active | Python FastAPI backend serving a single HTML file with no build step, no node_modules | [ADR-0001](0001-fastapi-backend-with-single-html-frontend.md) |
