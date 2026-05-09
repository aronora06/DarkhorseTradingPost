# News & research sources — trust tiers

**Purpose:** Reduce adversarial narrative risk (`plans/riskMitigation.md` §3 R10) while keeping research usable.

---

## 1. Tier A — primary (single-source OK for **facts**, not opinions)

Examples (non-exhaustive; maintain explicit allow-list in Phase 3 config):

- Company **investor relations** filings (10-Q / 10-K / 8-K via SEC EDGAR)
- Major exchange **listing notices**
- Tier-1 data vendors when surfaced through controlled tools (Finnhub / Alpaca fundamentals endpoints)

**Rule:** Factual claims about numbers (revenue, guidance ranges) should trace to Tier A when challenged.

---

## 2. Tier B — corroboration required for tradable thesis

Examples:

- Established financial newswires / newspapers with editorial standards
- Sell-side research summaries **only** when corroborated by Tier A metrics

**Rule:** Satellite **post-earnings playbook** minimum **two independent Tier B+ sources** OR **one Tier B + Tier A** filing confirmation (`satellite_sleeve.md`).

---

## 3. Tier C — sentiment / noise (never sole justification)

Examples:

- Social aggregators, forums, anonymous blogs

**Rule:** May inform **questions** for researcher agents — **cannot** alone justify an order.

---

## 4. Uncited model outputs

Internal LLM reasoning **does not count** as a source.

If tool output lacks citations (fallback scrape): downgrade to **Tier C treatment**.

---

## 5. Unicode / normalization

All headlines & bodies normalized (**NFKC**) before entering prompts (`plans/riskMitigation.md` §3 R10).

---

## Cross-links

- `RESEARCH/adversarial_vectors.md` NEWS rows  
- `doctrine/style_guide.md` citation fields in journal JSON
