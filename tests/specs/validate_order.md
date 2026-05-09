# Specification: `validate_order` behavior

**Module (future):** `src/darkhorse/risk/validate_order.py`  
**Doctrine inputs:** `doctrine/risk_policy.md`, `doctrine/universe.md`, sleeve docs

Each rule: **PASS** / **REJECT** / **DEFER** (NO_TRADE pending state).

---

## R-V01 — Sleeve & notional

| Example | Expect |
|---|---|
| Core BUY within ≤12% NAV entry, liquidity OK | PASS |
| Core BUY exceeding single-name cap | REJECT |
| Satellite BUY >50% Satellite NAV | REJECT |

---

## R-V02 — Universe & filters

| Example | Expect |
|---|---|
| SPY Core trade passing filters | PASS |
| OTC penny stock | REJECT |
| Core trade inside 2-day earnings window | REJECT |
| Satellite extension not on watchlist | REJECT |

---

## R-V03 — PDT buffer (<$25k accounts)

| Example | Expect |
|---|---|
| Swing trade, no day-trade conflict | PASS |
| Would create 3rd day trade in 5 days | REJECT |
| Ambiguous broker count | DEFER |

---

## R-V04 — Daily loss kill active

If sleeve flagged **daily_loss_halt_today**: any aggressive opening trade REJECT (flatten-only rules Phase 3 defines).

---

## R-V05 — Drawdown / uncle

Core halted after −15% DD: REJECT adds; allow risk-reducing sells per state machine (Phase 3).

Uncle triggered: REJECT all discretionary trades pending human reset.

---

## R-V06 — Order type & caps

| Example | Expect |
|---|---|
| Limit order default size | PASS |
| Market order without exception flag | REJECT |
| >3 trades/day in sleeve | REJECT |

---

## Cross-links

- `tests/specs/adversarial.md`  
- `RESEARCH/adversarial_vectors.md`
