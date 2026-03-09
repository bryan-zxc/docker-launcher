# PR Review Response — v0.1.0

## Fixes Applied

| # | Original Issue | Resolution |
|---|---------------|------------|
| 1 | [Critical] Frontend sends `img.name` instead of `img.id` to backend — builds/creates fail | Changed `img.name` to `img.id` in build button, select option value, and image lookup |
| 2 | [Critical] SSE streaming endpoints have no error handling — broken stream on error | Added try/except around all 3 SSE generators; yield `ERROR:` events; pre-flight image validation for build |
| 3 | [High] `except Exception` leaks Docker internals via `str(e)` | Generic `"Container creation failed"` message; detailed error in log only |
| 4 | [High] Git clone failure silently swallowed — API returns 200 with empty workspace | Added `warnings` field to response when clone fails |
| 5 | [High] Non-atomic JSON writes + corrupt JSON silently returns empty | Atomic writes via temp file + `os.replace()`; `_load()` logs warnings on corrupt JSON |
| 6 | [High] Dockerfile SNIPPET for bash history never appended to .bashrc | Append SNIPPET to `/home/$USERNAME/.bashrc` |
| 7 | [High] `subprocess.Popen` with `shell=True` and list argument for VS Code launch | Removed `shell=True` |
| 8 | [Medium] `raise ValueError(...)` missing `from e` in 4 except blocks | Added `from e` to all `raise ValueError` in start/stop/delete/vscode |
| 9 | [Medium] `_read_metadata` silently returns `None` on corrupt metadata.json | Added `logger.warning()` with exc_info |
| 10 | [Medium] Git credentials `exec_run` exit code discarded | Check exit code and log warning on failure |
| 11 | [Medium] `PackageNotFoundError` unhandled in version endpoint | try/except with `"dev"` fallback |

## Written Off

| # | Original Issue | Reason |
|---|---------------|--------|
| 12 | [Medium] `devcontainer-start.sh` exec_run result discarded | Runs with `detach=True` — no exit code available by design |
| 13 | [Medium] VS Code `Popen` result never checked | Fire-and-forget by design; `shutil.which` already guards |
| 14 | [Medium] Race condition on global `_client` | Worst case is redundant client creation; no data corruption risk |

## Re-run Results

- Ruff: pass
- Pyright: 0 errors, 0 warnings
- Vulture: clean
- Pytest: 37/37 pass

## Status: Ready for review
