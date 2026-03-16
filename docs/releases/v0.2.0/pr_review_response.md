# PR Review Response — v0.2.0

## Fixes Applied

| # | Original Issue | Resolution | Commit |
|---|---------------|------------|--------|
| 1 | Critical: Host-side command injection via `repo_url` in `open_in_vscode` (shell=True) | Replaced `shell=True` with list-form `Popen`; sanitised `repo_name` to alphanumeric/hyphen/underscore/dot only | f967abc |
| 2 | High: Container-side command injection via `repo_url` in template seeding bash -c | Used `shlex.quote()` for `workspace_dir` in all bash -c strings; repo_name sanitisation also prevents injection | f967abc |
| 3 | High: `; true` makes template seeding error handling dead code | Removed `; true`, changed `2>/dev/null` to `2>&1` so errors are captured and reported | f967abc |
| 4 | Medium: `_current_version` silently returns "dev" | Added `logger.warning()` when version lookup fails | f967abc |
| 5 | Low: Direct key access `asset["browser_download_url"]` | Changed to `.get()` for consistency | f967abc |

## Re-run Results

- Ruff: pass
- Pyright: pass (0 errors)
- Vulture: pass
- Pytest: 53/53 pass
- ADR compliance: all pass

## Status: Ready for review
