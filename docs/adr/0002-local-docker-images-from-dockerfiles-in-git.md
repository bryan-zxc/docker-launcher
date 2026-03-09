# ADR-0002: Local Docker images from Dockerfiles in git

## Context

The app needs to provide pre-configured Docker dev environments. Images need to be versioned, inspectable, and buildable without access to a container registry.

## Alternatives Considered

- **Container registry (ACR, ghcr.io)** — pre-built images are faster to pull, but require registry infrastructure, push permissions, and CI pipelines to build and publish. Adds operational complexity for a local tool.
- **Docker Hub public images** — not appropriate for tooling with proxy workarounds baked in.

## Decision

Store image definitions as **Dockerfiles in the git repo** under `images/<name>/`. Each subfolder contains a Dockerfile, a `metadata.json` describing the image, and an `assets/` directory with supporting scripts. The app builds images locally on demand using the Docker SDK.

Images are tagged as `docker-launcher/<name>:latest`. The app checks whether the tag exists before building and skips if cached (unless force-rebuild is requested).

## Consequences

- First build is slow (several minutes for the base image with Playwright + Claude Code). Subsequent builds use Docker layer caching.
- No registry infrastructure to manage. Anyone can build from source.
- Image definitions are version-controlled and reviewable in PRs.
- Adding new image variants (data-eng, web-dev) is just adding a new subfolder.
