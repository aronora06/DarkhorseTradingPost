# Anti-pattern catalog (seed)

Living document — extend as weekly reviews surface failures. Mirrors high-level entries in `RESEARCH/adversarial_vectors.md`.

| ID | Anti-pattern | Why it fails | Detection / mitigation |
|---|---|---|---|
| AP-01 | **Trading off a headline without Tier A/B corroboration** | LLM recency bias + fabrication risk | `news_sources.md`; bear analyst argument |
| AP-02 | **Round-tripping intraday under PDT limits** | Regulatory freeze | Buffered day-trade counter |
| AP-03 | **Chasing illiquid gaps** | Slippage eats edge | ADV + limit-only defaults |
| AP-04 | **Prompt-engineering around sizing** | Violates constitution | `validate_order` notional caps |
| AP-05 | **Ignoring earnings window for Core** | Event lottery | Calendar filter |
| AP-06 | **Satellite earnings gamble without playbook tags** | Inconsistent agent behavior | Journal enforcement |
| AP-07 | **Duplicate fire trades** | Retry amplification | Deterministic client order ids |
| AP-08 | **Confidence inflation on thin data** | Calibration drift | Confidence gate + weekly calibration |

Promotion to doctrine requires slow path (`plans/suggestedNextSteps.md` §1.1); anti-patterns here are **immediate caution flags**, not promoted lessons.

---

## Cross-links

- `plans/riskMitigation.md` risk catalogue  
- `RESEARCH/adversarial_vectors.md`
