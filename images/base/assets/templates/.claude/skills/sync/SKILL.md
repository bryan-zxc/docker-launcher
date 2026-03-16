---
name: sync
description: "Use when the user says /sync, 'sync', 'push changes', 'commit and push', or wants to save and push their work. Stages all changes, commits with an auto-generated message, pulls, and pushes."
---

# Sync

Stage all changes, commit, pull, and push in one step. Minimise questions -- just do it.

## Workflow

1. Stage all changes:
   ```bash
   git add -A
   ```

2. Generate a commit message from the staged diff:
   - Summarise what changed in 1-2 sentences
   - Use conventional commit format (feat:, fix:, chore:, docs:, etc.)

3. Commit:
   ```bash
   git commit -m "<generated message>"
   ```

4. Pull to integrate remote changes:
   ```bash
   git pull
   ```

5. If there are merge conflicts:
   - Attempt to resolve them automatically where possible
   - For conflicts you cannot resolve, show the user the conflicting files and ask for guidance
   - After resolving, `git add` the resolved files and `git commit`

6. Push:
   ```bash
   git push
   ```

## Rules

- Do NOT ask the user to confirm the commit message -- just commit
- Do NOT ask the user to review the diff before committing -- just commit
- If `git pull` has no conflicts, proceed silently
- If push fails due to non-fast-forward, pull again and retry once
- Always report the final status (success or failure) when done
