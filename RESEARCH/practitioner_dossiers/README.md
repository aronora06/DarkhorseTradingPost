# RESEARCH/practitioner_dossiers/

Synthesized consensus from working practitioners on specific operational questions. Different from `papers/` — papers are academic; dossiers are practical knowledge from people who actually trade.

The point is to triangulate: when Kaufman, Tharp, Clenow, and Robot Wealth all converge on a number for drawdown halts, that's a stronger signal than any one of them alone. When they disagree, the disagreement itself is informative.

## Index (Phase 1)

| File | Topic |
|---|---|
| [`drawdown_halts.md`](drawdown_halts.md) | Daily loss vs peak-to-trough halts; uncle points |
| [`universe_small_account.md`](universe_small_account.md) | Liquidity, breadth, spread costs at ~$1k AUM |
| [`sizing_and_pdt.md`](sizing_and_pdt.md) | Position sizing discipline + PDT guardrails |

## When to write a dossier

When a doctrine decision needs an outside-view sanity check beyond a single source. Phase 1 established three focused dossiers (above); add more when a new operational question warrants the same treatment (e.g. options policy once v2 enables derivatives).

## File format

```markdown
# Dossier: <topic>

**Compiled:** YYYY-MM-DD
**Refresh by:** YYYY-MM-DD (default: 1 year out)

## Question
The specific operational question this dossier answers.

## Sources consulted
- Author / publication, year, link.
- (Aim for 4+ practitioners, not just academic papers.)

## Where they agree
The consensus, with quoted/paraphrased specifics from each source.

## Where they disagree
The dimensions on which practitioners differ, and what drives the difference (account size, asset class, strategy type).

## Implication for Darkhorse
The specific doctrine numbers / rules we adopt, and which sources support each.

## Caveats
- Where practitioner consensus may not transfer (different scale, different mandate, different decade).
- What we'd want to re-examine if a regime change occurs.
```

## Refresh discipline

Each dossier carries a "refresh by" date. At refresh, we re-read the most recent editions of the sources and update if any practitioner has materially changed their view. Refreshes are a quarterly task (one or two dossiers per quarter, rotating).
