# RESEARCH/papers/

One-page summaries of source papers we've read. The point is not to reproduce the paper — it is to have, in our own words, what the paper claims, what evidence it offers, and what we are taking from it for Darkhorse.

## Conventions

- **One file per paper.** Filename is `YYYY-firstauthor-keyword.md` (e.g. `2026-finsaber-look-ahead.md`).
- **Cite the paper at the top.** Title, authors, venue, year, link to arXiv or DOI.
- **Length: one page.** If a paper deserves more than a page, write a separate deep-dive note in `RESEARCH/architecture/` and link to it.

## Required sections

```markdown
# <paper title>

**Authors:** ...
**Venue:** ...
**Year:** ...
**Link:** ...
**Read on:** YYYY-MM-DD

## Claim
One paragraph: what does the paper assert?

## Evidence
One paragraph: what data / experiments support the claim? How robust?

## What we take from it
Bullets: specifically how this informs Darkhorse — doctrine, prompts, architecture, anti-patterns, or tests. Each bullet should map to a file or test we plan to write.

## What we don't take from it
Bullets: where the paper's conclusions don't apply to our setting (different scale, different model, different mandate).

## Open questions
Bullets: things we'd want to test if we had the data.
```

## Phase 1 reading list (initial)

Per `../../plans/devPhaseChecklist.md` §1.1, read at least 2 source papers per major risk:

- **Look-ahead bias** — FINSABER (KDD 2026)
- **Perturbation cascades** — TradeTrap
- **Strategic deception** — Apollo Research deception studies
- **Adversarial inputs** — Unicode homoglyph attacks on financial NLP
- **Memory architecture** — FinMem

Add to this list as new relevant work appears in the monthly competitive-landscape reviews.
