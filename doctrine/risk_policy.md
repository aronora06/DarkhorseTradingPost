# Risk policy — halts, kills, and regulatory guardrails

**Doctrine version:** v0.1-phase1  
**Aligned with:** `plans/initialPlan.md` §8, `plans/riskMitigation.md` §5–6

All thresholds below are enforced in **`validate_order`** and supporting risk modules — not via prompt plea bargains.

---

## 1. Sleeve economics (reference)

| Sleeve | Notional | Role |
|---|---:|---|
| Core | $900 | Conservative; SPY-competitive mandate |
| Satellite | $100 | Risk capital; survivable total loss |

No cross-funding between sleeves without explicit human-approved mechanics outside v1 agent scope.

---

## 2. Daily loss kill (“bad day” brake)

Stops intraday damage from bugs, broker issues, or agentic runaway.

| Sleeve | Threshold | Dollar anchor (@ full deploy) | Why this number |
|---|---:|---:|---|
| Core | **−2%** of sleeve NAV | −$18 | Tight brake on process failure; Tharp-style aggregate daily risk bound |
| Satellite | **−10%** of sleeve NAV | −$10 | Concentrated sleeve may swing intraday without implying strategy breakage |

**Effect:** freeze **that sleeve** until next trading session (or manual review — Phase 3 codifies exact state machine). Other sleeve unaffected unless shared account constraint forces joint pause.

---

## 3. Drawdown halt (“bad regime” brake, peak-to-trough)

Measured from **high water mark (HWM)** of sleeve equity curve. **HWM does not reset** after a halt-only recovery (`plans/initialPlan.md` §8.2).

| Sleeve | Halt threshold | Dollar anchor | Why this number |
|---|---:|---:|---|
| Core | **−15%** from HWM | −$135 from peak | Below SPY-scale trauma benchmark; triggers review before deeper impairment |
| Satellite | **None** | — | Halting explicit risk capital defeats its purpose; uncle point still applies |

**Effect:** Core sleeve frozen until Aaron manual unfreeze after review.

---

## 4. Uncle point (“stop trusting the system”)

Hard governance tripwire requiring **full doctrine review**, not a tactical pause.

| Sleeve | Threshold | Dollar anchor | Effect |
|---|---:|---:|---|
| Core | **−25%** from HWM | −$225 | Liquidate Core to SPY per wind-down posture (`riskMitigation` §6 path); freeze Satellite pending review |
| Satellite | **−80%** from HWM | −$80 | Near-total-loss tripwire; Satellite frozen; Core unaffected unless coupled risk |

Wind-down nuance: rolling 6-month Sharpe vs SPY triggers SPY conversion policy — see `plans/riskMitigation.md` §6 (orthogonal but complementary).

---

## 5. Pattern Day Trader (PDT) buffer

Accounts under **$25k** equity: **no day trades** encoded as strategy discipline.

**Buffered rule:** block when **2** round-trip day trades would occur within **5** rolling sessions if the requested trade completes — **one below** regulatory threshold of 3 (`plans/riskMitigation.md` §3 R7).

**Fail-closed:** if broker-reported day-trade counts unavailable or ambiguous → **NO_TRADE** pending reconciliation.

---

## 6. Spending & cadence tripwires (operational)

From `plans/riskMitigation.md` §5 (representative; Phase 3 binds exact env/config):

| Tripwire | Threshold | Response |
|---|---|---|
| Trades per day per sleeve | **3** hard max | Reject further aggressions |
| Single routine token spend | **$0.50** hard max | Abort routine loudly |
| Monthly Anthropic spend | **$10** console cap | External kill — routines fail visible |

---

## 7. Kill-switch file / env

Harness checks **`KILLSWITCH`** file flag + configured env before any LLM or order path (`plans/initialPlan.md` §3 design). Details finalized in Phase 3 implementation spec.

---

## Cross-links

- `doctrine/core_sleeve.md`, `doctrine/satellite_sleeve.md`  
- `tests/specs/kill_switch.md`, `tests/specs/drawdown.md`, `tests/specs/validate_order.md`  
- `RESEARCH/adversarial_vectors.md` OPS / regulatory rows
