"""Prerequisite checks for container creation: gh CLI and auth."""

import logging
import re
import subprocess
import sys
from typing import Generator

logger = logging.getLogger(__name__)


def gh_installed() -> bool:
    """Check if the gh CLI is available on PATH."""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def gh_authenticated() -> bool:
    """Check if gh is authenticated to github.com."""
    if not gh_installed():
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_prerequisites() -> dict:
    """Return current prerequisite status."""
    installed = gh_installed()
    return {
        "gh_installed": installed,
        "gh_authenticated": gh_authenticated() if installed else False,
    }


def install_gh() -> Generator[str, None, None]:
    """Install GitHub CLI via winget, yielding progress lines."""
    if sys.platform != "win32":  # type: ignore[unreachable]
        yield "ERROR: Automatic install only supported on Windows"
        return

    yield "Installing GitHub CLI via winget..."
    try:
        proc = subprocess.Popen(
            [
                "winget",
                "install",
                "--id",
                "GitHub.cli",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError:
        yield "ERROR: winget not found. Please install GitHub CLI manually from https://cli.github.com"
        return

    assert proc.stdout is not None
    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    for raw_line in proc.stdout:
        line = raw_line.decode("utf-8", errors="replace").rstrip()
        line = ansi_re.sub("", line)
        if not line:
            continue
        # Filter progress spinner characters
        line = line.replace("\u2588", "-").replace("\u2591", " ")
        yield line

    rc = proc.wait()
    if rc != 0:
        yield f"ERROR: Installation failed with exit code {rc}"
    else:
        yield "GitHub CLI installed successfully"


def gh_login() -> Generator[str, None, None]:
    """Run gh auth login with device code flow, yielding progress lines."""
    if not gh_installed():
        yield "ERROR: GitHub CLI is not installed"
        return

    yield "Starting GitHub authentication..."
    try:
        proc = subprocess.Popen(
            [
                "gh",
                "auth",
                "login",
                "--hostname",
                "github.com",
                "--git-protocol",
                "https",
                "--web",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
        )
    except FileNotFoundError:
        yield "ERROR: gh command not found"
        return

    assert proc.stdout is not None
    assert proc.stdin is not None

    # Send Enter to skip the "Press Enter to open" prompt
    try:
        proc.stdin.write(b"\n")
        proc.stdin.flush()
    except OSError:
        pass

    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    for raw_line in proc.stdout:
        line = raw_line.decode("utf-8", errors="replace").rstrip()
        line = ansi_re.sub("", line)
        if not line:
            continue
        yield line

    rc = proc.wait()
    if rc != 0:
        yield "ERROR: Authentication failed"
    else:
        yield "GitHub authentication successful"
