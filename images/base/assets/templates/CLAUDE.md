# Project Instructions

## Python Environment

- Always activate `.venv` before running any skill scripts: `source .venv/bin/activate`
- Use `uv add <package>` to add dependencies -- never edit `pyproject.toml` directly
- Use `uv` for all package management (not pip)
- If `.venv/` is not in `.gitignore`, add it

## System Dependencies

Some skills may require system packages that are not pre-installed (e.g. LibreOffice, Tesseract OCR, Poppler). If a script fails due to a missing system tool, install it with `sudo apt-get install -y <package>`.

## Skills

Skills are available in `.claude/skills/`. Each has a `SKILL.md` with usage instructions.

Available skills:
- **playwright-cli** -- browser automation and testing
- **docx** -- create, read, and edit Word documents
- **pdf** -- PDF processing, form filling, text extraction
- **pptx** -- create and edit PowerPoint presentations
- **xlsx** -- spreadsheet creation and manipulation
- **sync** -- stage, commit, pull, and push changes
