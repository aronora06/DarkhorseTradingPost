# Darkhorse Trading Outpost — Glossary

Vocabulary used in doctrine, prompts, code, and discussion. The point of this file is consistency — when "halt" appears in `risk_policy.md`, in a prompt, and in `validate_order.py`, it must mean the same thing.

## Core concepts

**Sleeve** — a logical sub-portfolio with its own mandate, doctrine, journal, and risk limits. Darkhorse has two: Core ($900, conservative) and Satellite ($100, risk capital). Sleeves never cross-fund.

**Doctrine** — the slow-changing rules that govern the agent's behavior. Files under `doctrine/`. Read into every routine. Edited only via PR Aaron merges.

**Routine** — a single scheduled invocation of the agent. Darkhorse has five: pre_market, market_open, midday_scan, end_of_day, weekly_review. Each is stateless; reads its world from disk.

**Debate** — the multi-agent decision flow: researcher → parallel bull_analyst + bear_analyst → risk_manager. The risk_manager owns the final decision.

**Decision** — a single output of a routine. Has an action (BUY / SELL / NO_TRADE), a ticker, a confidence, a thesis, and a reasoning trace. Logged to the journal regardless of whether it placed an order.

**NO_TRADE** — the default action under any uncertainty. Doing nothing is a feature.

**Validate_order** — the Python wall every order passes through before reaching Alpaca. Code-enforced risk policy. Cannot be bypassed by the agent.

**Kill-switch** — a file flag (`KILLSWITCH` at repo root), env var, or remote endpoint that the routine checks first. If on, the routine logs and exits without trading. Aaron can flip it; the agent cannot.

## Risk vocabulary

**Daily loss kill** — single-day stop. If a sleeve drops X% in one trading day, freeze that sleeve until tomorrow. Catches runaway agent behavior. Core: 2% ($18). Satellite: 10% ($10).

**Drawdown halt** — peak-to-trough freeze. If a sleeve drops X% from its high-water mark, freeze until Aaron manually unfreezes. Catches strategy decay. Core: 15% ($135). Satellite: NONE (truncating risk capital defeats its purpose).

**Uncle point** — "the system is broken, stop trusting it." Tighter halt than drawdown; full doctrine review required before resuming. Core: 25% ($225). Satellite: 80% ($80).

**HWM (high-water mark)** — the all-time-high NAV of a sleeve, used as the reference for drawdown calculations. **HWM does not reset after a halt.** Recovery does not change the HWM.

**Position cap** — maximum percentage of sleeve NAV a single position may represent. Core: 10% (~$90). Satellite: 50% ($50).

**Sector cap** — maximum sleeve exposure to a single GICS sector. Core: 25%. Satellite: not enforced (concentration is the point).

**PDT (Pattern Day Trader)** — FINRA rule restricting day-trading on accounts under $25K. Darkhorse's $1k account is well below this threshold; `validate_order` enforces no day-trades to avoid tripping it.

**Idempotency key** — `client_order_id` derived deterministically from `{routine}_{date}_{ticker}_{intent_hash}`. A retry of the same logical order returns the original, not a new one.

## Memory vocabulary

**Episodic memory (L1)** — raw journal of every decision. JSONL, append-only, indefinite retention.

**Semantic memory (L2)** — distilled lessons. Falsifiable, sunset-dated. Lives in `memory/<sleeve>/lessons.md`.

**Anti-pattern (L3)** — named recurring failure mode. Doctrine-level. Lives in `doctrine/anti_patterns.md`.

**Reasoning pattern (L4)** — quarterly snapshot of *how* the agent reasons (not what it concludes). For Aaron's eyes; not fed back to the agent.

**Doctrine (L5)** — the constitution. Promoted from lessons that have been re-validated 3 times.

**Lesson** — a falsifiable rule extracted from journal patterns. Has a hypothesis, evidence, falsification criterion, and sunset date.

**Distillation** — the process of going from raw journal entries to a compressed lesson. Done by the weekly review routine; gated by Aaron's PR merge.

**Sunset** — the expiration date on a lesson. At sunset, the lesson is re-validated against post-creation data. Confirmed → extended. Refined → superseded. Falsified → retired.

**Promotion** — the move from semantic memory to doctrine. Lessons that survive 3 re-validations get promoted (rules earn their durability).

## Calibration vocabulary

**Confidence** — agent's stated probability that the decision will produce the expected outcome. Range 0.0–1.0. Logged with every decision.

**Confidence floor** — the minimum confidence for action. Below the floor, default is NO_TRADE. Default 0.7.

**Calibration error** — predicted confidence minus realized hit rate, per confidence bucket.

**Calibration drift** — change in calibration error over time. Drift > 5pp sustained → freeze new live capital, doctrine review.

**Outcome class** — winner / loser / break-even / open. Set when the decision's horizon elapses.

## Architectural vocabulary

**Harness** — the Python orchestration around the LLM calls. Sets up sessions, loads doctrine, manages caching, logs cost, writes journal. Lives in `src/harness.py`.

**Tool** — a Python function the agent can call. Tools are the agent's hands: `alpaca.submit_order`, `data.quote`, `news.sonar`, etc.

**Tool contract** — the typed signature + docstring of a tool. The agent reads contracts; the harness enforces them.

**Structured output** — Anthropic beta feature that constrains the model to a JSON schema at decode time. Used for the risk-manager's decision JSON.

**Prompt cache** — Anthropic feature that lets us pay 0.10x for repeated stable context. Doctrine, lessons, anti-patterns, tool contracts go in the cache; market state and news do not.

**Tier (model tier)** — Premium / Workhorse / Cheap. Premium is Opus 4.7 for the risk-manager. Workhorse is Sonnet 4.6 for sub-agents. Cheap is Haiku 4.5 for journaling and reflection.

## Research vocabulary

**Hypothesis** — a falsifiable claim about how the system or market behaves. Registered in `RESEARCH/hypotheses/`. Doctrine changes that test a hypothesis must reference it.

**Falsification criterion** — the specific evidence that would prove a hypothesis (or lesson) wrong. Required.

**Side-by-side** — paper accounts running architectural variants in parallel for direct comparison.

**FINSABER discipline** — backtesting practice that uses post-training-cutoff data only, walk-forward windows, full universe including delistings. Named after the FINSABER paper (KDD 2026).

**Look-ahead bias** — using information in a backtest that wouldn't have been available at the decision time. The largest silent failure mode in LLM-driven backtests because the model has read the news.

**Recency bias** — over-weighting the latest information. Mitigated by the forced "30-day base rate" prompt section.

**Adversarial input** — deliberately crafted news/data to mislead the agent (Unicode homoglyphs, prompt injection in news content, fabricated headlines). Tested weekly.

**Wind-down** — the process of converting Core sleeve to SPY-only and treating the system as a research sandbox. Triggered by `riskMitigation.md` §6 conditions.

## Operational vocabulary

**Heartbeat watcher** — a process that confirms a routine actually fired. Cloudflare Worker + local launchd, both posting to Discord on failure.

**Tailnet** — the Tailscale virtual network. The dashboard is reachable only on the tailnet (initially).

**Halt** — generic term for "this sleeve is not trading right now." Caused by daily-loss kill, drawdown halt, uncle point, or kill-switch.

**Unfreeze** — manual action by Aaron to resume trading after a halt. Requires entering a reason; reason logged to audit log.

**Dead-letter** — a failed-to-deliver message (Discord, journal write) that gets stored locally for retry. Failures don't disappear silently.
