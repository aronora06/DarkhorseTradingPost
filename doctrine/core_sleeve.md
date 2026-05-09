# Core sleeve doctrine

**Notional:** $900 (90% of $1k)  
**Objective:** Meet or beat **SPY** net of costs over meaningful horizons with **drawdown discipline**. Default stance: **do nothing** unless edge is clear.

---

## 1. Mandate

- Long-only US equities meeting **`universe.md` Core filters**.
- **No options, futures, forex, crypto** in v1 (`plans/initialPlan.md` §2.7).
- **No leverage** beyond cash account mechanics Alpaca exposes.
- Benchmark-aware: evaluate thesis risk vs SPY drift + correlation regime.

---

## 2. Positioning & diversification posture

Target **~9–20** active Core positions at full deployment (`plans/initialPlan.md` §8.1) — binding constraint is microstructure + auditability, not maximizing ticker count.

**Default sizing guardrails (pre-code constants finalize in Phase 3):**

| Rule | Guideline |
|---|---|
| Single-name exposure | **≤ 12%** of Core NAV for initial entries unless risk-manager documents exceptional thesis + passes stricter confidence gate |
| Sector exposure | **≤ 25%** of Core NAV per GICS sector |
| Minimum viable position | Skip names where intended economic exposure would be dominated by spread/slippage noise |

Round explicitly to whole-share constraints imposed by broker — residual cash acceptable.

---

## 3. Trading style

- **Limit orders default.** Market orders require elevated confidence + explicit risk-manager flag (`plans/riskMitigation.md` §3 R4).
- **Turnover:** none targeted; churn flagged in weekly review if observed.
- **Core earnings rule:** exclude names with earnings within **next 2 trading days** (`plans/initialPlan.md` §8.1).

---

## 4. No-fly list (initial)

Reject Core exposure to:

- Leveraged / inverse ETFs
- Pending M&A names with **deal spread < 2%** (calendar arb traps)
- Symbols failing Core liquidity / price floors (`universe.md`)
- Any instrument class disallowed in v1 (`plans/initialPlan.md` §11)

---

## 5. Wind-down interaction

If rolling performance triggers SPY conversion (`plans/riskMitigation.md` §6), Core mandate yields to mechanical index posture — agent stops discretionary Core trades.

---

## Cross-links

- `doctrine/risk_policy.md`, `doctrine/universe.md`, `tests/specs/sizing.md`
