# Dossier: Position sizing psychology & PDT mechanics (micro-account)

**Compiled:** 2026-05-09  
**Refresh by:** 2027-05-09

## Question

How should **position sizing discipline** and **Pattern Day Trader (PDT)** constraints shape agent behavior for a **sub-$25k** US equities account running multiple routines per day?

## Sources consulted

- FINRA / SEC rule summaries on **PDT** (pattern day trader definitions, margin account implications)
- Broker documentation (e.g., Alpaca) on **day trade counting** and restrictions on cash vs margin accounts
- Practitioner risk texts (**Tharp**, **Kaufman**) on fixed fractional sizing vs volatility-adjusted sizing at small scale

## Where they agree

- **Sizing rules belong in code**, not in moment-to-moment discretion — especially when multiple automated routines could otherwise amplify churn.
- **PDT is not “soft guidance.”** At sub-$25k, exceeding allowed day trades triggers forced waits or account flags; an agent that ignores this can lock the account during volatility.
- **Buffer below the legal limit.** Practitioner operational hygiene mirrors engineering margin-of-safety: stop before the cliff edge.

## Where they disagree

- **Vol targeting vs static caps.** Quants scale exposure to volatility; simple retail systems often use fixed % caps. Darkhorse uses **fixed NAV-derived caps** first (clarity + auditability); can revisit vol scaling in later phases.

## Implication for Darkhorse

- `validate_order` tracks **`daytrade_count`** (or equivalent) and enforces **no day trades** on sub-$25k accounts, with buffer at **2 trades / 5 rolling days** (steering: one below regulatory 3) — see `doctrine/risk_policy.md`.
- **Trades per day per sleeve** capped (`plans/riskMitigation.md` §5) to reduce runaway churn.
- Satellite may hold concentrated risk **within sleeve NAV**, but cannot circumvent account-level regulatory walls.

## Caveats

- Exact Alpaca field semantics can change; Phase 3 implementation must confirm API fields against live/paper responses and encode **fail-closed** behavior if ambiguous.

## Cross-links

- `doctrine/core_sleeve.md`, `doctrine/satellite_sleeve.md`, `tests/specs/sizing.md`, `tests/specs/validate_order.md`
