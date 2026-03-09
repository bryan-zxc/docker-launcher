# PR Review Response — v0.1.0

## Fixes Applied

| # | Original Issue | Resolution | Commit |
|---|---------------|------------|--------|
| 1 | [Critical] Frontend sends `img.name` instead of `img.id` to backend — builds/creates fail | Changed `img.name` to `img.id` in build button `data-build-image`, select `<option value>`, and image lookup comparison | dcfd09e |
| 2 | [Critical] SSE streaming endpoints have no error handling — broken stream on error | Added try/except around all 3 SSE generators (build, install-gh, gh-login) that yield `ERROR:` events; added pre-flight image validation for build endpoint | dcfd09e |
| 3 | [High] `except Exception` leaks Docker internals via `str(e)` | Replaced `str(e)` with generic `"Container creation failed"` message; detailed error remains in log | dcfd09e |
| 4 | [High] Git clone failure silently swallowed — API returns 200 with empty workspace | Added `warnings` field to response when clone fails so frontend can display it | dcfd09e |
| 5 | [High] Non-atomic JSON writes + corrupt JSON silently returns empty | `_save()` now writes to temp file then `os.replace()` atomically; `_load()` logs warnings on corrupt/unreadable JSON | dcfd09e |
| 6 | [High] Dockerfile SNIPPET for bash history defined but never appended to .bashrc | Added `echo "$SNIPPET" >> /home/$USERNAME/.bashrc` to the RUN instruction | dcfd09e |

## Re-run Results

- Ruff: pass
- Pyright: 0 errors, 0 warnings
- Vulture: clean
- Pytest: 37/37 pass

## Status: Ready for review
