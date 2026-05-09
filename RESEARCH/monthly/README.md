# RESEARCH/monthly/

Monthly retrospectives. ~2 pages each. Audience: Aaron, plus future-Aaron, plus the year-1 publication when it's compiled.

The monthly is the lowest-friction retrospective cadence. It exists so the quarterly retrospective and the annual report don't have to compress 12 months of memory into one synthesis pass — instead they synthesize 12 monthlies and 4 quarterlies into a higher-level story.

See `../../plans/researchCharter.md` "Outputs → Research" for the cadence and what each level does differently.

## File format

`YYYY-MM.md`, one file per month, written within the first week of the following month.

```markdown
# Monthly Retrospective — YYYY-MM

**Compiled:** YYYY-MM-DD

## Calibration drift
- This month's calibration error per confidence bucket.
- Trend vs prior 3 months.
- Any bucket in alert (>10pp drift)?

## Costs
- Spend this month, by provider, vs cap.
- Cache hit rates per routine.
- Any tripwires fired?

## Lesson churn
- Proposed: N
- Merged: N (list with one-line each)
- Falsified: N
- Promoted to doctrine: N (rare; usually 0)

## Anti-pattern additions
- New entries in `doctrine/anti_patterns.md` this month.

## Competitive landscape digest
- One-paragraph digest of this month's competitive-landscape review.
- Anything we adopted? Anything we explicitly chose not to adopt?

## Notable trades
- 3–5 trades worth examining (winners, losers, anti-pattern instances). What did we learn?

## Live-vs-paper-shadow divergence
- Number of divergence days this month.
- Each divergence: explained or under investigation?

## Hypothesis updates
- Any hypothesis status changes this month? Evidence accumulated.

## Open question for next month
One specific thing worth attention next month — a calibration concern, a lesson worth watching, a competitive technique worth piloting.
```

## Discipline

- **Honest.** A month with no notable trades and zero lesson merges is a valid month and writes up in 30 minutes. Don't manufacture insight.
- **Don't rewrite history.** If a calibration trend reverses, write next month's retrospective noting the reversal — don't go back and edit prior months.
- **Anonymizable.** Express trades as percentages of sleeve NAV, not dollar amounts, so the file can be included in publication releases without retrofitting.
