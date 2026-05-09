# Suggested Next Steps

Current recommendations for moving from Phase 3 foundations toward paper trading and eventually Phase 4 live micro-size trading. This is a working document; `plans/devPhaseChecklist.md` remains the canonical phase tracker.

## 0. Current status (2026-05-09)

Phase 0-3 complete. **Phase 4a (production harness + paper trading pipeline) is implemented.**

- All Phase 3 foundations remain in place: Python scaffold, `uv`, Ruff, mypy strict, pytest, Hypothesis, CI coverage gates, deterministic risk modules, core utilities, tools, cassette scaffolding, network guardrails.
- **Production Anthropic harness** (`src/darkhorse/harness.py`, 784 lines): researcher (Sonnet 4.6) with tool loop + risk-manager (Opus 4.7) with structured JSON output. Prompt caching (1h TTL), per-call cost telemetry, tenacity retry on transient errors, structlog.
- **End-to-end `market_open` routine** (`src/darkhorse/routines/market_open.py`): compose risk state → researcher → risk-manager → confidence gate (0.70) → `validate_order` → `submit_order` to Alpaca paper → journal + audit + Discord notify.
- **Expanded production prompts**: `system_core.md`, `researcher.md`, `risk_manager.md` with doctrine injection, decision JSON schema, tool guidance, confidence calibration, hard boundaries.
- **159 tests passing**, 88.85% package coverage, 96.32% risk coverage. 42 new tests cover the harness (tool dispatch, cost computation, researcher loop, risk-manager structured output, full session flows, retry predicate) and market_open (NO_TRADE, confidence gate, BUY dry-run, BUY paper submit, kill switch blocks, journal/audit/notify).

**API connections verified (2026-05-09):** Anthropic (Haiku/Sonnet/Opus accessible), Alpaca paper ($1,000 paper equity, ACTIVE), Perplexity Sonar, Tavily, Finnhub, Discord webhook. All keys populated in `.env`. Smoke tests at `tests/smoke/test_api_connections.py`.

**Ready for first paper run.** The harness is fully wired. Next step: run `python -m darkhorse.routines.market_open` against the live Alpaca paper account and verify the journal/audit/notification pipeline.

**Not yet done:** Initial cassette recording from live run, local scheduler, SnapTrade wrapper, dashboard, hosting deployment, live account funding.

**Alpaca live account:** Setup in progress, awaiting authorization. Placeholder keys in `.env`. Live trading deferred until approved and funded.

## 1. Roadmap shift: paper trading first

The original plan specified "real money from day 1 of trading." We are adjusting the sequencing:

1. **Paper trading comes first.** The Alpaca paper account is live and funded ($1,000 paper equity). We build the production harness and run it against paper immediately. This gives us real end-to-end validation of the agent loop, journal/audit pipeline, cost tracking, and Discord notifications without waiting for live account approval.
2. **Live trading activates when ready.** Once the Alpaca live account is approved, funded, and the paper-trading phase has validated the system (minimum 5 clean trading days on paper), we flip to live at $50 Core deployed with paper-shadow running in parallel.
3. **Everything else is unchanged.** Risk guardrails, the $50 deployment cap, drawdown/wind-down rules, and the capital ramp schedule all remain exactly as specified.

This is a sequencing change, not a scope change. Paper trading is no longer just a "shadow" — it is the primary proving ground before real money.

## 2. Previously validated design decisions

**Status: signed off (2026-05-08).** All items reviewed and accepted. See previous version of this file for the full list. Key decisions: slow doctrine promotion, reasoning audits human-only, 6-month lesson sunset, systemd primary scheduler, HTMX/Alpine/Tailwind stack, Tailscale-only access, SQLite v1, hard-pass on China-hosted/self-hosted models, non-negotiable wind-down rule, no options/futures/crypto v1.

## 3. Things Aaron specifically needs to do

### 3.1 The Satellite watchlist (~25 names)

Not a blocker for Core paper trading or Phase 4. Draft when ready.

### 3.2 Account setup — remaining items

> **Canonical detail lives in [`accountSetup.md`](accountSetup.md).**

- [x] (2026-05-09) **Anthropic Console** — API key configured, models accessible (Opus 4.7, Sonnet 4.6, Haiku 4.5).
- [x] (2026-05-09) **Alpaca paper account** — keys configured, $1,000 paper equity, ACTIVE.
- [x] (2026-05-09) **Perplexity Sonar API** — key configured, search working.
- [x] (2026-05-09) **Tavily** — key configured, search working.
- [x] (2026-05-09) **Finnhub** — key configured, quotes working.
- [x] (2026-05-09) **Discord webhook** — configured, test message sent.
- [x] (2026-05-08) **GitHub repo** — private, direct push to `main`.
- [ ] **Alpaca live account** — setup in progress, awaiting authorization. Will update `.env` with real keys when approved.
- [ ] **SnapTrade → Fidelity** — deferred until Fidelity link approval.

## 4. Recommended next implementation sequence

### 4.1 ~~Immediate: build the production harness for paper trading~~ DONE (2026-05-09)

1. [x] **`src/darkhorse/harness.py` production loop** — researcher (Sonnet 4.6) with tool loop + risk-manager (Opus 4.7) with structured output. Prompt caching, cost telemetry, retry, structlog. 784 lines.
2. [x] **`market_open` routine wired end-to-end** — compose → harness → confidence gate → validate_order → submit_order → journal + audit + Discord.
3. [ ] **Record initial cassettes** — run the harness once live (`uv run python -m darkhorse.testing.record market_open_initial`), commit the cassette, then all CI tests replay from it.
4. [ ] **Run the paper routine manually** — verify: decision journaled, audit logged, Alpaca paper order placed (or NO_TRADE), Discord notification sent, cost within budget.

### 4.2 Next: automated paper trading schedule

Once the harness works manually:

1. **Add a local scheduler** — cron or launchd on Aaron's Mac to fire `market_open` at 9:35 AM ET weekdays against Alpaca paper.
2. **Run for 5+ trading days** — Aaron reads every journal entry. Verify: no `validate_order` bypasses, no hallucinated tickers, no unintended day trades, token spend within budget.
3. **Daily Discord recap** — decision summary, cost, any errors.

### 4.3 When Alpaca live is ready: activate live trading

Once the live account is approved, funded, and paper trading has proven clean:

1. **Update `.env`** with real Alpaca live API keys.
2. **Run smoke tests** to verify live connectivity: `DARKHORSE_ALLOW_NETWORK_TESTS=1 uv run pytest tests/smoke/ -v`.
3. **Enable live mode** — same routine, `BrokerEnvironment.LIVE`, $50 Core deployment cap enforced by `R-V01-PHASE-CAP`.
4. **Paper-shadow runs in parallel** — same routine fires against both live and paper, journals compared for divergences.

### 4.4 Phase 3.5 operations (can proceed in parallel)

- Provision Hetzner CX22 Ashburn, Tailscale, systemd skeletons, reverse proxy/TLS, backups, heartbeat watchers.
- Deploy `.env` to the target machine with locked-down permissions.
- Move the scheduler from local Mac to the VPS once stable.

## 5. Lower-priority improvements

These aren't blockers; logging them so they don't get lost:

- **`CONTRIBUTING.md`** — contribution rules for future reference.
- **`CHANGELOG.md`** — tracking doctrine/architecture changes alongside `git log`.

## 6. Open questions for Aaron

- **How much of your time per week** is the right budget? The sequencing assumes daily Discord check (~2 min) plus weekly ~30-min doctrine review.
- **Is "research" framing for you, or is it shareable?** Defaults to private with opt-in publication.
- **What's your tolerance for total experiment loss?** Plan treats $1,000 as fully expendable plus ~$100/year ops.

## 7. Highest-priority recommendation

Run the production harness against the Alpaca paper account. The harness is built, tested, and wired end-to-end. Execute `python -m darkhorse.routines.market_open`, verify the journal/audit/Discord pipeline, record the first cassette, then set up the local scheduler for 5 days of automated paper trading.
