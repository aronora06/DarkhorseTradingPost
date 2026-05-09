# Satellite sleeve doctrine

**Notional:** $100 (10% of $1k) — **explicit risk capital**; total loss must remain survivable (`plans/initialPlan.md` §1).

---

## 1. Mandate

- Seek **asymmetric, thesis-driven** opportunities inside disciplined guardrails.
- Still **no options / futures / forex / crypto** until each asset class gets a written policy (`plans/initialPlan.md` §2.7).
- Satellite **may** accept earnings volatility **only** via the playbook below — no ad-hoc “special pleading.”

---

## 2. Universe & concentration

- Starts from **Satellite universe** definition (`doctrine/universe.md`): S&P 500 core filters **plus** curated extension list (`satellite_watchlist.md`).
- **Maximum single position:** **50%** of Satellite NAV (**$50** at full deploy) — hard cap in `validate_order`.
- Liquidity floors weaker than Core but still binding (`universe.md`).

---

## 3. Post-earnings drift playbook (explicit)

**Goal:** exploit **post-event repricing** without gambling pre-announcement uncertainty like Core avoids.

### Preconditions (all must pass)

| Gate | Requirement |
|---|---|
| PE-1 | Earnings event **released** (confirmed timestamp from structured data provider or primary IR feed — not headlines alone) |
| PE-2 | Symbol on valid tradable list & passes Satellite liquidity filters **post-gap** |
| PE-3 | **Skip first 15 minutes** after regular-session open following the overnight reaction (manual timing baked into routine schedule — Phase 3 encodes clock) |
| PE-4 | **Volume confirmation:** session volume ≥ **1.25×** 20-day ADV by midday check **or** deliberate thesis stating why liquidity is sufficient anyway (bear must argue contra) |

### Entry mechanics

| Parameter | Rule |
|---|---|
| Direction | Long-only v1; shorting excluded unless future ADR |
| Thesis | Must cite **two independent corroborating sources** (`news_sources.md` tiers) for the drift mechanism (guidance change, margin trajectory, narrative reset — not “it popped” alone) |
| Size cap first tranche | **≤ 25%** of Satellite NAV (**$25**) before partial confirmation (close +1 session stable beyond gap extremes) |
| Add-on | Scale toward **50%** cap only if Day+2 price holds inside gap window **and** no adverse filing |

### Invalidation & exits

| Trigger | Action |
|---|---|
| Thesis contradiction | Exit ≤ **T+3** sessions at prevailing limits unless risk-manager documents fresh thesis |
| Gap-fill adverse move | Exit if price retraces **> 75%** of earnings gap against position direction |
| Liquidity degradation | If spreads widen beyond Satellite slippage tolerance → NO_TRADE / flatten |
| Macro shock overlap | Fed / CPI surprise same window → shrink size **50%** or abstain |

### Logging

Journal entries must tag `playbook: post_earnings_drift_v1` plus checklist gates satisfied — enables calibration reviews.

---

## 4. Interaction with Core

Satellite journals separate from Core; **no implicit hedge assumptions** across sleeves.

---

## Cross-links

- `doctrine/universe.md`, `doctrine/satellite_watchlist.md`, `doctrine/news_sources.md`  
- `tests/specs/sizing.md`, `tests/specs/adversarial.md` EVT-02  
- `RESEARCH/practitioner_dossiers/universe_small_account.md`
