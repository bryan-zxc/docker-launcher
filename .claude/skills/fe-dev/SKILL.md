---
name: fe-dev
description: Frontend development reference for the Docker Launcher dashboard. Use when modifying or extending src/docker_launcher/static/index.html — adding UI features, changing styles, creating new components, or fixing frontend bugs. Provides the design system tokens, component patterns, and testing workflow.
---

# Frontend Development

The frontend is a single file at `src/docker_launcher/static/index.html` — vanilla HTML, CSS custom properties, and plain JS. No build step, no framework.

## Design System — Option A Midnight

### Typography
- **Font**: Outfit (Google Fonts) — weights 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)
- **Fallback**: `'Outfit', system-ui, sans-serif`
- **Monospace**: Use a monospace font **only** for logs, tags, and hashes — never for headings, labels, or body text
- **Icons**: Material Symbols Outlined (Google Fonts CDN), always rendered as `<span class="material-symbols-outlined">icon_name</span>`
- **Never use emoji** — always use Material Symbols or inline SVG

### Colour Tokens (CSS custom properties)

All colours are defined as CSS custom properties on `html.light` and `html.dark`. Always use `var(--token)` — never hardcode hex values in component styles.

**Core surfaces:**
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--bg` | #F5F5F5 | #0a0a0a | Page background |
| `--surface` | rgba(255,255,255,0.7) | rgba(20,20,20,0.6) | Glass-morphism cards, panels |
| `--elevated` | rgba(255,255,255,0.85) | rgba(30,30,30,0.7) | Highlighted surfaces |
| `--border` | rgba(0,0,0,0.08) | rgba(255,255,255,0.08) | Standard borders |
| `--border-subtle` | rgba(0,0,0,0.05) | rgba(255,255,255,0.05) | Hover borders |

**Text:**
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--heading` | #000000 | #ffffff | H1-H3, primary text |
| `--subheading` | #222222 | #D0D0CE | Secondary headings |
| `--body` | #63666A | #97999B | Body text |
| `--muted` | #75787B | #75787B | Meta text, labels |
| `--disabled` | #A7A8AA | #53565A | Disabled states |

**Accent:**
| Token | Value | Usage |
|-------|-------|-------|
| `--accent` | project accent colour | Primary buttons, active nav, highlights |
| `--accent-hover` | slightly darker shade | Hover state for accent |
| `--accent-tint` | accent at 0.08-0.10 alpha | Background tints |
| `--accent-border` | accent at 0.16-0.18 alpha | Accent borders |

**Status colours:**
| Token | Usage |
|-------|-------|
| `--green` / `--green-tint` | Running, success |
| `--amber` / `--amber-tint` | Building, warning |
| `--rose` / `--rose-tint` | Error, danger, delete |
| `--blue` / `--blue-tint` | VS Code, info, links |

### Glass-morphism

Cards and panels use glass-morphism styling:
- `background: var(--surface)` (semi-transparent)
- `backdrop-filter: blur(12px)` / `-webkit-backdrop-filter: blur(12px)`
- `border: 1px solid var(--border)`
- `border-radius: 12px` (or as appropriate)

### Theme System
- Light/dark via `html.light` / `html.dark` class on the root element
- Toggled by `toggleTheme()`, persisted in `localStorage`
- All theme-aware CSS uses `var(--token)` so switching is automatic
- For dark-only overrides: `html.dark .some-class { ... }`

### Layout
- **Sidebar**: fixed width, always dark, contains brand, nav, theme toggle
- **Main area**: flex column — topbar (surface bg, border-bottom), scrollable content area
- **Content padding**: 28px 32px
- **Drawer**: slides from right, overlay + panel, z-index 50/60

### Component Classes

**Buttons:**
- `.btn` — default bordered button
- `.btn-primary` — accent fill button
- `.card-btn` — small action button on container cards
- `.card-btn.vscode` — blue-tinted VS Code button
- `.card-btn.danger` — red on hover (delete)

**Cards:**
- `.container-card` — glass-morphism card with backdrop-filter blur
- `.card-status-bar.{running|exited|created|creating}` — coloured left bar
- `.status-tag.{running|exited|created|creating}` — inline status pill

**Form:**
- `.create-panel` — rounded panel with `.create-form` grid inside
- `.form-group` — label (uppercase, 11px) + input/select

**Drawer:**
- `.drawer` / `.drawer-overlay` — toggle with `.open` class
- `.drawer-log` — monospace log area with `.log-line.{info|error|success}`

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/images` | List image definitions |
| GET | `/api/images/{name}` | Get single image |
| POST | `/api/images/{name}/build` | SSE stream — build image |
| GET | `/api/containers` | List containers |
| POST | `/api/containers` | Create container (`{image, repo_url?, name?}`) |
| POST | `/api/containers/{id}/start` | Start container |
| POST | `/api/containers/{id}/stop` | Stop container |
| POST | `/api/containers/{id}/vscode` | Get VS Code URI |
| DELETE | `/api/containers/{id}` | Delete container + volumes |

## Testing with Playwright

Always verify frontend changes in a headed browser.

### Start the app
```bash
uv run docker-launcher &   # default port
```

### Open headed browser
```bash
PLAYWRIGHT_MCP_SANDBOX=false playwright-cli open http://localhost:3000 --headed
```

Both `--headed` and `PLAYWRIGHT_MCP_SANDBOX=false` are **required** — without them the browser is invisible to the user.

### Interact and verify
```bash
playwright-cli snapshot                    # get current page state with element refs
playwright-cli click e5                    # click element by ref
playwright-cli fill e12 "some text"        # fill input
playwright-cli eval "someFunction()"       # run JS in page
playwright-cli screenshot                  # capture viewport
```

### Clean up
```bash
playwright-cli close
```

### Troubleshooting
- If `playwright-cli` is not found, run `playwright-cli install --skills` first
- If the default port is occupied, use a different port via config or environment variable
- Do **not** use `reload=True` with uvicorn — it breaks `Path(__file__)` resolution on Windows
