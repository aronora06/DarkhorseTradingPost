# ADR-0009: Testing Strategy

## Status

`accepted` (2026-05-09)

## Context

Testing an LLM-driven trading system has three distinct surfaces:

1. **Deterministic Python** — `validate_order`, sizing, drawdown, kill_switch, idempotency, journal, calibration math. Most of the system. Traditional unit tests apply.
2. **Harness orchestration** — multi-agent debate flow, retries, error handling, cost telemetry. Logic exists, but inputs include LLM responses (non-deterministic).
3. **LLM behavior itself** — does the agent reason well, follow doctrine, avoid anti-patterns? Inherently non-deterministic; expensive to evaluate at scale; primary feedback channel is human review of journal entries.

Traditional CI testing for layers 1 and 2 is straightforward. Layer 3 requires a different evaluation strategy that is intentionally outside CI.

## Decision

**Three-layer test strategy, plus periodic manual evaluation:**

| Layer | Tool | What it tests | When |
|---|---|---|---|
| **Unit (deterministic)** | pytest + pytest-cov | All Python except LLM calls. ≥95% coverage on `src/darkhorse/risk/`. | Every commit, every PR. |
| **Property (deterministic)** | Hypothesis | Adversarial input space against `validate_order` rules. | Every commit. |
| **Cassette (replayed LLM)** | pytest + custom cassette layer | Harness orchestration: sequencing, retries, error envelopes, side effects. LLM is mocked via recorded I/O cassettes. | Every commit. |
| **Adversarial fixtures** | pytest with curated bad inputs | Unicode homoglyphs, prompt injection in news content, stale quotes, malformed tool returns. | Every harness PR; weekly in production. |
| **Manual evaluation** | Aaron + weekly review routine | Reasoning quality, doctrine fidelity. | Weekly + quarterly reasoning audit. |
| **Paper-shadow validation window** | Live paper account, ≥ 2 weeks | Behavioral regression detection on architectural changes. | Per cross-cutting rule in `../devPhaseChecklist.md`. |

Phase 3 note: cassette tests begin when `src/darkhorse/harness.py` introduces the first LLM orchestration surface. Until then, CI covers deterministic Python only; no placeholder cassette harness is required before there is a harness to replay.

**CI rules:**
- Run on PR + on push to main.
- ruff, mypy --strict, pytest (unit + property + cassette), coverage report.
- **No live LLM calls.** No live broker calls.
- CI runs in <2 minutes target.

**What we deliberately don't test in CI:**
- Live LLM behavior (cost, flakiness, non-determinism — paper-shadow window catches behavioral regression instead).
- Live Alpaca calls (broker paper sandbox is for dev-machine integration testing only).
- LLM-as-judge evaluations (reserved for the quarterly reasoning audit).

## Consequences

### Positive

- Fast CI (<2 min). PR feedback is responsive.
- Cheap CI (no live LLM calls). PR cost is essentially zero.
- High confidence on the safety surface (`validate_order`). 100% adversarial coverage via Hypothesis.
- Regression detection on the harness (cassette tests catch silent breakage of orchestration logic).
- Behavioral regression on the LLM caught by the paper-shadow window — slow but real.

### Negative / costs

- LLM behavior changes (model swaps, prompt revisions) only surface in paper-shadow at the 2+ week mark. We accept this; the alternative (LLM tests in CI) is non-deterministic and expensive.
- Cassette tests can drift from reality. When prompts change, cassettes must be re-recorded. We make this a one-line CLI command and a deliberate PR step.
- Property-based tests on `validate_order` can find pathological-but-irrelevant edge cases. Mitigation: hypothesis strategies are intentional and reflect real input distributions.

### Neutral

- The strategy splits "deterministic" from "non-deterministic" cleanly. We accept that the LLM is a black box for testing purposes, and we test around it (input validation, output validation, side-effect assertions).

## Tooling specifics

**Hypothesis strategies for `validate_order`:**

```python
from hypothesis import given, strategies as st
from darkhorse.risk.validate_order import validate_order

@given(
    ticker=st.text(min_size=1, max_size=10),
    qty=st.integers(min_value=-1_000_000, max_value=1_000_000),
    limit_price=st.decimals(min_value=-1000, max_value=1_000_000, places=2),
    sleeve=st.sampled_from(["core", "satellite", "neither"]),
)
def test_validate_order_never_passes_invalid(ticker, qty, limit_price, sleeve):
    order = build_order(ticker, qty, limit_price, sleeve)
    if not is_valid(order):
        assert validate_order(order).rejected
```

**Cassette format:**
- JSON files at `tests/cassettes/<test_name>.json`
- Each cassette is a list of (request_hash, response_dict) pairs
- Replay layer matches request hash; if no match, fail the test (no live LLM call)
- Re-record CLI: `uv run python -m darkhorse.testing.record <test_name>`

**Adopted external tools:**
- **assertllm** — for the deterministic-assertion library it provides for LLM outputs (substring, regex, JSON validity, cost, latency checks). Use as a complement to pytest, not a replacement.
- **agentpytest** or custom cassette layer — start custom (≤200 lines); switch to agentpytest if our needs match its abstractions.
- **tool-scorer** — defer; evaluate after harness is built and we know what tool-call patterns to assert.

## Alternatives considered

- **Live LLM smoke tests on PR.** Tempting for "did we break the prompt." Rejected: per-PR cost ($0.10–$0.50), flakiness (non-determinism), and slow feedback. The 2-week paper-shadow window is the proper place for behavioral validation.
- **LLM-as-judge evaluations in CI.** Same rejection reasons plus the model-judge double-jeopardy (we'd be testing one Claude with another Claude on the same training distribution). Reserved for quarterly reasoning audits where it's appropriate.
- **End-to-end live Alpaca tests.** Paper sandbox is fine for local development. Not in CI — not deterministic, requires keys, slows the feedback loop.
- **Snapshot testing with text-diff.** Considered for prompt outputs. Rejected because LLM output isn't byte-stable; cassette-replay is the correct shape (semantic equivalence at the harness side-effect layer, not text equality).
- **No CI tests; rely on paper-shadow.** Strawman; paper-shadow catches behavioral regression but not orchestration bugs (e.g., "harness crashes on tool error"). Both layers are needed.

## Falsification criterion

This testing strategy is wrong if:

- A class of bugs reaches production that the test layers should have caught (e.g., a `validate_order` bypass that Hypothesis didn't generate, a harness orchestration bug not covered by cassettes).
- CI test time exceeds 5 minutes — slows PR cadence enough that engineers (Aaron) skip running tests locally.
- Cassette drift becomes >1 hour of work per major prompt change — indicates the cassette layer needs better tooling.
- Coverage on `src/darkhorse/risk/` falls below 95%.

## Linked hypotheses

None. Testing strategy is foundational infrastructure.

## Re-check date

2026-11-09 (6 months) — re-evaluate after Phase 4–5 produces the first ~3 months of test-layer experience.

## References

- `../../RESEARCH/architecture/testing_ai_agents.md` (research note that informed this decision)
- `../devPhaseChecklist.md` Phase 1.3 (test specs) and Phase 7 (adversarial gate)
- `../riskMitigation.md` §3 R10 (adversarial test suite)
- assertllm.dev, agentpytest, tool-scorer (PyPI)
