# Dossier: Universe selection & execution constraints at small account size

**Compiled:** 2026-05-09  
**Refresh by:** 2027-05-09

## Question

For **$1k–$5k** retail equity accounts, what does practitioner/systematic literature emphasize about **universe breadth**, **liquidity**, **spreads**, and **regulatory constraints** (especially PDT under $25k)? How does that support Darkhorse’s Core vs Satellite split?

## Sources consulted

| Source type | Examples | Relevant takeaway |
|---|---|---|
| Systematic equity practitioners | Clenow (*Stocks on the Move*), quantitative equity blogs | Liquidity & investability dominate micro-account viability |
| Risk / process authors | Tharp (position sizing, ruin avoidance) | Fewer, cleaner names beat “coverage” when costs are large vs edge |
| Regulatory / broker education | FINRA PDT rule summaries; Alpaca/Broker PDT docs | Sub-$25k: day-trade count is a hard optimization constraint |
| Retail quant educators | Robot Wealth, systematic investing primers | Keep turnover and complexity low until edge is measurable |

## Where they agree

- **Costs are non-linearly painful small.** Spread + slippage as a fraction of expected edge rises as account size falls; “trade everything” is irrational.
- **Liquidity floors matter more than ticker count.** ADV and price floors are crude but robust filters for tradability.
- **Concentration is inevitable at $1k** if you hold more than token diversification — so **mandate clarity** (Core vs risk sleeve) matters more than pretending to run 50 positions.
- **PDT is a first-class design constraint** for US equities cash accounts under $25k: strategies that require frequent round-trips within T+1 conflict with survival.

## Where they disagree

- **Breadth vs conviction.** Some argue a concentrated high-conviction book; others argue minimum N for idiosyncratic noise damping. At $1k, **N is naturally small**; the debate resolves to **liquidity + thesis quality**.
- **Extended universe (mid/small cap).** Practitioners chasing factor exposure may dip below large-cap liquidity; Darkhorse **defers** that unless/until data + cost model justify it (`plans/initialPlan.md` §8.1).

## Implication for Darkhorse

Codified in `doctrine/universe.md`:

| Topic | Darkhorse choice | Practitioner support |
|---|---|---|
| Core universe | S&P 500 + liquidity/price/M&A/earnings filters | Large-cap liquidity consensus |
| Satellite universe | Core universe **plus** ≤25-name extension (Aaron-curated) | Controlled breadth expansion without Russell 1000 token bloat |
| PDT | Code-enforced; buffered below regulatory threshold | Broker/regulatory reality |
| Round-trip friction | Limit orders default; caps on trades/day | Cost-aware micro-account practice |

**Explicit non-goals at this scale:** hunting illiquid story stocks, extended FX/options complexity, or “many small lottery tickets” without explicit Satellite thesis.

## Caveats

- Fidelity visibility via SnapTrade does **not** change Alpaca execution constraints — sizing must remain consistent with **Alpaca account** rules and buying power.
- If Alpaca upgrades data feeds or account type changes (unlikely at $1k), revisit intraday strategies — still subservient to PDT guardrails.

## Cross-links

- Filters & cadence: `doctrine/universe.md`
- Order wall & PDT detail: `tests/specs/validate_order.md` (planned examples), future `src/darkhorse/risk/validate_order.py`
- Steering: `plans/initialPlan.md` §8.1, `plans/riskMitigation.md` §3 R4/R7
