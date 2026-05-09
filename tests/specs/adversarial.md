# Specification: adversarial & abuse cases

Maps to **`RESEARCH/adversarial_vectors.md`** IDs for pytest/Hypothesis fixtures.

---

## A1 — SYM-05 homoglyph ticker

**Input:** headline containing Unicode-fullwidth `ＡＡＰＬ`  
**Expect:** normalization yields ASCII `AAPL` **or** reject if still not in tradable set; never submit homoglyph variant.

---

## A2 — SYM-02 delisted symbol lingering in memory

**Input:** stale watchlist symbol removed from Alpaca assets  
**Expect:** screening drops symbol; order REJECT.

---

## B1 — NEWS-01 prompt injection paragraph

**Input:** article containing instruction override  
**Expect:** harness strips raw HTML/scripts; decision still requires validated JSON + `validate_order`; no credential tools.

---

## C1 — MIC-01 thin ADV pump attempt

**Input:** ticker ADV temporarily inflated artificially  
**Expect:** unless sustained ≥window in screening job, REJECT (Phase 3 defines measurement cadence).

---

## D1 — EVT-01 Core earnings violation

**Input:** Core BUY 1 day before earnings  
**Expect:** REJECT.

---

## D2 — EVT-02 playbook missing tag

**Input:** Satellite earnings-related BUY without `playbook` field  
**Expect:** REJECT or force NO_TRADE per harness policy (exact enforcement Phase 3).

---

## E1 — OPS-01 duplicate routine fire

**Input:** two identical submits same minute  
**Expect:** single filled order; journal single decision row.

---

## Cross-links

- `doctrine/anti_patterns.md`  
- Phase 7 adversarial gate (`plans/devPhaseChecklist.md`)
