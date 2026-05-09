# Developer handoff — Phase 3 progress (2026-05-09)

This document orients the **next implementation agent** after the first Phase 3 coding slice landed on `main` (commit **67b81c3** area). It summarizes a **code review**, a **documentation review**, and a **prioritized backlog** aligned with `plans/devPhaseChecklist.md`.

## 1. Where we are

### 1.1 Phase checklist (high level)

| Block | Status |
| --- | --- |
| Phase 0–2 steering / doctrine / architecture docs | Complete per checklist |
| **Phase 3.1** — Tooling, layout, CI, `.env.example`, `config/settings.toml` | **Implemented** — verify boxes in `devPhaseChecklist.md` when reviewed |
| **Phase 3.2** — Risk modules | **`validate_order`**, **`sizing`**, **`drawdown`**, **`kill_switch`**, **`wind_down`** implemented with tests. **No** dedicated integration module wiring these into a single “risk snapshot” yet — harness will compose. |
| **Phase 3.3** — Core utilities | **`config`**, **`idempotency`**, **`journal`**, **`audit`**, **`calibration`**, **`notify`** (+ minimal **`schemas/`**) implemented. |
| **Phase 3.4+** — Tools, hosting, funding | **Not started** in code |

### 1.2 What shipped in the repo

- **Package:** `src/darkhorse/` per ADR-0007 (`pyproject.toml`, `uv.lock`, Python **3.13**).
- **CI:** `.github/workflows/ci.yml` — `ruff`, `ruff format`, `mypy --strict src`, `pytest` with **`--cov=darkhorse --cov-fail-under=88`**.
- **Risk:** `risk/validate_order.py` is the hard gate; sibling modules provide **pure helpers** (HWM, caps, kill evaluation, soft wind-down predicate).
- **Config:** `Settings` in `config.py` loads **`config/settings.toml`** (repo root via path math) + **`.env`** at repo root; `get_settings()` is LRU-cached — use `clear_settings_cache()` in tests.
- **Persistence:** JSONL append with optional dedupe (`journal.py`); schemas aligned to subsets of `plans/dataSchema.md`.
- **Tests:** 59 tests (unit + Hypothesis on `validate_order`); `mypy --strict` clean on `src/`.

### 1.3 Intentional gaps (do not assume done)

- **`harness.py`**, **routines**, **tools/alpaca.py**, **`tools/_contracts.py`**, **FastAPI app** — not present.
- **Kill switch + drawdown + wind-down** are **not** yet called automatically from a routine entrypoint — `evaluate_kill_switch(...)` expects explicit paths/env; `validate_order` expects a fully-built `ValidationContext`.
- **Architecture doc vs code:** journal I/O is **`src/darkhorse/journal.py`**, not `tools/journal.py` (architecture updated in the companion commit).
- **`docs/architecture.md` §4.1** claimed risk “never reads doctrine” — enforcement numbers should stay in **`config/settings.toml`** + **`Settings`**; doctrine prose remains for the harness only.

## 2. Code review notes

### 2.1 Strengths

- **Risk in code:** `validate_order` encodes spec rule IDs; good audit trail.
- **Test discipline:** Property tests + high coverage on `darkhorse.risk.validate_order`; broad package coverage threshold in CI.
- **Settings:** Absolute paths for TOML/env avoid cwd surprises.
- **Idempotency:** 48-char Alpaca-safe `client_order_id` via deterministic hash.

### 2.2 Risks / follow-ups

1. **Sector sizing (SZ-02):** `sizing.sector_would_breach_cap` needs **caller-supplied** sector exposure; no GICS map in code yet — Alpaca/harness must provide sector bucket totals before submit.
2. **Kill remote behavior:** Remote check is **fail-closed** (blocks on HTTP errors). Confirm this matches operational preference vs “fail-open to local only.”
3. **`get_settings()` cache:** Long-running process is fine; tests or REPL that mutate env must call `clear_settings_cache()`.
4. **`DecisionJournalRecordV1`** is a **minimal** subset of `dataSchema.md` §1 — extending fields when the harness writes real decisions without breaking JSON consumers.
5. **Hypothesis / CI:** ADR-0009 — **no live LLM in CI**; current tests comply.

### 2.3 Style and imports

- Prefer **absolute imports** (`from darkhorse.risk import ...`).
- Ruff + mypy are mandatory gates — run `uv sync` then `uv run ruff check .`, `uv run mypy --strict src`.

## 3. Documentation review

| Artifact | Assessment |
| --- | --- |
| `docs/architecture.md` | Strong, current; **kill-switch env name** corrected to **`DARKHORSE_KILL`** to match code + `tests/specs/kill_switch.md`. Journal path note aligned with `journal.py` location. |
| `docs/README.md` | Accurate roles of `plans/` vs `docs/` vs `doctrine/`; list “planned” docs — **this handoff** is an early `docs/` addition. |
| `plans/devPhaseChecklist.md` | Source of truth for sequencing; **§3.1–3.3 checkboxes** should be ticked after human pass. |
| `doctrine/` + `tests/specs/` | Phase 1 approved — **code must stay faithful**; changes = doctrine PR discipline (`learningSystem.md`). |
| `suggestedNextSteps.md` (root) | Older framing (Phase 1); still useful for Aaron-owned tasks (**watchlist**, accounts). Next agent should treat **this handoff + checklist** as the implementation spine. |

## 4. Next steps (prioritized for the next agent)

### 4.1 Immediate — close Phase 3.1–3.3 bookkeeping

1. Update **`plans/devPhaseChecklist.md`** §3.1–§3.3 with dated `[x]` for completed items (human + Aaron gate per project norms).
2. Add **`docs/runbook.md`** stub or first-pass **“how to run pytest / pre-commit / CI locally”** pointer (optional if README suffices).
3. Ensure **`.hypothesis/`** is gitignored (done in companion commit).

### 4.2 Phase 3.4 — Tools (deterministic, no LLM in CI)

1. **`src/darkhorse/tools/_contracts.py`** — Pydantic IO models for every tool; `extra="forbid"` where appropriate.
2. **`src/darkhorse/tools/alpaca.py`** — Live + paper clients; **every submit** builds `OrderRequest` + `ValidationContext` and calls `validate_order`. Unit tests against **mocked HTTP**; optional **paper** integration test behind env flag (skipped in CI by default).
3. **`tools/data.py`**, **`tools/news.py`** — Finnhub/yfinance; Sonar/Tavily with **NFKC normalization** on news text (see `RESEARCH/adversarial_vectors.md`).
4. **Asset list job** — weekly pull Alpaca assets → `data/assets/YYYY-MM-DD.json` (gitignored dir); feed ticker whitelist for `validate_order`.

### 4.3 Composition layer (still Phase 3, pre-agent)

1. **Routine skeleton** — `python -m darkhorse.routines.<name>` loads `Settings`, runs `evaluate_kill_switch`, loads persisted HWM / halt flags (SQLite or JSON state file — **decide** per ADR-0003), builds `ValidationContext`, then calls harness placeholder (logging only) until LLM work starts.
2. **Wire `stale_human_review_pause`** — needs real timestamps from `git` or file mtimes for doctrine/journal paths (spec KS-03).
3. **`wind_down` → context** — rolling Sharpe vs SPY and Core return since start must be computed elsewhere; set `core_soft_wind_down_spy_only` on context when true.

### 4.4 Phase 3.5+ (hosting)

Per checklist: Hetzner, Tailscale, systemd, nginx/Caddy, B2 backups — **no code in the merged slice**; follow ADR-0005/0010/0011 when tooling is ready.

### 4.5 Phase 4+ (explicit non-goals until checklist says)

- **No** production harness with live Anthropic in CI.
- **No** doctrine auto-merged by agent without Aaron.

## 5. Quick commands (Aaron / agent)

```bash
cd /path/to/DarkhorseTradingOutpost
uv sync
uv run ruff check .
uv run ruff format .
uv run mypy --strict src
uv run pytest -ra --cov=darkhorse --cov-fail-under=88
```

Copy **`.env.example`** → **`.env`**; never commit secrets.

## 6. Open questions for the next agent

1. **Persisted drawdown / HWM state:** file under `memory/` vs SQLite mirror first — pick one and document in `dataSchema` or a short ADR note.
2. **Remote kill URL semantics:** document expected response body and operational runbook when URL is down.
3. **satellite_watchlist.md** is still placeholder — Satellite live path blocked until populated (Phase 9 path).

---

*When this backlog shifts materially, update this file or replace it with a dated successor in `docs/`.*
