# Tradable universe

**References:** `plans/initialPlan.md` §8.1, `plans/riskMitigation.md` §3 R4

Universe definitions are **inputs** to screening jobs (Phase 3); this file states policy **intent**.

---

## 1. Core universe

**Base list:** S&P 500 constituents as of weekly refresh snapshot.

**Hard filters (reject if fail):**

| Filter | Threshold | Rationale |
|---|---|---|
| Price | Close ≥ **$10** | Penny-stock spread/noise avoidance |
| Liquidity | 20-day ADV dollar ≥ **$25M** | Slippage control at micro size |
| Sector cap | ≤ **25%** of Core NAV in any **GICS sector** | Hidden concentration guard |
| Leveraged/inverse ETFs | Excluded | Structural mismatch vs mandate |
| Pending M&A | Exclude if **deal spread < 2%** | Arb / breakage traps |
| Earnings window | Exclude if earnings ≤ **2 trading days** | Event lottery avoidance |

**Refresh cadence:** weekly Sunday pre-market full filter pass; **monthly** full reconstitution reconciliation vs provider list.

---

## 2. Satellite universe

**Base list:** Core-eligible names **plus** extension symbols listed in `satellite_watchlist.md` (≤ **25** extensions).

**Hard filters:**

| Filter | Threshold |
|---|---|
| Price | Close ≥ **$5** |
| Liquidity | 20-day ADV dollar ≥ **$5M** |
| Asset class | Common equity only v1 (no options/etc.) |

Extensions **must** carry maintained thesis paragraphs in `satellite_watchlist.md`. Agent challenges monthly; Aaron owns final inclusion.

---

## 3. Corporate actions & staleness

If symbol changes ticker, merges, or halts: screening pipeline removes from tradable set until reconciled.

**Fail-closed:** if screening data missing at decision time → **NO_TRADE** for dependent intents.

---

## Cross-links

- `doctrine/satellite_watchlist.md`  
- `RESEARCH/adversarial_vectors.md` §Symbol integrity  
- `tests/specs/validate_order.md`
