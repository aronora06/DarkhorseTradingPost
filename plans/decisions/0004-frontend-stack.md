# ADR-0004: Frontend Stack — FastAPI + HTMX + Alpine + Tailwind + DaisyUI

## Status

`accepted` (2026-05-09)

## Context

The dashboard is a single-user, read-mostly observability tool with two write actions (kill-switch toggle, doctrine PR approval). Per `../frontendAndHosting.md`, design constraints:

- Single user; no multi-tenancy
- No real-time sub-second updates needed
- No order entry by Aaron through the UI (intentional)
- "Useful > pretty" — but not ugly
- Aaron must be able to use it from his phone via Tailscale

Multiple stacks could deliver this:
- **Next.js / React SPA** — the default for "modern" web frontends
- **HTMX + Alpine + Tailwind** — server-rendered interactivity
- **Streamlit / Gradio** — Python-native dashboards
- **Hand-rolled vanilla JS + Flask templates** — older but workable

## Decision

**FastAPI (backend) + Jinja2 templates + HTMX + Alpine.js + Tailwind CSS + DaisyUI (frontend) + Plotly.js (charts only on chart pages).**

- **FastAPI** — same Python project as the agent; shares config, journal readers, schemas
- **Jinja2** — templates with full-page + fragment patterns triggered by `HX-Request` header
- **HTMX 2.x** — content swapping, polling for live-ish updates, confirmation dialogs
- **Alpine.js** — client-side state for modals, dropdowns, the kill-switch confirm flow
- **Tailwind CSS via CDN** — utility classes; no build pipeline
- **DaisyUI** — Tailwind plugin providing buttons, cards, modals, tables, alerts, stats. Avoids hand-rolling components.
- **Plotly.js (CDN, conditionally loaded)** — interactive charts on Performance and Calibration pages only

Total frontend asset weight: <100 KB excluding Plotly. Plotly only loads when its page is visited.

Authentication: **Tailscale presence is the credential.** No application-level auth in v1.

## Consequences

### Positive

- Zero build pipeline. No Node, no webpack, no separate frontend repo. Aaron can read the entire frontend stack in one sitting.
- One language end-to-end (Python). Schema changes propagate from pydantic models through templates without translation layers.
- DaisyUI eliminates the "I have to design every button" tax. The dashboard looks competent without bespoke design.
- HTMX's content-negotiation pattern (one URL, full or fragment based on `HX-Request`) means data fetching code is shared between full-page nav and partial swaps.
- Single-process deployment: FastAPI serves both API and HTML from the same uvicorn process behind nginx. Operational simplicity matches what the project values everywhere else.

### Negative / costs

- Heavy interactive viz (drag-to-zoom on multi-pane charts, custom drawing) is harder than in a React+D3 setup. Plotly handles 95% of likely needs; the 5% case requires hand-coded JS or migration.
- HTMX is ~4 years old and stable but smaller community than React. If we hire engineers (we won't), they'd need to learn it.
- Tailwind via CDN means no class-tree-shaking — we ship the full Tailwind CSS file (~50 KB after gzip). Acceptable on Tailscale; a build pipeline would shrink this further but adds complexity.

### Neutral

- Mobile responsiveness comes from Tailwind+DaisyUI defaults; works on Aaron's phone without custom mobile-first design.

## Alternatives considered

- **Next.js / React SPA.** Full power for any future interactivity. Rejected: requires Node, build pipeline, separate API contract, deployment complexity. Single-user dashboard doesn't earn this. Revisit if Phase 10+ wants multi-pane interactive analytics that exceed Plotly.
- **Streamlit.** Fastest to a first dashboard. Rejected: the routing and state model fights against multi-page apps; auth and customization are awkward; aesthetics are recognizably "Streamlit." Strong choice for a one-shot research notebook, weak for a production dashboard we'll live with for a year.
- **Gradio.** Same caveats as Streamlit, more ML-demo flavored.
- **Vanilla Flask + jQuery.** Workable but jQuery is a step back from HTMX in 2026; HTMX gets us the same patterns with less code.
- **Vue / Svelte SPA.** Lighter than React but same build-pipeline objection. Defer.

## Falsification criterion

This decision is wrong if:

- A dashboard feature genuinely requires interactivity beyond what HTMX + Alpine + Plotly can deliver (e.g., Aaron wants to draw trade annotations directly on the equity curve).
- Page-load times exceed 2 seconds on the Tailscale path despite asset optimization.
- Aaron finds the dashboard unpleasant enough to use that he stops opening it (the bored-owner failure mode in `../riskMitigation.md` R16). Subjective but real — this is the most user-experience-sensitive decision in the project.

## Linked hypotheses

None. The dashboard is a tool, not a research artifact.

## Re-check date

2026-11-09 (6 months) — re-evaluate after Aaron has used the dashboard daily for several months.

## References

- `../frontendAndHosting.md` (information architecture, page-level requirements)
- `../../RESEARCH/architecture/frontend_dashboard_stack.md` (research note that informed this decision)
- HTMX 2.x docs, Alpine.js docs, DaisyUI components
