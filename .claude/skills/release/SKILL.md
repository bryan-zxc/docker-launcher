---
name: release
description: Prepare and ship a release. Use when the user says "/release", "create a release", "prepare release", "bump version", "ship it", or wants to cut a new version. Handles PR creation, lint checks, ADR compliance, bug detection, and produces review artifacts for the release reviewer.
---

# Release

Prepare a release from `develop` to `main`. Creates the PR first, runs all quality checks, produces review artifacts, and hands off to the reviewer.

## Workflow

### 1. Create PR

Create the PR immediately — it's the anchor for everything that follows.

```bash
gh pr create --base main --head develop \
  --title "Release v<TBD>" \
  --body "Release PR — version and summary to be updated after review."
```

### 2. Inspect the PR diff

Show the user what's in this release:

```bash
gh pr diff <pr-number> --name-only
gh pr diff <pr-number>
git log main..develop --oneline
```

Present a summary of the changes and recommend a version bump with rationale:
- **patch** (0.1.0 -> 0.1.1) — bug fixes only
- **minor** (0.1.0 -> 0.2.0) — new features, backwards compatible
- **major** (0.1.0 -> 1.0.0) — breaking changes

Wait for user confirmation.

### 3. Download latest Claude Code installer

Download the latest installer so it gets committed and bundled into the `.exe`:

```bash
powershell.exe -ExecutionPolicy Bypass -File images/base/assets/fetch-claude-installer.ps1
```

This must succeed — do not proceed if the download fails.

### 4. Update version and changelog

Update the version in `pyproject.toml` -> `[project] version`.

Update `CHANGELOG.md` at the repo root (create the file if it doesn't exist). Prepend a new section following the [Keep a Changelog](https://keepachangelog.com) format:

```markdown
## [<version>] - <YYYY-MM-DD>
### Added
- <new features, grouped by ticket>
### Fixed
- <bug fixes>
### Changed
- <changes to existing functionality>
```

Omit any section (Added/Fixed/Changed) that has no entries.

Commit, push, and update the PR:

```bash
uv lock
git add pyproject.toml uv.lock CHANGELOG.md images/base/assets/claude-install.sh
git commit -m "Bump version to v<version>"
git push origin develop
```

```bash
gh pr edit <pr-number> --title "Release v<version>" --body "$(cat <<'EOF'
## Release v<version>

### Summary
<bullet points from commit log since last release>

### Pre-release checks
See `docs/releases/v<version>/pr_review_result.md`

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 5. Create release folder

```bash
mkdir -p docs/releases/v<version>
```

### 6. Run all checks

Collect results for the report as you go.

#### 5a. Lint suite (sequential — must fix before proceeding)

Run `/lint-test` (Ruff, Pyright, Vulture). Fix all issues. Track auto-fixed count and manual fixes.

#### 5b. Tests (sequential — must pass before proceeding)

```bash
uv run pytest
```

Fix any failures before proceeding.

#### 5c-5f. Analysis (parallel agents)

Once lint and tests pass, launch **all remaining checks in parallel**. Each analysis agent scores findings on a **confidence scale (0-100)** and only issues scoring **>= 80** make it into the report.

##### ADR compliance (1 agent per relevant ADR)

Read `docs/adr/adr.md` to get the ADR list. For each ADR:
1. Read the ADR file
2. Determine if it's relevant to the files changed in this PR
3. If relevant, scan changed code for compliance

Launch one agent per relevant ADR. Each returns: ADR number/title, Pass/Fail, specific findings if failed.

##### Bug detection (Agents 1-3)

**Agent 1 — Diff-based bug scan:**
Read the PR diff and scan for:
- Logic errors, off-by-one, wrong conditions
- Missing null/undefined checks
- Race conditions in threaded code
- Security issues (injection, path traversal)
- Incorrect type narrowing or unsafe casts

**Agent 2 — Git history context:**
For each file modified in the PR:
1. Run `git log --oneline -10 -- <file>` and `git blame <file>` on the modified sections
2. Check if any recent changes revert, contradict, or regress previous fixes
3. Look for patterns where the same area was fixed before — recurring bug indicators

**Agent 3 — Previous PR comments:**
Check the last 5 merged PRs that touched the same files:
```bash
gh pr list --state merged --limit 20 --json number,files,title
```
Filter to PRs that share files with this release. Read their review comments for issues that may also apply here.

**Confidence scoring rubric (give to each agent):**
- **0**: False positive — doesn't stand up to scrutiny, or is a pre-existing issue
- **25**: Might be real, but could be a false positive; unverified
- **50**: Verified real issue, but a nitpick or unlikely in practice
- **75**: Double-checked and very likely real; will impact functionality
- **100**: Confirmed real, will happen frequently; evidence directly proves it

Only report findings with confidence >= 80. For each finding, include the confidence score in the report.

##### Error handling

Perform a **systematic 5-step audit** of error handling in changed files:

**Step 1 — Identify all error handling points:**
Map every `try/except`, `catch`, error callback, and fallback path in the changed code.

**Step 2 — Scrutinize each handler:**
For each error handling point, check:
- Is the exception type specific enough? (no bare `except:`)
- Is the error logged with sufficient context (logger, not just `print`)?
- Does the user get feedback (API error response, UI message)?
- Is the original exception preserved (not swallowed)?

**Step 3 — Examine error messages:**
- Are error messages actionable? (tell the user what went wrong and what to do)
- Do they leak sensitive information? (stack traces, internal paths, credentials)

**Step 4 — Check for hidden failures:**
- Functions that return `None` or default values on error without logging
- Boolean flags that silently mask errors
- External calls (Docker SDK, filesystem, network) without any error handling
- Async operations that can fail silently

**Step 5 — Validate against project standards:**
- Check CLAUDE.md and ADRs for error handling conventions
- Verify consistency with how errors are handled elsewhere in the codebase

Apply the same confidence scoring (>= 80 to report).

##### Code simplification

Scan changed code for simplification opportunities. Preserve all existing functionality — only suggest changes that improve clarity without altering behavior.

Focus areas:
- Overly nested logic that could be flattened (early returns, guard clauses)
- Duplicated code that could be shared
- Abstractions that don't earn their complexity
- Complex conditionals that could be decomposed into named booleans
- Unnecessary intermediate variables or redundant conversions

Do NOT suggest:
- Adding docstrings, comments, or type annotations to unchanged code
- Refactoring that changes public APIs
- Stylistic preferences already handled by Ruff

### 7. Produce pr_review_result.md

This file reports **findings only** — never mention fixes here. Fixes go in `pr_review_response.md`.

Write to `docs/releases/v<version>/pr_review_result.md`:

```markdown
# PR Review Result — v<version>

**PR**: #<number> Release v<version>
**Branch**: develop -> main
**Date**: <today>
**Commits**: <count>

## 1. Lint Suite

**Auto-fixed**: <N> issues

**Manual fixes**:

| File | Issue | Fix |
|------|-------|-----|
| `file.py:line` | description | what was done |

(or "No manual fixes needed")

## 2. Tests

| Suite | Result | Details |
|-------|--------|---------|
| pytest | pass/fail | N/N passed, N skipped |

## 3. ADR Compliance

| ADR | Relevant? | Status | Findings |
|-----|-----------|--------|----------|
| 0001 — title | Yes/No | Pass/Fail | details or — |

## 4. Bug Detection

| File | Issue | Severity | Confidence | Source |
|------|-------|----------|------------|--------|
| `file.py:line` | description | Critical/High/Medium | 80-100 | diff/history/prior-PR |

(or "No bugs found")

## 5. Git History Context

| File | Finding | Source |
|------|---------|--------|
| `file.py:line` | description of regression or recurring issue | blame/log/prior-PR |

(or "No historical concerns")

## 6. Error Handling

| File | Issue | Severity | Confidence |
|------|-------|----------|------------|
| `file.py:line` | description | Critical/High/Medium | 80-100 |

(or "No issues found")

## 7. Code Simplification

| File | Suggestion |
|------|-----------|
| `file.py:line` | description |

(or "No suggestions")

## Summary

- **Critical**: N
- **High**: N
- **Medium**: N
- **Historical concerns**: N
- **Suggestions**: N
- **Status**: Ready for review / Needs fixes
```

### 8. Fix all issues

If the report found any Critical or High issues:
1. Fix each one
2. Commit and push to `develop`
3. Re-run all checks
4. Update the report

### 9. Produce pr_review_response.md

Write to `docs/releases/v<version>/pr_review_response.md`:

```markdown
# PR Review Response — v<version>

## Fixes Applied

| # | Original Issue | Resolution | Commit |
|---|---------------|------------|--------|
| 1 | description | what was done | sha |

(or "No fixes needed — all checks passed on first run")

## Re-run Results

- Ruff: pass
- Pyright: pass
- Vulture: pass
- Pytest: N/N pass
- ADR compliance: all pass

## Status: Ready for review
```

### 10. Commit review artifacts and push

```bash
git add docs/releases/v<version>/
git commit -m "Add release review artifacts for v<version>"
git push origin develop
```

### 11. Hand off to reviewer

Tell the user: "PR is ready. Run `/release-review` to review."

---

## Post-merge: Tag, release, and report

After the reviewer merges the PR, this skill continues:

### 12. Verify changelog and tag

Check out `main` and verify the changelog reflects everything in the release (including any fixes made during the review process):

```bash
git checkout main && git pull origin main
```

Review `CHANGELOG.md` — if any fixes were made after the initial changelog entry (e.g. during step 8), update it now:

```bash
git add CHANGELOG.md
git commit -m "Update changelog for v<version>"
git push origin main
```

Then tag and push to trigger the release workflow:

```bash
git tag v<version>
git push origin v<version>
```

### 13. Monitor CI/CD

Watch the GitHub Actions release workflow triggered by the tag:

```bash
gh run list --limit 1
gh run watch <run-id>
```

If the workflow fails:
1. Check the failure: `gh run view <run-id> --log-failed`
2. Fix the issue directly on `main` — do NOT go back to `develop`
3. Increment the patch version by 0.0.1 (e.g. v0.2.0 -> v0.2.1)
4. Update `pyproject.toml` with the new version
5. Commit and push to `main`:
   ```bash
   git checkout main && git pull origin main
   git add -A
   git commit -m "Hotfix v<new-version>: <brief description>"
   git push origin main
   ```
6. Tag the hotfix:
   ```bash
   git tag v<new-version>
   git push origin v<new-version>
   ```
7. Merge the fix back to `develop` so the branches stay in sync:
   ```bash
   git checkout develop && git merge main
   git push origin develop
   ```
8. Monitor the new CI run — repeat if it fails again

### 14. Update GitHub Release notes

The CI workflow creates the GitHub Release and uploads the `.exe` zip automatically on tag push. Update the release with notes from the changelog:

```bash
gh release edit v<version> --notes "$(cat <<'EOF'
<copy the CHANGELOG.md section for this version>

## Download
Download `docker-launcher.zip`, extract, and run `docker-launcher.exe`.

Requires Docker Desktop.
EOF
)"
```

### 15. Post-release report

Stay on `main`. Create an HTML slide deck saved to `docs/releases/v<version>/release-report.html`.

**Slide content:**

**Slide 1 — Release overview**
- Version, date, PR link
- One-line summary

**Slide 2 — What's new**
- Features delivered (tickets closed in this release)
- Bug fixes

**Slide 3 — Quality gate results**
- Lint/type check: pass
- Tests: N/N pass
- ADR compliance: all pass
- Issues found and resolved count

**Slide 4 — Known issues / what's next**
- Deferred items, known limitations
- Upcoming work from the backlog

**Slide 5 — How to get it**
- `.exe` users: GitHub Releases download link
- Clone users: `git pull && uv run docker-launcher`

### 15b. Update README with download link

After the release is published, update `README.md` with the download link from the GitHub Release page. Replace any existing download link or placeholder with the new one. Also update the `{{DOWNLOAD_LINK}}` placeholder in the release report HTML if present.

### 15c. Commit release report and README to main

Commit the report to `main` after the release workflow succeeds and the download link has been updated. This must be post-release because the report includes CI/CD results, the final release status, and the download link, which aren't known until the workflow completes.

```bash
git add docs/releases/v<version>/release-report.html README.md
git commit -m "chore: add release report for v<version>"
git push origin main
```

This commit is untagged so it does not trigger the release workflow.

### 16. Merge back to develop

```bash
git checkout develop && git merge main
git push origin develop
```
