# Downloads the Claude Code installer on the HOST before Docker build.
# Runs via initializeCommand — host has normal network access (no Zscaler in Docker).
#
# Strategy:
#   1. Try direct download from claude.ai
#   2. If that returns HTML, resolve the redirect and download from GCS
#   3. If GCS is blocked (ECONNREFUSED), detect system proxy and retry

$ErrorActionPreference = "Stop"
$output = "images\base\assets\claude-install.sh"
$installUrl = "https://claude.ai/install.sh"
$gcsHost = "https://storage.googleapis.com"

function Test-ValidScript($path) {
    if (-not (Test-Path $path)) { return $false }
    $first = Get-Content $path -TotalCount 1 -ErrorAction SilentlyContinue
    return ($first -match "^#!/bin/bash")
}

# --- Attempt 1: Direct download ---
Write-Host "Fetching Claude Code installer..."
try {
    curl.exe -fsSL $installUrl -o $output 2>$null
} catch {}

if (Test-ValidScript $output) {
    Write-Host "Claude Code installer downloaded successfully."
    exit 0
}

# --- Attempt 2: Resolve redirect to GCS ---
Write-Host "Direct download failed. Resolving redirect..."
$redirectUrl = ""
try {
    $redirectUrl = (curl.exe -sI -o NUL -w "%{redirect_url}" $installUrl 2>$null).Trim()
} catch {}

if ($redirectUrl -match "^$([regex]::Escape($gcsHost))") {
    Write-Host "Resolved to GCS: $redirectUrl"
    try {
        curl.exe -fsSL $redirectUrl -o $output 2>$null
    } catch {}

    if (Test-ValidScript $output) {
        Write-Host "Claude Code installer downloaded successfully (via GCS)."
        exit 0
    }
}

# --- Attempt 3: Retry via system proxy ---
Write-Host "GCS download failed. Detecting system proxy..."
$proxyUrl = ""
try {
    $proxyUrl = [System.Net.WebRequest]::DefaultWebProxy.GetProxy($gcsHost).AbsoluteUri
    if ($proxyUrl -eq "$gcsHost/") { $proxyUrl = "" }
} catch {}

if ($proxyUrl) {
    Write-Host "Using proxy: $proxyUrl"
    $env:HTTPS_PROXY = $proxyUrl
    $env:HTTP_PROXY = $proxyUrl

    # Retry direct URL with proxy
    try {
        curl.exe -fsSL $installUrl -o $output 2>$null
    } catch {}

    if (Test-ValidScript $output) {
        Write-Host "Claude Code installer downloaded successfully (via proxy)."
        exit 0
    }

    # Retry GCS URL with proxy
    if ($redirectUrl) {
        try {
            curl.exe -fsSL $redirectUrl -o $output 2>$null
        } catch {}

        if (Test-ValidScript $output) {
            Write-Host "Claude Code installer downloaded successfully (via proxy + GCS)."
            exit 0
        }
    }
}

Write-Host ""
Write-Host "ERROR: Could not download Claude Code installer."
Write-Host ""
Write-Host "Manual fix: download the installer on a non-proxied network and save it to:"
Write-Host "  $output"
Write-Host ""
exit 1
