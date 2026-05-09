# Darkhorse Trading Outpost — Data Schema

The schemas below define the shapes of every durable artifact the system produces. These are what the **learning system** in `learningSystem.md` operates on. Keeping them stable, versioned, and validated is what allows the system to actually learn rather than accumulate noise.

All JSONL files use **schema_version** as the first field. Schema migrations happen through forward-compatible additions; breaking changes require a new file with a new version and a one-shot migration.

## Conventions

- All timestamps: ISO-8601 UTC with `Z` suffix.
- All money: USD, decimal as string (avoid float for currency).
- All tickers: uppercase, validated against the asset list.
- All IDs: prefixed by entity type (`dec_`, `les_`, `ant_`, `pmt_`, `cal_`).
- All optional fields: explicit `null`, not omitted.

---

## 1. Decision Entry (Episodic / L1)

**Path:** `memory/<sleeve>/journal/YYYY-MM-DD.jsonl`

One line per decision (including NO_TRADE). Append-only. Source of truth for everything else.

```json
{
  "schema_version": "1.0",
  "decision_id": "dec_2026-05-12_1335_AAPL_a3f9",
  "timestamp": "2026-05-12T13:35:00Z",
  "sleeve": "core",
  "routine": "market_open",
  "doctrine_version": "git-sha-of-doctrine-tree",
  "prompt_version": "git-sha-of-prompts-tree",
  "model_assignments": {
    "researcher": "claude-sonnet-4-6",
    "bull_analyst": "claude-sonnet-4-6",
    "bear_analyst": "claude-sonnet-4-6",
    "risk_manager": "claude-opus-4-7"
  },
  "ticker": "AAPL",
  "action": "BUY",
  "qty": "5",
  "order_type": "limit",
  "limit_price": "189.50",
  "time_in_force": "day",
  "confidence": 0.78,
  "expected_horizon_days": 14,
  "expected_outcome_pct": 0.04,
  "thesis_summary": "Post-earnings drift continuation; bear case (China softness) discounted by services growth.",
  "reasoning_trace": {
    "researcher_summary": "...",
    "bull_argument": "...",
    "bear_argument": "...",
    "risk_manager_verdict": "..."
  },
  "tools_used": [
    {"tool": "data.quote", "args": {"ticker": "AAPL"}, "result_hash": "sha256:..."},
    {"tool": "news.sonar", "args": {"q": "AAPL earnings", "recency": "week"}, "result_hash": "sha256:..."}
  ],
  "risk_checks": {
    "validate_order_passed": true,
    "checks_run": ["sleeve_position_cap", "daily_loss_kill", "drawdown_halt", "ticker_whitelist", "pdt_safe", "kill_switch_off"],
    "kill_switch_state": "off"
  },
  "lessons_referenced": ["les_023", "les_041"],
  "anti_patterns_flagged": [],
  "alpaca": {
    "client_order_id": "core_2026-05-12_AAPL_buy_a3f9",
    "broker_order_id": null,
    "submitted_at": "2026-05-12T13:35:01Z",
    "fill_status": "pending"
  },
  "cost": {
    "input_tokens": 28543,
    "cached_input_tokens": 21034,
    "output_tokens": 4120,
    "total_usd": "0.0184"
  },
  "outcome": null
}
```

The `outcome` field is null at write time. A separate post-horizon process backfills it once the expected_horizon_days has elapsed:

```json
"outcome": {
  "filled_at": "2026-05-12T13:35:14Z",
  "filled_price": "189.48",
  "horizon_end": "2026-05-26T13:35:00Z",
  "exit_price": "194.80",
  "exit_reason": "horizon_reached",
  "realized_pct": 0.0281,
  "realized_usd": "26.45",
  "slippage_bps": 0.8,
  "outcome_class": "winner"
}
```

**Validators:**
- Every required field present
- Ticker in current asset list
- `client_order_id` matches deterministic derivation
- `cost.total_usd` ≤ per-routine cap
- Either `validate_order_passed: true` AND an Alpaca submission, OR action == `"NO_TRADE"`

---

## 2. Calibration Entry

**Path:** `memory/<sleeve>/calibration.jsonl`

One line per resolved decision (after horizon). Built by the post-horizon process from decision entries.

```json
{
  "schema_version": "1.0",
  "calibration_id": "cal_dec_2026-05-12_1335_AAPL_a3f9",
  "decision_id": "dec_2026-05-12_1335_AAPL_a3f9",
  "sleeve": "core",
  "decision_timestamp": "2026-05-12T13:35:00Z",
  "horizon_end": "2026-05-26T13:35:00Z",
  "predicted_confidence": 0.78,
  "predicted_outcome_pct": 0.04,
  "realized_outcome_pct": 0.0281,
  "outcome_class": "winner",
  "doctrine_version": "git-sha",
  "prompt_version": "git-sha",
  "tags": ["sector:tech", "post_earnings", "large_cap", "thesis:drift_continuation"]
}
```

**Used by:** `src/learning/calibration_analysis.py` to compute confidence-bucket hit rates and detect drift.

---

## 3. Lesson Entry (Semantic / L2)

**Path:** `memory/<sleeve>/lessons.md` (markdown, not JSONL — humans edit these)

Each lesson is a markdown section with structured frontmatter:

```markdown
---
lesson_id: les_023
title: Post-earnings drift survives 5–10 trading days, not 30
status: active
created: 2026-06-15
sunset: 2026-12-15
revalidations: []
hypothesis: |
  Post-earnings drift signal decays after roughly 10 trading days; positions
  taken on the drift thesis should size for that horizon, not longer.
falsification: |
  If decisions tagged "thesis:drift_continuation" with horizon > 10 days
  outperform those with horizon ≤ 10 days over a rolling 13-week sample
  with N >= 20 in each bucket.
evidence_decisions:
  - dec_2026-06-02_..._MSFT_...
  - dec_2026-06-04_..._GOOG_...
  - (3 more)
proposed_changes:
  - prompts/risk_manager.md: cap horizon for drift theses at 10 trading days
  - doctrine/core_sleeve.md: add explicit horizon guidance for earnings-driven entries
supersedes: null
superseded_by: null
---

## les_023 — Post-earnings drift survives 5–10 trading days, not 30

[Long-form discussion follows...]
```

**Used by:** every routine, via prompt cache. Filtered to `status: active`.

---

## 4. Anti-Pattern Entry (L3)

**Path:** `doctrine/anti_patterns.md` (promoted to doctrine because anti-patterns are durable)

```markdown
---
anti_pattern_id: ant_007
name: Recency-driven thesis flip
created: 2026-07-08
last_observed: 2026-09-22
status: active
description: |
  Agent flips a previously-justified thesis based on a single news article from the last 24h
  without referencing the 30-day base rate.
telltale_signs:
  - Action reverses on a position held < 5 days
  - Reasoning trace cites only news < 24h old
  - Bear/bull argument doesn't mention prior thesis
mitigation: |
  Risk-manager must explicitly answer "What changed in the last 30 days that
  is structurally different, not just news?" before approving a reversal.
origin_post_mortem: pmt_017
---

## ant_007 — Recency-driven thesis flip

[Long-form discussion...]
```

**Used by:** every routine. Risk-manager prompt explicitly references the active anti-pattern list.

---

## 5. Post-Mortem Entry

**Path:** `memory/<sleeve>/post_mortems/pmt_NNN.md`

Triggered automatically by losing trade > 1% of sleeve NAV, daily-loss kill firing, or drawdown halt.

```markdown
---
post_mortem_id: pmt_017
trigger: losing_trade_over_1pct
triggered_at: 2026-07-07T20:30:00Z
related_decisions:
  - dec_2026-07-03_..._XYZ_...
loss_usd: -12.40
loss_pct_of_sleeve: -0.0138
sleeve: core
status: complete
proposed_anti_patterns: [ant_007]
proposed_lessons: []
---

## What happened
[narrative]

## Why it happened
[root cause analysis]

## What anti-pattern (if any) does this represent?
[either references existing or proposes new]

## What would have prevented it?
[concrete proposed change to doctrine/prompts/anti-patterns]
```

---

## 6. Reasoning Pattern Snapshot (L4)

**Path:** `memory/<sleeve>/reasoning_patterns/YYYY-Qn.md`

Auto-generated quarterly. Read by Aaron, **not** by the agent.

```markdown
---
snapshot_id: rps_2026Q3_core
generated: 2026-09-30
sleeve: core
sample_size: 50
sample_method: stratified_random_by_confidence_outcome
audit_model: claude-haiku-4-5
---

## Reasoning style frequencies
- "Bear case treated substantively" — 64% (was 51% in 2026Q2)
- "30-day base rate referenced" — 78% (was 72%)
- ...

## Notable patterns
[narrative observations]

## Recommendations for Aaron's review
[suggested prompt or doctrine evolutions]
```

---

## 7. Cost Telemetry

**Path:** `memory/cost/YYYY-MM-DD.jsonl`

Per-routine cost record. One line per routine invocation.

```json
{
  "schema_version": "1.0",
  "routine": "market_open",
  "sleeve": "core",
  "started_at": "2026-05-12T13:35:00Z",
  "ended_at": "2026-05-12T13:35:42Z",
  "duration_ms": 41843,
  "model_calls": [
    {
      "role": "researcher",
      "model": "claude-sonnet-4-6",
      "input_tokens": 8123,
      "cached_input_tokens": 6200,
      "output_tokens": 1450,
      "usd": "0.0040"
    }
  ],
  "tool_calls": {
    "data.quote": 4,
    "news.sonar": 1
  },
  "external_costs": {
    "perplexity_sonar_usd": "0.0010",
    "finnhub_usd": "0.0000"
  },
  "total_usd": "0.0184"
}
```

**Used by:** dashboard cost page, monthly cap enforcement.

---

## 8. Hypothesis Registry Entry

**Path:** `RESEARCH/hypotheses/H_NNN.md`

```markdown
---
hypothesis_id: H_005
title: Multi-agent debate produces lower max DD than single-agent baseline
status: open
opened: 2026-05-15
research_question: RQ6
falsification_criterion: |
  Side-by-side paper accounts: single-agent max DD ≤ multi-agent max DD
  AND single-agent Sharpe ≥ multi-agent Sharpe over ≥ 60 trading days.
related_decisions: []
related_lessons: []
re_check_date: 2026-08-15
---

[Long-form discussion]
```

---

## 9. System Audit Log

**Path:** `memory/audit/YYYY-MM-DD.jsonl`

Append-only, separate from the journal. Records every privileged action: kill-switch toggles, halt unfreezes, doctrine PR merges, manual config changes.

```json
{
  "schema_version": "1.0",
  "event_id": "aud_...",
  "timestamp": "2026-05-12T20:14:33Z",
  "actor": "aaron",
  "actor_method": "dashboard_session",
  "action": "kill_switch_toggle",
  "from_state": "off",
  "to_state": "on",
  "reason_provided": "Reviewing earnings-week behavior; pausing for manual review",
  "ip": "100.64.x.x"
}
```

**Used by:** governance review; quarterly retrospective.

---

## Schema Validation

A `schemas/` directory holds JSON Schema files for each schema above. The journal writer, calibration writer, and audit writer all validate against these before persisting. Invalid entries fail loudly to Discord rather than silently writing.

Schema migrations:
- Forward-compatible (add field, default null) — increment minor version, no migration needed
- Breaking — increment major version, write a one-shot migration script in `migrations/`, freeze old version, document in ADR
