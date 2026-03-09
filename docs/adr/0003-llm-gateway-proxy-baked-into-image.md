# ADR-0003: LLM Gateway proxy baked into container image

**Status: Superseded**

> **Note:** This ADR is superseded. In the personal/open-source version (Docker Launcher), the LLM Gateway proxy has been removed entirely. Direct Claude Code authentication (API key or OAuth) is used instead, so there is no need for a proxy to be baked into the container image. This ADR is retained for historical context only.

## Context

The LLM Gateway proxy (`proxy.py`) forwarded Claude Code requests to a corporate LLM Gateway, injecting an SSO token from a bind-mounted cache file. In the original devcontainer setup, `proxy.py` lived in the workspace repo at `/workspace/claude-code/proxy.py` and was only available when using that specific repo.

## Decision

COPY `proxy.py` into the Docker image at `/usr/local/bin/proxy.py` during build. The container startup script (`start.sh`) references this fixed path instead of a workspace-relative path.

This meant containers worked with **any cloned repo**, not just the original devcontainer repo. The proxy was part of the environment, not the project.

## Consequences

- Updating `proxy.py` required rebuilding the image. This was acceptable since proxy changes were rare and the app supports force-rebuild.
- The token cache was bind-mounted from the host (`~/.docker-launcher`), so token refresh worked without rebuilding.
- Containers were self-contained — clone any repo and Claude Code worked immediately.
