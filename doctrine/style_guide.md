# Agent output style guide

Defines **machine-checkable shapes** for decisions and journals. Prompt prose may vary; **schemas must not**.

---

## 1. Doctrine versioning

Each routine load pins:

| Field | Example | Meaning |
|---|---|---|
| `doctrine_git_sha` | `abc123f` | Commit SHA of `doctrine/` consumed |
| `doctrine_bundle_version` | `v0.1-phase1` | Human-readable bundle tag |

Every journal line repeats these fields (`plans/riskMitigation.md` §3 R8 drift mitigation).

---

## 2. Decision JSON (pre-submission)

Emitted by risk-manager role; validated via **Anthropic structured outputs** before Python walls (`plans/decisions/0002-tiered-model-strategy.md`, `RESEARCH/architecture/anthropic_sdk_features.md`).

**Minimal required keys:**

```json
{
  "schema_version": "decision_v1",
  "sleeve": "core | satellite",
  "symbol": "SPY",
  "side": "buy | sell | hold",
  "qty": 0,
  "confidence": 0.0,
  "time_in_force": "day | gtc",
  "risk_checks": {
    "pdta_safe": true,
    "within_sleeve_notional": true,
    "universe_allowed": true,
    "earnings_rule_ok": true
  },
  "playbook": null,
  "reason_summary": "≤280 chars plain text"
}
```

**Rules:**

- `confidence` ∈ [0,1]; trades **require** ≥ **0.70** AND all `risk_checks` true **before** `validate_order`.
- `playbook` nullable string enum (e.g., `"post_earnings_drift_v1"`) when Satellite uses explicit playbook.
- Unknown fields forbidden (forward-compatible bumps increment `schema_version`).

---

## 3. Journal JSONL rows

Append-only JSON lines (`memory/<sleeve>/journal/YYYY-MM-DD.jsonl` — Phase 3 paths).

**Minimal keys:**

| Field | Notes |
|---|---|
| `ts_utc` | ISO8601 |
| `routine` | `pre_market`, `market_open`, ... |
| `doctrine_git_sha`, `doctrine_bundle_version` | Duplicated |
| `decision` | Embedded Decision JSON or `null` if NO_TRADE |
| `model_trace_id` | Provider trace for audit |
| `outcome_link` | Pending until fills reconcile |

NO_TRADE entries still logged with explicit reason enum (`uncertainty`, `data_missing`, `risk_blocked`, ...).

---

## 4. Prompt-facing narrative rules

- Prefer bullet reasoning over essays; cite source tiers (`news_sources.md`).
- Mandatory **`30-day base rate`** reflection subsection each routine (`plans/initialPlan.md` §3.4).
- No hedged imperative doublespeak (“probably should buy now”) — pick **hold** if unclear.

---

## Cross-links

- `plans/dataSchema.md` (telemetry specifics — ensure consistency Phase 3)  
- `tests/specs/idempotency.md` for order keys
