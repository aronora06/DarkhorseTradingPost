# Frontend Dashboard Stack — 2026

**Compiled:** 2026-05-09
**Refresh by:** 2026-11-09
**Linked ADRs:** ADR-0004 (frontend stack)

## Summary

The 2026 server-rendered Python web stack has consolidated around **FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind CSS**, with **DaisyUI** as the recommended component layer to avoid hand-rolling buttons, modals, and form controls. Adding **Plotly.js** for charts (or Chart.js as a lighter fallback) covers the equity-curve / drawdown / calibration visualizations.

This stack delivers the full "single-user observability dashboard" use case in <1MB of frontend assets, with no build pipeline, no SPA framework, and full server-side data fetching from the same Python project as the agent. It is the right call for Darkhorse and for the broader "internal tool dashboard" pattern.

## Sources reviewed

- TestDriven.io, "Using HTMX with FastAPI" (updated 2026)
- ggoggam.github.io, "Making a simple dashboard with HTMX" (TIL)
- tech-insider.org, "HTMX Tutorial: Build a Live Web App in 13 Steps [2026]"
- volfpeter/fastapi-htmx-tailwind-example (GitHub) — full IoT dashboard reference
- kszongic/htmx-fastapi-starter (GitHub) — 2026 starter template

## Key findings

### 1. The HX-Request header is the hinge

The clean pattern: one URL, two response shapes.

```python
@app.get("/portfolio")
async def portfolio(request: Request, sleeve: str = "core"):
    data = await load_portfolio(sleeve)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "portfolio_fragment.html", {"request": request, "data": data}
        )
    return templates.TemplateResponse(
        "portfolio_full.html", {"request": request, "data": data}
    )
```

`portfolio_full.html` extends a base layout; `portfolio_fragment.html` is just the inner content. This means:
- Direct browser navigation gets a full page
- HTMX-triggered swaps get just the fragment
- Same data, same code, two presentations

### 2. Jinja2 fragment templates

Template inheritance + `{% block %}` directives let us serve full pages and named fragments from the same template tree. The `jinja2-fragments` package adds `render_block(template, block_name, context)` for cases where a single template should yield multiple sub-fragments.

For Darkhorse: probably not needed in v1. Two-template pattern (full + fragment) is enough.

### 3. Alpine.js for client-side interactivity

HTMX handles server-driven updates. Alpine handles client-side state where a roundtrip is wasteful — modals, dropdowns, kill-switch confirm dialog, the dashboard filter chips. ~14KB minified, no build pipeline.

Pattern:
```html
<div x-data="{ confirmOpen: false }">
  <button @click="confirmOpen = true">Toggle Killswitch</button>
  <div x-show="confirmOpen" class="modal">
    ...
    <button hx-post="/killswitch/toggle"
            hx-confirm="Type 'TOGGLE' to confirm"
            @click="confirmOpen = false">Confirm</button>
  </div>
</div>
```

The kill-switch toggle is the most security-sensitive write action; pair Alpine's UI state with HTMX's `hx-confirm` for the actual destructive call.

### 4. Tailwind + DaisyUI

Tailwind alone means hand-rolling component classes (which we will not do well as a single-user project). **DaisyUI** is a Tailwind plugin that provides ready-made `btn`, `card`, `modal`, `table`, `alert`, `stat`, `tabs`, `navbar` components — all themable, all CSS-only, no JS dependency.

Adding DaisyUI:
- Install via npm or CDN (we'll use CDN to avoid a build pipeline)
- Configure 1–2 themes (light + dark) in a `<style>` tag or config
- Class-based usage in templates: `<button class="btn btn-primary">`

Total stack weight: Tailwind via CDN (~50KB after CSS-tree-shaking) + DaisyUI (~15KB) + HTMX (~14KB) + Alpine (~14KB) ≈ **<100KB** of frontend assets total. Plus Plotly (~3MB if loaded), but only on the Performance and Calibration pages.

### 5. Charts: Plotly vs Chart.js

| Charts | Plotly.js | Chart.js |
|---|---|---|
| Bundle size | ~3.4MB (full) / ~250KB (basic) | ~70KB |
| Interactivity | Excellent (zoom, pan, hover, export) | Good (hover, basic zoom) |
| Configuration | More verbose | More concise |
| Time-series | Excellent | Good |
| Plotting financial OHLC | First-class | Plugin required |

Recommendation:
- **Plotly.js for the Performance and Calibration pages** (equity curve, drawdown, confidence histograms) — interactivity matters, file size doesn't (the dashboard isn't bandwidth-constrained on Tailscale).
- Use Plotly's CDN; load only on the pages that need it.
- Chart.js is a fallback only if Plotly's bundle becomes a problem (unlikely on a single-user dashboard).

### 6. Forms and writes

Two write actions in the dashboard (per `frontendAndHosting.md`):
1. Kill-switch toggle.
2. Doctrine PR approval/rejection.

Both are low-frequency, high-stakes. Confirmation pattern: HTMX `hx-confirm` for one-shot prompts; for the kill-switch, a typed-confirmation modal ("type TOGGLE to confirm") to defeat habituation.

### 7. Server-Sent Events for live updates

For "Last 3 decisions feed" and "live cost meter," SSE via `EventSourceResponse` (`sse-starlette` package) gives us push updates without WebSocket complexity. HTMX has native SSE support via `hx-ext="sse"` and `sse-connect`.

For v1: polling at 30–60 second intervals is simpler and entirely sufficient. SSE upgrade if Aaron wants live tape behavior on a particular page later.

### 8. Authentication via Tailscale only

The dashboard binds to the tailnet interface. There is no application-level auth in v1. Per `frontendAndHosting.md`, "presence on the tailnet *is* the credential." The only write actions are guarded by the typed-confirmation modal.

In Phase 6+ if we add Cloudflare Access, we get a layer of identity-aware proxy on top — still no application-level auth code, just an HTTP header trust setup.

## Implications for Darkhorse

Locked frontend stack:

| Layer | Choice | Notes |
|---|---|---|
| App framework | FastAPI | Already in use for the rest of the project |
| Templating | Jinja2 | Two-template pattern (full + fragment) |
| Client interactivity | HTMX 2.x | HX-Request header drives content negotiation |
| Component state | Alpine.js | Modals, dropdowns, dashboard filters |
| Styling | Tailwind CSS via CDN | No build pipeline |
| Components | DaisyUI plugin | Buttons, cards, modals, tables out of the box |
| Charts | Plotly.js (CDN, loaded on chart pages only) | Chart.js fallback if perf issue |
| Live updates (v1) | Polling 30–60s | Upgrade to SSE only if Aaron wants live tape |
| Auth | Tailscale presence | Confirmation modals on writes |

Repository layout:
```
src/darkhorse/web/
├── app.py                  # FastAPI app
├── routes/
│   ├── overview.py
│   ├── portfolio.py
│   ├── performance.py
│   ├── calibration.py
│   ├── decisions.py
│   ├── lessons.py
│   ├── anti_patterns.py
│   ├── costs.py
│   ├── system_health.py
│   └── writes.py           # killswitch + doctrine PR actions
└── templates/
    ├── base.html
    ├── overview_full.html
    ├── overview_fragment.html
    ├── ...
static/
├── css/
│   └── tailwind.config.css   # if we ever build locally
└── js/
    ├── htmx.min.js           # vendored
    ├── alpine.min.js         # vendored
    └── plotly.min.js         # CDN'd by default; vendored if offline-needed
```

Vendoring vs CDN:
- HTMX, Alpine, Tailwind+DaisyUI: vendor (versions pinned in `static/`). CDN as a backup or initially.
- Plotly: CDN only, loaded conditionally.

## Open questions

- **htmx-extensions to enable.** `class-tools`, `loading-states` are nice quality-of-life. Decide in Phase 6.
- **CSP / security headers.** Tailscale-only access reduces the threat surface but a basic CSP is still hygienic. Configure in nginx (or Caddy).
- **Mobile optimization.** Aaron explicitly wants phone access. DaisyUI is mobile-friendly by default; verify on the Overview page first.
- **Dark mode.** DaisyUI ships dark themes. Decide default at first dashboard PR.
