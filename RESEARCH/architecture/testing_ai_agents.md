# Testing AI Agents — 2026 Practice

**Compiled:** 2026-05-09
**Refresh by:** 2026-11-09
**Linked ADRs:** ADR-0009 (testing strategy)

## Summary

Testing LLM-driven systems in 2026 is a tractable problem if you draw the line cleanly between the deterministic surface (which gets unit-tested traditionally) and the non-deterministic LLM surface (which gets contract-tested with deterministic assertions plus snapshot regression tests, and human-evaluated periodically).

For Darkhorse, the deterministic surface is **most of the system** — `validate_order`, sizing, drawdown, kill_switch, idempotency, journal writes, calibration math. The LLM surface is the harness output: a JSON decision struct that must pass `validate_order`. We test the LLM surface by asserting properties of its output, not by trying to assert the model's reasoning.

We deliberately do **not** call live LLMs in CI. Cost, flakiness, and non-determinism make that a poor test design.

## Sources reviewed

- assertllm.dev — pytest-based LLM assertion framework (22+ deterministic assertions, zero LLM calls for most)
- agentpytest (PyPI) — pytest plugin recording agent trajectories as JSON cassettes, statistical regression detection
- agenttest-py (PyPI) — eval-driven testing with built-in judge scorers
- pytest-assay — for Pydantic AI agents specifically
- tool-scorer — tool-call accuracy regression testing
- Anthropic's published evaluation guidance (cookbook, evaluation patterns)
- Apollo Research evaluation methodology (deception evals, pressure tests)

## Key findings

### 1. The deterministic surface gets traditional tests

Most failure modes in a trading agent are not "the LLM said something wrong" — they're "the validator let through a position cap violation," or "the kill-switch didn't fire," or "the idempotency key collided." These are **deterministic Python bugs**, and they get traditional pytest unit tests with full coverage.

For Darkhorse, the deterministic surface that needs ≥95% coverage:
- `validate_order` (every rule, including refusal under valid inputs)
- `sizing` (per-sleeve sizing math)
- `drawdown` (HWM tracking, halt firing, recovery without HWM reset)
- `kill_switch` (file flag, env var, remote endpoint priority)
- `idempotency` (deterministic client_order_id derivation, no collisions)
- `journal` (append-only writes, schema validation, daily rotation)
- `wind_down` (riskMitigation §6 conversion logic)

### 2. Property-based testing for the risk wall

`Hypothesis` is the right tool for `validate_order`. Generate adversarial inputs (Unicode homoglyph tickers, zero-quantity orders, negative prices, off-list tickers, day-trade attempts on PDT-restricted accounts) and assert the validator rejects them all.

This catches the "valid input space" mistakes that example-based tests miss. It's the cheapest way to push validate_order toward provable correctness short of formal methods.

### 3. The LLM surface is contract-tested, not behavior-tested

We do not assert "the agent recommended BUY for AAPL on this date." We assert:

- **Schema:** the decision JSON matches the `Decision` pydantic model.
- **Validity:** `validate_order(decision)` passes (or, for NO_TRADE, the validator agrees there's nothing to validate).
- **Bounds:** confidence ∈ [0, 1], horizon ∈ {1..30 days}, qty ≥ 0, etc.
- **Reasoning trace presence:** required fields are populated and non-empty.
- **Cost:** cached_input_tokens > 0 after the first routine in a session (cache is working).

These assertions are deterministic and cheap. They catch ~80% of regressions without calling an LLM.

### 4. Snapshot / cassette testing for harness behavior

For the harness orchestration logic itself (sequencing, error envelopes, retries, telemetry), record cassettes of past LLM responses and replay them in CI. This is what `agentpytest` and `pytest-assay` do.

Pattern:
- Live run produces a cassette (request → response pair, sanitized of secrets).
- Cassette is committed to the repo under `tests/cassettes/`.
- CI replays cassettes through the harness, asserts side effects (journal entries, validate_order calls, retry behavior).

The LLM is mocked out via cassette playback; the harness logic is exercised end-to-end. Updates to cassettes are deliberate and reviewed.

### 5. Adversarial test suite (Phase 1 / Phase 7)

`riskMitigation.md` §3 R10 calls for weekly adversarial tests. Implement as deterministic fixtures:

- Unicode homoglyph tickers (Cyrillic А vs Latin A in "AAPL")
- Fabricated headlines with hidden-text injection
- Stale quotes / time-skewed data
- Bad tool returns (missing fields, wrong types, large payloads)
- Earnings-soon names on the no-fly list

The harness processes these inputs; the test asserts the resulting orders fail `validate_order` or that the agent emits NO_TRADE. **The pass criterion is that nothing bad happens** — not that the LLM identifies the attack. The LLM may be fooled; the validator must not be.

### 6. Live LLM evaluation is periodic, manual, and out of CI

Aaron's weekly journal review (the `learningSystem.md` §1 calibration analysis and §6 reasoning audits) is the human-eval layer. Quarterly Haiku-driven reasoning audits provide a programmatic complement, but those run on real journal data, not in CI.

Per-PR live LLM smoke tests are tempting but expensive ($0.10–$0.50 per PR adds up at any meaningful PR cadence). Skip; rely on paper-shadow validation windows for behavioral regression detection (the `initialPlan.md` cross-cutting rule: "No new prompt change lands without a paper-shadow observation period of ≥ 2 weeks").

### 7. Tool-call accuracy specifically

`tool-scorer` and similar frameworks evaluate whether the model picks the right tool with the right arguments. For Darkhorse this matters most for:

- Did the agent call `data.quote` before deciding? (Required by doctrine.)
- Did the agent call `news.sonar` with reasonable query terms?
- Did the agent emit the order via `alpaca.submit_order` rather than fabricating a fill?

These are testable as harness invariants — assert the tool-call sequence in cassette tests.

## Implications for Darkhorse

Three-layer test strategy:

| Layer | Tool | What it tests | Run frequency |
|---|---|---|---|
| **Unit (deterministic)** | pytest + pytest-cov | All Python except LLM calls. ≥95% coverage on `src/risk/`. | Every commit, every PR. |
| **Property (deterministic)** | Hypothesis | Adversarial input space against `validate_order`. | Every commit. |
| **Cassette (replayed LLM)** | pytest + custom cassette layer (lightweight, in-repo) | Harness orchestration: sequencing, retries, error envelopes, side effects. | Every commit. |
| **Manual eval** | Aaron + weekly review routine | Reasoning quality, doctrine fidelity. | Weekly. |
| **Adversarial** | dedicated fixtures | Unicode, prompt injection, stale data. | Weekly in production; on every harness PR in CI. |

CI behavior:
- On PR: ruff, mypy --strict, pytest (unit + property + cassette), coverage report.
- No live LLM calls.
- No live broker calls (Alpaca paper sandbox is dev-machine only).
- CI runs in <2 minutes for the v1 surface.

External tool selection:
- **assertllm** — adopt for the deterministic-assertion library. Lightweight, no provider lock-in.
- **agentpytest or custom** — record cassettes. Likely custom (a few hundred lines of Python) because the cassette format is simple and we want full control.
- **tool-scorer** — defer; evaluate after harness is built and we know what tool-call patterns to assert.

## Open questions

- **Cassette format.** JSON files with request hash → response, or pickle? JSON is reviewable in PRs.
- **How often to refresh cassettes?** Tied to prompt changes. If a prompt changes, the cassette likely needs re-recording. Make it a one-line CLI command.
- **Statistical regression on win-rate.** `agentpytest` supports bootstrap / paired-permutation tests on outcomes across cassette runs. Worth exploring once we have ≥30 cassettes.

## What we deliberately don't do

- **LLM-as-judge in CI.** Adds non-determinism and cost. Save this for the quarterly reasoning audit which is meant to be qualitative.
- **End-to-end live trading tests in CI.** The live system is itself the integration test, with the validator as the safety net. Phase 4's "5 trading days minimum" plays this role.
- **Mocking the model with hand-crafted responses.** Cassettes from real runs are higher-fidelity and require less imagination.

## Reading list

- assertllm full docs (saved during research session)
- agentpytest docs and example projects
- Anthropic evaluation cookbook (Phase 2 read)
- Apollo Research deception eval methodology (relevant for adversarial layer)
