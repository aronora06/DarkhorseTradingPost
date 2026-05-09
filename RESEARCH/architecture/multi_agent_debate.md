# Multi-agent debate patterns — TradingAgents vs Darkhorse

**Last updated:** 2026-05-09  
**Companion paper summary:** `../papers/2024-xiao-tradingagents.md`

## TradingAgents (published framework)

- Rich division of labor: **four analyst personas**, bull/bear researchers, trader, risk team, fund manager.
- Emphasizes **structured + NL hybrid** messaging to reduce garbled state across long chains.
- Claims improved risk-adjusted metrics vs simpler LLM traders on historical simulations.

## Darkhorse v1 harness (ADR-0008)

- **Minimal graph:** researcher → parallel bull/bear → Opus risk-manager → `validate_order` wall → broker tool.
- **Cost-aware tiering:** Sonnet subagents, Opus final judge, Haiku journaling (`plans/decisions/0002-tiered-model-strategy.md`).
- **Execution isolation:** no fund-manager role with unrestricted authority — human + kill-switch + Git governance.

## Design delta rationale

| Dimension | TradingAgents | Darkhorse choice |
|---|---|---|
| Role count | Many | Few — operational simplicity & token budget |
| Risk enforcement | Agents + structure | **Python modules trump prompts** |
| Data surfaces | Broad toolkits | Curated tools per ADR-0001 |
| Evaluation promise | Backtest uplift | Treat as hypothesis; live gated ramp |

## Failure-mode implication

More agents ⇒ more **coordination attack surface** (prompt injection hopping roles). Darkhorse mitigates via **short DAG**, structured outputs, ticker normalization, and adversarial catalog (`RESEARCH/adversarial_vectors.md`).

## Action items (future)

- Revisit role expansion **only** after stable calibration metrics (`plans/devPhaseChecklist.md` Phase 6).
- If debate transcripts show information loss, adopt additional **structured handoffs** (not more prose rounds).
