---
name: lint-test
description: Run the project's linting and type-checking suite. Use when the user says "/lint-test", "run linting", "check code quality", "run ruff", "run pyright", "run vulture", or before creating a PR. Also use proactively when you've made significant code changes and want to verify quality before committing.
---

# Lint Test

Run the full linting and type-checking suite for the docker-launcher project. Fix any issues found before reporting results.

## 1. Ruff — linting and formatting

Ruff handles both style linting (unused imports, common bugs, naming) and code formatting in one pass.

```bash
uv run ruff check .
uv run ruff format --check .
```

If there are errors:
1. Auto-fix: `uv run ruff check . --fix && uv run ruff format .`
2. Re-run both check commands
3. If issues remain that can't be auto-fixed, present each one to the user and work through them together before proceeding to the next tool

## 2. Pyright — static type checking

Pyright catches type errors, nullable access, unbound variables, and incorrect function signatures.

```bash
uv run pyright src/
```

Common fix patterns:
- **`docker.errors`/`docker.types` not recognized**: Ensure `import docker.errors` and `import docker.types` are explicit at the top of the file (the type stubs don't re-export submodules)
- **Possibly unbound variable**: Initialize the variable before the `try` block (e.g. `page = None`)
- **Optional member access**: Guard with `if x is not None` or use `x or default`
- **Argument type mismatch**: Narrow the type before passing (e.g. `cid = container.id or ""`)

If there are errors, fix each one. If a fix is unclear, present it to the user. All errors must be resolved before proceeding to the next tool.

## 3. Vulture — dead code detection

Vulture finds unused functions, variables, and unreachable code. A whitelist file excludes framework-invoked code (FastAPI endpoints, HTTP handler methods) that appears unused but is called by the framework.

```bash
uv run vulture src/ vulture_whitelist.py
```

If there are findings:
1. Determine whether each one is genuinely dead code or a false positive (framework-invoked, dynamically called, etc.)
2. **Dead code**: delete it, then re-run Ruff and Pyright to ensure nothing breaks
3. **False positive**: add it to `vulture_whitelist.py` with a comment explaining why it's needed
4. Present any ambiguous cases to the user before deciding

## Reporting

After all three tools pass, report a summary with two sections:

**Auto-fixed**: just state the total count (e.g. "12 issues auto-fixed by Ruff"). No need to list them individually.

**Manual fixes**: list each one in a markdown table:

| File | Issue | Fix |
|------|-------|-----|
| `docker_service.py:201` | `get_container` unused | Deleted function |

If there were no manual fixes needed, just say "No manual fixes needed".
