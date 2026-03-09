---
name: release-review
description: Review a release PR as the designated reviewer. Use when the user says "/release-review", "review the release", "review the PR", or wants to walk through a release before merging. Guides the reviewer through the changes, suggests probing questions, and merges when satisfied.
---

# Release Review

Walk the reviewer through a release PR interactively, one content category at a time. The goal is to help the reviewer build confidence in the release.

## Setup

Find the open release PR targeting `main`:

```bash
gh pr list --base main --state open --json number,title,url
```

If multiple PRs exist, ask the reviewer which one. Then load the context:

```bash
gh pr diff <pr-number>
git log main..develop --oneline
```

Read the review artifacts from `docs/releases/v<version>/`:
- `pr_review_result.md`
- `pr_review_response.md`

## Part 1: Interactive code walkthrough

Analyse the PR diff and group the changes into content categories based on what was actually changed (e.g. "Auth service changes", "Docker service changes", "Frontend updates", "New configuration files", "Build/packaging changes"). The categories should reflect the actual content, not a fixed template.

Go through **one category at a time**. For each:

1. Summarise what changed in this category — the key files, the intent, the approach
2. Suggest 2-3 probing questions the reviewer might want to ask. These should be specific to the changes, not generic. Think about:
   - Edge cases that could break
   - Backwards compatibility
   - User-facing impact
   - Error paths
   - Interactions with other parts of the system
3. **Wait** — let the reviewer ask their own questions, pick from the suggestions, or say they're happy with this category
4. Answer any questions by reading code, checking the diff, or reasoning through the logic
5. Only move to the next category when the reviewer says so

## Part 2: Automated review outcomes

After all code categories are covered, present the full contents of both review artifacts from `docs/releases/v<version>/`:

1. Show `pr_review_result.md` — the initial automated findings
2. Show `pr_review_response.md` — what was fixed and the re-run results

Present them in full, not summarised. Then ask: "Any questions or concerns about the automated review outcomes?"

Wait for the reviewer to ask questions or confirm they're satisfied.

## Part 3: Reviewer notes

Write `docs/releases/v<version>/reviewer_notes.md` summarising the review session. This is a record of the reviewer's work — what they examined, what they questioned, what they understood and accepted, and what they changed. Structure:

- **Review walkthrough**: One entry per content category. For each, note what was reviewed and what questions the reviewer asked. Capture the full picture of the reviewer's engagement — understanding, questioning, probing, and accepting are equally important as finding issues. If the reviewer asked a question, understood the answer, and was satisfied, record that. If they found something to fix, record that too.
- **Changes made during review**: Table of files changed and what was done. Only include if changes were made.
- **Deferred**: Items acknowledged but accepted for this release.

## Closing

When the reviewer is happy:

1. Commit review changes and reviewer notes:
```bash
git add docs/releases/v<version>/reviewer_notes.md
git add -u  # any files changed during review
git commit -m "Add reviewer notes and review fixes for v<version>"
git push origin develop
```

2. Merge the PR:
```bash
gh pr merge <pr-number> --merge --delete-branch=false
```

3. Tell the user: "Release v<version> merged. Ask the release preparer to continue with `/release` to tag, monitor CI, and produce the post-release report."
