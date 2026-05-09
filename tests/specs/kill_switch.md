# Specification: kill-switch & human pause

**Modules (future):** `src/darkhorse/risk/kill_switch.py`, harness preamble

---

## KS-01 — File flag

| State | Expect |
|---|---|
| `KILLSWITCH` present at repo root (Phase 3 defines exact format) | Immediate abort — no LLM, no orders |
| Flag absent | Continue to env check |

---

## KS-02 — Environment flag

| State | Expect |
|---|---|
| `DARKHORSE_KILL=1` | Abort |
| Normal | Continue |

---

## KS-03 — Auto-pause (governance)

Per `plans/riskMitigation.md` §3 R16: if **14 days** without doctrine/journal human activity signal → trading paused pending acknowledgement.

| Example | Expect |
|---|---|
| Stale review timer fired | OPEN_ROUTINES_RETURN_PAUSED |

(Exact mechanism Phase 3.)

---

## KS-04 — Provider spend caps

Anthropic monthly cap breach surfaces as **hard abort** pre-call (`plans/riskMitigation.md` §5).

---

## Cross-links

- `doctrine/risk_policy.md` §7  
- `tests/specs/validate_order.md` (interaction when paused)
