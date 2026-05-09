# Adversarial input vectors (catalog)

**Maintained:** Phase 1 risk codification  
**Last updated:** 2026-05-09  
**Consumes:** `plans/riskMitigation.md` R5, R10, R16; `doctrine/risk_policy.md`; future `src/darkhorse/risk/validate_order.py`

This catalog lists **inputs or states that could trick the agent or bypass intent**. For each vector: **detection**, **`validate_order` action**, **harness / tool action**, **test hook** (Phase 7 adversarial gate expands coverage).

Design principle: **default NO_TRADE** when classification is uncertain.

---

## Legend

| Column | Meaning |
|---|---|
| **VO** | `validate_order.py` (hard reject / resize / delay) |
| **HN** | Harness: prompt construction, tool policy, refusal to act |
| **TS** | Test spec / cassette / property test |

---

## 1. Symbol & instrument integrity

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| SYM-01 | Hallucinated ticker | `ZZTOP` not in Alpaca tradables | Reject | Structured output schema + ticker normalization pass | `tests/specs/adversarial.md` A1 |
| SYM-02 | Delisted / untradeable | Merger cash-out pending | Reject | Refresh universe snapshot before open | A2 |
| SYM-03 | Halted symbol | LULD halt mid-day | Reject / defer | Quote tool surfaces halt flag → NO_TRADE | A3 |
| SYM-04 | Wrong exchange / OTCADR confusion | Pink-sheet ticker disguised as equity | Reject allow-list | Universe excludes OTC by construction | A4 |
| SYM-05 | Unicode homoglyph ticker | `ＡＡＰＬ` vs `AAPL` in headline | Reject | NFKC normalization before prompt (`riskMitigation` R10) | A5 |

## 2. News & narrative manipulation

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| NEWS-01 | Prompt injection in article body | `"Ignore prior instructions..."` | No bypass VO | Sandboxed news excerpts; cite-only discipline | B1 |
| NEWS-02 | Fabricated catalyst | Fake PR on low-credibility domain | Reject if thesis requires uncorroborated claim | Cross-source requirement in `doctrine/news_sources.md` | B2 |
| NEWS-03 | Time-zone / stale timestamp gaming | "Breaking" hours-old item | Rate-limit reaction | Clock & source latency metadata in digest | B3 |
| NEWS-04 | Sentiment spam / bot swarm | Coordinated micro-cap pump | Liquidity & ADV filters already exclude thin names | Satellite extension thesis required | B4 |

## 3. Market microstructure traps

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| MIC-01 | Low-float squeeze | Gap + halt cycle | ADV + price floors | No market orders except exceptional path | C1 |
| MIC-02 | Wide spread manipulation | Quote flickering | Slippage guards / limit-only default | Journal compares quote vs fill | C2 |
| MIC-03 | Opening auction chaos | 9:30–9:35 noise | Delay open routine (`riskMitigation` R6) | `market_open` @ 9:35 ET | C3 |
| MIC-04 | Options-expiration pin (equities) | Weird flows near OPEX | Not v1 options risk — still equities volatility | Awareness prompt section optional later | C4 |

## 4. Corporate events & calendar hazards

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| EVT-01 | Earnings surprise gap | Core exclusion window violation | Reject Core entries violating 2-day rule | Calendar tool + doctrine | D1 |
| EVT-02 | Satellite post-earnings drift misuse | Chasing without playbook | Size caps + playbook checklist | `doctrine/satellite_sleeve.md` §Post-earnings | D2 |
| EVT-03 | M&A arb residual | Deal collapse | Core excludes pending M&A per filters | Monitor spread thresholds | D3 |
| EVT-04 | Spin-off / ticker change | Wrong CUSIP lineage | Weekly universe refresh | Corporate action awareness | D4 |

## 5. Account & operations

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| OPS-01 | Duplicate order on retry | Routine fires twice | Deterministic `client_order_id` idempotency | Harness honors broker ack state | E1 (`idempotency.md`) |
| OPS-02 | Partial fill ambiguity | Unknown position | Reconcile positions endpoint before new risk | State machine in harness | E2 |
| OPS-03 | Buying power drift | Pending unsettled cash | Reject oversize | Include BP snapshot fields | E3 |
| OPS-04 | PDT proximity | 3rd day trade approaching | Hard reject approaching limit | Buffered rule at 2/5 | E4 |

## 6. Model behavioral hazards

| ID | Vector | Example | VO | HN | TS |
|---|---|---|---|---|---|
| LLM-01 | Strategic deception / hidden intent | Apollo-style pressure scenarios | Cannot fund / transfer | No privileged tools; journaling | Research note |
| LLM-02 | Confidence inflation | 0.95 on thin evidence | Confidence gates + calibration tracking | Minimum corroboration rules | F1 |
| LLM-03 | Tool-call spam | Runaway loops | Token / routine caps (`riskMitigation` §5) | Hard abort thresholds | F2 |

---

## Coverage tracking

| Artifact | Role |
|---|---|
| `doctrine/anti_patterns.md` | Human-readable mirror of recurring traps |
| `tests/specs/adversarial.md` | IDs ↔ concrete examples for pytest/Hypothesis |
| Phase 7 adversarial suite | Weekly synthetic headline injection (`riskMitigation` R10) |

## Cross-links

- `RESEARCH/practitioner_dossiers/` — outside-view grounding  
- `plans/riskMitigation.md` §3 R10, §7 open items (prompt injection via news)  
- [`RESEARCH/papers/2026-rizvani-adversarial-news-algorithmic-trading.md`](papers/2026-rizvani-adversarial-news-algorithmic-trading.md) — homoglyph / hidden-text headline threat quantification
