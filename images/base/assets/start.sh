#!/bin/bash
set -euo pipefail

# =============================================================================
# Dev Container Startup Script
# Seeds Claude Code config and verifies tooling.
# =============================================================================

CLAUDE_CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CLAUDE_JSON="$CLAUDE_CONFIG/.claude.json"

echo "============================================"
echo "  Dev Container Setup"
echo "============================================"
echo ""

# --- 1. Seed claude config (skip onboarding) ---
mkdir -p "$CLAUDE_CONFIG"
if [ ! -f "$CLAUDE_JSON" ]; then
    echo "Seeding $CLAUDE_JSON (skip onboarding)..."
    cat > "$CLAUDE_JSON" << 'SEED'
{
  "hasCompletedOnboarding": true,
  "theme": "dark"
}
SEED
else
    # Ensure onboarding is marked complete
    if command -v jq &>/dev/null; then
        tmp=$(jq '.hasCompletedOnboarding = true' "$CLAUDE_JSON" 2>/dev/null) && \
            echo "$tmp" > "$CLAUDE_JSON"
    fi
fi

# --- 2. Seed settings.json (statusline) ---
SETTINGS_JSON="$CLAUDE_CONFIG/settings.json"
if [ ! -f "$SETTINGS_JSON" ]; then
    echo "Seeding statusline config..."
    cat > "$SETTINGS_JSON" << 'SETTINGS'
{
  "statusLine": {
    "type": "command",
    "command": "/usr/local/bin/claude-statusline.sh"
  }
}
SETTINGS
else
    # Ensure statusline is set even if settings file already exists
    if command -v jq &>/dev/null && ! jq -e '.statusLine' "$SETTINGS_JSON" &>/dev/null; then
        tmp=$(jq '. + {"statusLine": {"type": "command", "command": "/usr/local/bin/claude-statusline.sh"}}' "$SETTINGS_JSON" 2>/dev/null) && \
            echo "$tmp" > "$SETTINGS_JSON"
    fi
fi

# --- 3. Verify claude binary is available ---
if command -v claude &>/dev/null; then
    echo "Claude: $(claude --version 2>/dev/null || echo 'found')"
else
    echo "WARNING: claude binary not found."
    echo "  Try rebuilding the container image."
fi

# --- 4. GitHub CLI authentication ---
if command -v gh &>/dev/null; then
    if gh auth status &>/dev/null; then
        echo "GitHub: $(gh auth status 2>&1 | grep 'Logged in' | head -1 | sed 's/^[[:space:]]*//')"
    else
        echo ""
        echo "============================================"
        echo "  GitHub Authentication Required"
        echo "============================================"
        echo ""
        gh auth login -h github.com -p https -w
    fi
fi

echo ""
echo "Ready."
