# Specification: drawdown & high water mark

**Module (future):** `src/darkhorse/risk/drawdown.py`

---

## DD-01 — HWM tracking

- Persist sleeve equity peak **\(P\)**.
- Drawdown at time \(t\): **\((E_t - P) / P\)**.

HWM **does not reset** after tactical halt (`plans/initialPlan.md` §8.2).

---

## DD-02 — Core −15% halt

| Example | Expect |
|---|---|
| Equity −14.9% from HWM | Operational |
| Equity −15.0% from HWM | Enter `CORE_DD_HALT` — blocks risk-increasing orders |

---

## DD-03 — Core −25% uncle

Crossing −25% → `CORE_UNCLE` state → governance actions per `doctrine/risk_policy.md`.

---

## DD-04 — Satellite paths

Satellite **skips** −15% halt but respects −80% uncle and daily loss kill.

---

## DD-05 — Recovery without HWM reset

If equity recovers after halt, HWM remains historical peak — prevents oscillating unlock loophole.

---

## Cross-links

- `tests/specs/validate_order.md`  
- `RESEARCH/practitioner_dossiers/drawdown_halts.md`
