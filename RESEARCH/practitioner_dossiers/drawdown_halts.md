# Dossier: Drawdown halts & risk-of-ruin framing

**Compiled:** 2026-05-09  
**Refresh by:** 2027-05-09

## Question

What do disciplined practitioners recommend for **when to stop trading** (daily vs peak-to-trough), and how do those recommendations map to a **~$1k** equities sleeve whose failure mode is behavioral + model error, not leverage?

## Sources consulted

Summarized themes (not verbatim trading advice). Primary editions vary; refresh updates numbers if authors publish revisions.

| Practitioner / outlet | Representative work | Theme relevant here |
|---|---|---|
| **Van Kaufman** | *Trading Systems and Methods* | Statistical validity vs curve-fit; stress regimes matter more than peak equity |
| **Van Tharp** | *Trade Your Way to Financial Freedom* | **R-multiples**, expectancy, position sizing as % of equity; importance of hard stops on *process* runaway |
| **Andreas Clenow** | *Stocks on the Move*, trend following equity curves | Slow strategies hit deep DDs as a feature; **risk overlays** and turnover discipline |
| **Robot Wealth** (blog / courses) | Trend / systematic retail framing | Practical risk caps, avoiding “hero mode” after losses |

## Where they agree

- **Separate “bad day” from “bad regime.”** Fast brakes on single-day damage catch bugs, connectivity gaps, and emotional/agentic spirals. Slower brakes on peak-to-trough catch structural decay.
- **Survival beats brilliance.** Position sizing and halt rules exist so the account (and the operator) can continue learning after a rough patch.
- **Rules must be defined before pain.** Discretionary overrides after losses correlate with worse outcomes; halts force a pause and review.

## Where they disagree

- **Fixed % vs volatility targeting.** Trend followers often tolerate deeper equity DDs when volatility is elevated *by design*; mean-reversion shops often want tighter peak-to-trough caps.
- **Pause vs de-risk.** Some frameworks reduce size after adverse moves; others halt flat until human review.
- **Recovery semantics.** Whether peak resets after a withdrawal, new capital, or strategy change (Darkhorse locks **HWM semantics** in doctrine — see `doctrine/risk_policy.md`).

## Implication for Darkhorse

Aligned with `plans/initialPlan.md` §8.2:

| Mechanism | Core | Satellite | Practitioner alignment |
|---|---|---|---|
| Daily loss kill | −2% of sleeve NAV | −10% of sleeve NAV | Tharp-style “stop the bleeding today”; tighter Core reflects mandate stability |
| Drawdown halt from HWM | −15% | **None** | Core: institutional-grade pause below SPY-scale trauma; Satellite: explicit risk capital |
| Uncle point | −25% | −80% | “Stop trusting the machine” tripwire; broader than a tactical halt |

**Adopt:** layered brakes (daily / DD / uncle), **no HWM reset after halt** (prevents oscillating unfreeze loops — consistent with practitioner emphasis on pre-commitment).

**Do not blindly adopt:** practitioner suggestions tuned to **leveraged futures/FX** portfolios (different ruin math) or accounts large enough to diversify across dozens of uncorrelated sleeves.

## Caveats

- None of the sources above validates LLM-specific failure modes (hallucination cascades, tool abuse). Those are handled by **code walls** (`validate_order`) and adversarial tests — see `RESEARCH/adversarial_vectors.md`.
- If Core mandate shifts toward higher-turnover tactics, revisit whether −15% DD halt remains appropriate vs turnover capacity.

## Cross-links

- Codified limits: `doctrine/risk_policy.md`
- Steering rationale: `plans/initialPlan.md` §8.2, `plans/riskMitigation.md` §3 R9
