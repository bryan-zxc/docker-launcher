# Docker Launcher

A local dashboard for spinning up Docker-based dev environments with pre-configured tooling and one-click VS Code attach.

## Prerequisites

- **Docker Desktop** — must be running (WSL 2 backend on Windows)
- **VS Code** — with Claude Code extension and container settings (see [VS Code setup](#vs-code-setup))
- **Python 3.13+** and **uv** — for running from source (not needed for `.exe` users)

## Quick start

### From source

```bash
git clone https://github.com/user/docker-launcher.git
cd docker-launcher
uv run docker-launcher
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### From `.exe`

1. Download `docker-launcher.zip` from the latest [GitHub Release](https://github.com/user/docker-launcher/releases)
2. Extract the zip
3. Run `docker-launcher.exe`
4. The browser opens automatically to [http://localhost:3000](http://localhost:3000)

## VS Code setup

Before using containers, configure VS Code so that Claude Code works inside them.

### 1. Install the Claude Code extension

1. Open VS Code
2. Click the **Extensions** icon in the sidebar (or press `Ctrl+Shift+X`)
3. Search for **Claude Code**
4. Click **Install**

### 2. Auto-install Claude Code in containers

By default, VS Code extensions only run on your local machine. To make Claude Code install automatically in every container you attach to:

1. Open VS Code Settings (`Ctrl+,`)
2. Search for **remote.containers.defaultExtensions**
3. Click **Add Item**
4. Enter `anthropic.claude-code`
5. Press **OK**

This ensures the extension is available inside containers without manually installing each time.

### 3. First-time Claude Code setup

When Claude Code starts for the first time, it opens with a **GUI experience**. At the bottom of the panel there is an option to switch to the **terminal experience** — we recommend selecting this as it works better.

## What you can do

- **Create containers** from pre-built image templates
- **Start, stop, and delete** containers from the dashboard
- **Open in VS Code** with one click (attaches to the running container)
- **Build images** with streaming build logs
- **Check prerequisites** — gh CLI install and GitHub auth status
