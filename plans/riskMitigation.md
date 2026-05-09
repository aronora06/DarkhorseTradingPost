# Darkhorse Trading Outpost — Cost & Risk Mitigation Plan

This document is the playbook for minimizing the downside of running a personal LLM-driven trading agent on $1,000 of real capital plus operational costs. It is the explicit acknowledgement that **this experiment may not beat SPY**, and the plan for ensuring that if it doesn't, the loss is bounded and recoverable as a learning expense rather than a meaningful financial setback.

It complements `initialPlan.md` — the initial plan describes *what we're building*; this document describes *what could go wrong and how we limit the damage*.

**Total experiment budget:** $1,000 trading capital + ~$100/year operational costs (LLM tokens at ~$3/mo with the tiered+cached strategy in §2, plus ~$5/mo Linode hosting, plus trivial data subscription tiers). Worst-case full-year burn if everything goes wrong: $1,000 + $100 = ~$1,100. The system is designed so this number does not exceed Aaron's pre-committed budget.

---

## 1. Risk Catalogue

The risks below are enumerated from `initialPlan.md` §10 and expanded. Each gets a category, a rough impact and likelihood call, and a mitigation strategy in §3+.

| # | Risk | Category | Impact | Likelihood |
|---|---|---|---|---|
| R1 | Look-ahead bias from model training data corrupts backtests | Evaluation | High | Very High |
| R2 | Recency bias — agent over-weights latest headline | Decision quality | Medium | High |
| R3 | LLM token cost dominates account edge at $1k AUM | Cost | High | High (without mitigation) |
| R4 | Trading costs (spread + slippage) exceed expected edge | Cost | Medium | Medium |
| R5 | Strategic deception — agent acts on info it shouldn't | Behavioral | High | Low |
| R6 | Alpaca outage at market open causes missed exits | Operational | Medium | Medium |
| R7 | FINRA Pattern Day Trader restriction trips on a sub-$25k account | Regulatory | High | Low (mitigated by code) |
| R8 | Doctrine drift — weekly reviews quietly liberalize rules | Governance | High | Medium |
| R9 | Strategy underperforms SPY net of costs (the base rate) | Strategy | Medium | High |
| R10 | Hallucinated ticker / Unicode-homoglyph adversarial news | Adversarial | High | Low |
| R11 | Agent double-trades on routine retry / restart | Operational | High | Medium (without idempotency) |
| R12 | Silent cron failure — routine doesn't fire, no one notices | Operational | Medium | Medium |
| R13 | Provider downtime (Anthropic, Perplexity, Finnhub) | Operational | Low | Medium |
| R14 | Data residency / privacy on prompts containing positions | Privacy | Low | Low (mitigated by provider choice) |
| R15 | Backtest fits to a single regime; live regime differs | Evaluation | High | High |
| R16 | Aaron loses interest, agent runs untended on stale doctrine | Governance | High | Medium |

---

## 2. Cost Mitigation: Tiered Model Strategy + Prompt Caching

This is the single biggest lever. At Opus 4.7-everywhere prices, naive daily spend would be ~$27/month — **2.7% of NAV per year**, which is roughly the alpha we're hoping to generate. That's an unacceptable cost-to-edge ratio. With caching and tiering, we get to ~$3/month (~0.3% of NAV/yr).

### 2.1 Pricing landscape (May 2026)

| Model | Input | Cache read | Output | Notes |
|---|---|---|---|---|
| Claude Opus 4.7 | $5 | $0.50 | $25 | 1M ctx; cache write 1.25x |
| Claude Sonnet 4.6 | $3 | $0.30 | $15 | 1M ctx |
| Claude Haiku 4.5 | $1 | $0.10 | $5 | 200K ctx |
| GPT-5.5 | $5 | $0.50 | $30 | 90% cache discount |
| GPT-5.4 | $2.50 | $0.25 | $15 | |
| GPT-5.4 mini | $0.75 | — | $4.50 | |
| Gemini 3.1 Pro | $2 / $4 | $0.20 / $0.40 | $12 / $18 | >200K context tier higher; Search grounding 5k free/mo then $14/1k |
| Gemini 3.1 Flash-Lite | $0.25 | $0.025 | $1.50 | 1M ctx |
| Grok 4.3 | $1.25 | — | $2.50 | 2M ctx; X/web search $5/1k |
| Grok 4.1 Fast | $0.20 | — | $0.50 | |
| DeepSeek V4-Pro | $0.435 | $0.0036 | $0.87 | 75% off through 5/31/26; reverts after |
| DeepSeek V4-Flash | $0.14 | $0.003 | $0.28 | |
| Kimi K2.6 | $0.60 | $0.15 | $2.50 | OpenAI-compatible |
| Mistral Large 3 | $2 | — | $6 | EU residency |
| Qwen3 Max | $0.78 | — | $3.90 | |

### 2.2 Agentic capability ranking (where verified)

- **Opus 4.7**: 87.6% SWE-bench Verified, 77.3% MCP-Atlas tool-use, 78.0% OSWorld — top of the field for agentic workflows
- **GPT-5.5**: 82.7% SWE-bench Verified, 98.0% τ2-bench Telecom — close second, stronger on some tool-use scenarios
- **Kimi K2.6**: 80.2% SWE-bench Verified, holds 4,000+ tool-call sessions — surprisingly strong but China-hosted
- **DeepSeek V4-Pro**: 80.6% self-reported SWE-bench — but **NIST CAISI flagged degraded held-out performance** vs DeepSeek's own reports, do not trust at face value
- **Sonnet 4.6**: 79.6% SWE-bench Verified — sweet spot for cost/capability
- **Gemini 3.1 Pro**: 78.8–80.6% (varies by source)
- **Haiku 4.5**: 73.3% SWE-bench Verified — ~90% of Sonnet 4.5's agentic perf at 4-5x speed

### 2.3 Tiered model assignment for Darkhorse

| Tier | Role in harness | Model | Why |
|---|---|---|---|
| Premium | Risk-manager final decision | **Claude Opus 4.7** | Highest-stakes call. 87.6% SWE-bench, leads MCP tool-use. Cache cuts cost ~88%. |
| Workhorse | Researcher, bull analyst, bear analyst | **Claude Sonnet 4.6** | 79.6% SWE-bench, 5x cheaper than Opus, shares cache namespace |
| Cheap | Journal compilation, reflection summary, ticker normalization | **Claude Haiku 4.5** | $1/$5 per MTok, 4-5x faster |
| Optional cheap-for-bulk | Pre-screen / news scan | **Gemini 3.1 Flash-Lite** | $0.25/$1.50, native search grounding (5k free/mo), US-hosted |
| **Hard pass** | — | DeepSeek/Kimi/Qwen | China-hosted prompts containing your positions; CAISI flagged DeepSeek perf gap |
| **Hard pass** | — | Self-host on Mac | Hardware ROI doesn't pencil at 5 routines/day |

**Rationale for "hard pass" on China-hosted models:** They are technically capable and cheap. But every prompt would contain Aaron's positions, doctrine, and decision history. Provider TOS allow training on inputs unless you explicitly opt out. Even if the model never appears to misuse the data, you've sent your portfolio strategy to a foreign jurisdiction. The cost savings (a few dollars/month) don't justify the loss of control. If/when Kimi K2.6 weights become available via a US-hosted inference provider (DeepInfra, Together), reconsider — same model, different residency.

**Rationale for "hard pass" on self-hosting:** A 36GB+ Mac running Llama 4 Scout via MLX gets ~60–100 tok/s. To match the agentic capability we need for the risk-manager role, you'd want 70B+ models, which require a $4–6k machine. At 5 routines/day and ~$3/month API spend with tiered+cached commercial models, the hardware payback period is essentially infinite. Self-host only makes sense if Aaron *already* owns the hardware for other reasons.

### 2.4 Prompt caching strategy

**Anthropic 1-hour cache** is the right SKU for Darkhorse. Mechanics:
- Cache write: 2x base input (Opus: $10/MTok)
- Cache read: 0.10x base input (Opus: $0.50/MTok)
- TTL: 1 hour, refreshed on every cache hit

**What to cache (stable across routines, often within session):**
- All doctrine files (`doctrine/*.md`)
- Last 30 days of journal (compressed summary written by `weekly_review.py`)
- Tool/MCP definitions
- Universe definition + current S&P 500 constituent list

**What NOT to cache (changes every routine):**
- Current positions snapshot (read fresh each routine)
- News feed results
- Live quotes / market state
- The routine-specific user message

**Expected cost reduction:** A typical Darkhorse routine sends ~30K prompt tokens, of which ~25K is stable context. Without cache: $0.15 input on Opus. With 1h cache after first hit: ~$0.04. **~73% cut on input alone.**

### 2.5 Daily spend estimates

Per routine token mix: researcher (~8K in / 1.5K out), bull (~6K / 1.2K), bear (~6K / 1.2K), risk-mgr (~12K / 2K), journal (~4K / 1K). 5 routines/day. Stable context ~70% cacheable.

| Strategy | Per routine | Daily (5) | Monthly | % of $1,000 NAV/yr |
|---|---|---|---|---|
| All Opus 4.7, no cache | $0.18 | $0.90 | ~$27 | 2.7% |
| All Opus 4.7, 1h cache | $0.06 | $0.30 | ~$9 | 0.9% |
| Sonnet main + Haiku subagents, cached | $0.025 | $0.13 | ~$4 | 0.4% |
| **Recommended (Opus risk-mgr + Sonnet subagents + Haiku journal, cached)** | **$0.018** | **$0.09** | **~$2.70** | **0.27%** |

Set a hard monthly spend cap (Anthropic Console) at $10/month. If we're over, something is wrong with the cache hit rate or routine count.

---

## 3. Per-Risk Mitigation Detail

### R1 — Look-ahead bias (High / Very High)

**The problem:** Claude has read the news from years past. Backtesting on any data inside its training window is meaningless because the model knows what happened. This is the single biggest silent failure mode in LLM-driven backtesting.

**Mitigation:**
- All backtests use **post-training-cutoff data only** (FINSABER discipline). Anchor on the model's stated cutoff, then add a 3-month buffer.
- For older periods we want to include in training-distribution analysis, anonymize tickers and dates (replace AAPL with "STOCK_A," replace "March 2020" with "Period 12").
- Walk-forward windows with rolling re-fits, not single-shot backtests.
- Treat any backtest result that looks "too good" as evidence of leakage, not evidence of skill.

### R2 — Recency bias (Medium / High)

**The problem:** LLMs over-weight whatever's in the most recent news headline. A single negative article can flip a thesis that was solid yesterday.

**Mitigation:**
- Every routine prompt includes a **"30-day base rate" section**: "what would you have decided 30 days ago with the same setup, ignoring today's news?" This is a forced prompt section, not optional.
- News tool returns time-decayed weighted summaries, not raw recent headlines.
- Bull/bear debate explicitly requires the bear to argue "today's news is noise" as one of its standard prompts.
- Calibration tracking — if confidence-≥0.7 trades that are driven by ≤24h-old news underperform, flag the pattern in weekly review.

### R3 — Token cost dominates edge (High / High without mitigation)

**Mitigation:** §2 above. Tiered models + 1h prompt caching gets us from 2.7% NAV/yr to 0.27%.

### R4 — Trading costs (Medium / Medium)

**The problem:** At $1,000, a 5% Core position is $45. A 10bp spread is $0.045. Round-trip is $0.09 — which sounds tiny until you realize you need to clear that on every trade *before* the strategy's edge starts contributing.

**Mitigation:**
- Universe filters enforce $25M ADV (Core) and $5M ADV (Satellite) — keeps us in tight-spread names.
- Price floor $10 (Core) / $5 (Satellite) — avoids penny-stock spreads.
- Limit orders only by default; market orders require explicit confidence ≥ 0.85 + risk-manager flag.
- No turnover targets — the system is allowed to hold; "do nothing" is a feature.
- Journal records realized slippage on every fill; `weekly_review.py` flags any trade where slippage > 0.5x position-expected-edge.

### R5 — Strategic deception (High / Low)

**The problem:** Apollo Research's ICLR paper showed GPT-4 acted on insider info and lied about it under pressure. We do not assume an LLM agent is incapable of this.

**Mitigation:**
- The agent has **no funding capability**. It cannot move money, cannot transfer between accounts, cannot deposit/withdraw. The Alpaca tool is restricted to order placement/cancellation/query within a pre-funded account.
- All decisions journaled with full reasoning trace; weekly review reads a sample by hand.
- Audit log separate from the journal — append-only, agent has no write access except through a structured tool that the harness controls.
- No long-running sessions — each routine is fresh, so "pressure to deceive across many turns" doesn't accumulate.

### R6 — Broker outage at market open (Medium / Medium)

**Mitigation:**
- Market-open routine runs at **9:35 AM, not 9:30** — lets Alpaca's API stabilize past the open spike.
- All order calls retry on 5xx with exponential backoff (3 attempts, 1s/3s/9s).
- If retries fail, alert via Discord webhook *and* via local launchd heartbeat watcher.
- A position can never be left in an "unknown" state — if we don't get an order confirmation, the next routine reconciles via positions endpoint before placing any new order.
- Hard rule: if Alpaca is down at market open, we don't trade that morning. Missing a trade is cheap. Double-trading or trading on stale state is expensive.

### R7 — PDT restriction (High / Low)

**Mitigation:**
- `validate_order` enforces a hard "no day-trades" rule on accounts under $25K, regardless of what the agent requests.
- Tracked via Alpaca's `daytrade_count` field.
- Setting buffered: rule fires at 2 day-trades in a 5-day rolling window (one below the regulatory 3) so we never get within striking distance.

### R8 — Doctrine drift (High / Medium)

**The problem:** Weekly reviews can quietly liberalize rules. "We should allow 7% positions instead of 5%, the data supports it." Six months later, position sizes are 12% and the discipline is gone.

**Mitigation:**
- **Agent-proposed** doctrine edits go via **GitHub draft PR**, which Aaron reviews and either merges, edits-and-merges, or closes-with-reasoning. Aaron's own doctrine edits may go directly to `main` — branch protection is not enforced — but the discipline expectation is that *material* doctrine changes still flow through a PR for the public-record value (the PR description becomes the rationale citation).
- PR template requires answering: "what would have to be true for this change to be wrong?"
- Quarterly: full doctrine diff against the original Phase 0 version, with a `git log doctrine/` review.
- Doctrine version pinned in every journal entry — if an old setup is referenced, we know which doctrine version evaluated it.

### R9 — Underperforms SPY (Medium / High)

**The honest base rate.** This is what most personal AI traders find. The mitigation is **cost containment so the experiment is cheap**, plus an explicit decision rule for when to wind it down.

**Mitigation:**
- Phase 4 starts at $50 of $900 Core deployed (real money but tiny). The size ramp through Phase 8 takes ~3 weeks at minimum, with each step gated on clean live-vs-paper-shadow diff and no halt firings. If at any ramp step Sharpe vs SPY is materially negative or live-paper divergence appears, we pause the ramp and investigate before proceeding.
- **Wind-down rule:** if rolling 6-month Sharpe vs SPY is < 0 and Core sleeve is > -10% from start, convert Core sleeve to SPY, keep Satellite running as a dedicated experiment-with-risk-capital. This is the "we admit we didn't beat the index, we're now an index-tracker for Core and a sandbox for Satellite" mode.
- Hard wind-down: if Core sleeve hits its uncle point (-25%), liquidate Core to SPY, freeze Satellite, full doctrine review. Honest assessment of whether to continue at all.

### R10 — Adversarial news / hallucinated tickers (High / Low)

**Mitigation:**
- Every ticker the agent emits must be on the current valid-ticker list (refreshed weekly from Alpaca's `assets` endpoint). Off-list tickers fail `validate_order`.
- All news tool returns Unicode-normalize (NFKC) before going into the prompt — homoglyph attacks become visible.
- Adversarial test suite runs weekly: fabricated headlines with hidden-text injection, Unicode tricks, fake earnings beats. The agent is graded on whether `validate_order` catches the resulting bad orders.
- News provider whitelist (`doctrine/news_sources.md`) — agent is told which sources are trusted; everything else is "treat as adversarial until corroborated."

### R11 — Double-trade on retry (High / Medium without idempotency)

**Mitigation:**
- Every order carries a deterministic `client_order_id` derived from `{routine_name}_{date}_{ticker}_{intent_hash}`. Alpaca dedupes; a retry of the same logical order returns the original order, not a new one.
- Journal entries are also keyed; a retry that arrives after the original wrote the journal is a no-op.

### R12 — Silent cron failure (Medium / Medium)

**Mitigation:**
- **Local launchd job on Aaron's always-on Mac** runs every 30 minutes during market hours. It checks the most recent journal entry timestamp; if the expected routine hasn't logged within 15 minutes of its scheduled fire, it pings Discord.
- **Cloudflare Worker (free tier)** as a redundant external watcher. Pings the journal webhook endpoint and alerts if no recent entry.
- Belt and suspenders: silent failure is worse than loud failure.

### R13 — Provider downtime (Low / Medium)

**Mitigation:**
- Sonar → Tavily fallback wired in `news.py`.
- Anthropic → Sonnet-only fallback if Opus is rate-limited (capability degrades, but we keep running).
- Finnhub → yfinance fallback for basic quotes (yfinance is unofficial and rate-limited but free).
- If two or more providers are down, the routine logs an "insufficient data, no trade" entry rather than acting on partial information.

### R14 — Data residency on prompts (Low / Low)

**Mitigation:** Already addressed by sticking to US-hosted providers (Anthropic, OpenAI, Google) for any prompt that contains positions or strategy. Foreign-hosted models get hard-pass per §2.3.

### R15 — Single-regime backtest (High / High)

**Mitigation:**
- Backtest must include at least one bull, one bear, and one sideways regime in walk-forward windows.
- FINSABER discipline catches this when the universe is broad enough.
- "Stress windows" tested explicitly: 2018 Q4, 2020 Q1, 2022 full year, any post-cutoff drawdown periods. Performance in each must be within tolerance.
- Live performance compared against backtest expectations weekly. Material divergence → freeze new capital, investigate.

### R16 — Aaron loses interest (High / Medium)

**The problem:** The system runs on a leash that Aaron periodically tightens. If Aaron stops paying attention, the leash slackens. A bored owner is the most common failure mode for personal trading systems.

**Mitigation:**
- **Auto-pause after 14 days of no doctrine PR / journal review.** The harness checks `git log doctrine/` and `git log memory/` modification dates; if no human activity in 14 days, send a "paused, please review" notification and stop trading until acknowledged.
- Weekly Discord summary is short and actionable — designed to take 2 minutes to read, with one explicit "approve / reject" link for any proposed doctrine change.
- Quarterly written check-in (calendar reminder): is this still worth running?

---

## 4. Cheap/Free Trigger Stack (Cost-Optimized Cron Alternatives)

The reference video uses Claude Code routines on cron. We use that as the spine but supplement with cheap event-driven triggers so we're not paying for routines that have nothing to do.

| Trigger | Cost | What it triggers | Free tier limits |
|---|---|---|---|
| Claude Code routines (cron) | API token cost only | The 5 daily routines | n/a |
| Alpaca WebSocket streams | $0 | Position-level price moves >X% | Unlimited at IEX |
| TradingView free alerts → webhook | $0 (free tier: 1 alert) | Technical setups | 1 free, $14.95/mo for more |
| Cloudflare Workers + Cron Triggers | $0 (free tier) | Watchdog, redundant scheduling, post-processing | 100k invocations/day free |
| GitHub Actions cron | $0 (free tier) | Backup scheduler, weekly reports | 2,000 min/mo free for private |
| Finnhub news webhook | $0 (free tier) | News-driven re-evaluation | Free tier limited |
| Local launchd / cron on Mac | $0 | Heartbeat watcher | n/a |
| Discord webhook | $0 | Notifications | unlimited |

**Pattern:** the 5 cron routines handle the daily rhythm, WebSocket events handle position-level surprises, and the Cloudflare Worker + launchd watcher confirm the cron actually fired. Total trigger infrastructure cost: $0/month.

---

## 5. Spending Caps & Tripwires

| Cap | Threshold | What happens |
|---|---|---|
| Anthropic monthly spend | $10/mo | Hard cap in Anthropic Console; over → routines fail loud |
| Daily routine count | 7 (5 scheduled + 2 event) | Soft cap; >7 triggers a warning |
| Single-routine token spend | $0.50 | Hard cap; over → routine aborts before LLM call returns |
| Trades per day per sleeve | 3 | Hard cap in `validate_order` |
| Average position holding time | ≥ 1 trading day (Core) | Soft floor; sub-1-day cohort flagged in weekly review |

These tripwires exist to catch agentic runaway behavior — a model that decides "I'll just call myself 50 times to research this more" should fail closed, loud, and visibly.

---

## 6. The "It Didn't Work" Plan

Acknowledging the base rate. If after 6 months of live operation the rolling Sharpe vs SPY is < 0:

1. **Core sleeve converts to SPY-only.** The agent stops trading Core; we hold the index.
2. **Satellite continues** as a dedicated sandbox-with-risk-capital.
3. **Doctrine review** identifies what we learned — the harness, the discipline, the cost model are all valuable independent of whether this specific strategy beat the market.
4. **No additional capital** is committed to the trading side. The harness becomes a research tool, not a wealth-management system.

This is not a failure mode — it's the most likely outcome, and the system is designed so that outcome costs less than the alternative of running the experiment for years on hope.

---

## 7. Open Items for Future Risk Review

- **Tax accounting at year-end.** Wash-sale tracking, short-term vs long-term realized gains. Current plan: defer to v2; export trades to TurboTax / a tax tool by hand for 2026 tax year.
- **Insurance gap.** SIPC covers Alpaca up to $500k securities; not relevant at $1k. Worth re-checking if/when we scale.
- **Death/incapacitation handoff.** What happens to the running system if Aaron is unavailable? Currently: KILLSWITCH file in repo + Aaron's standard instructions. Worth formalizing if/when capital scales.
- **Adversarial agent prompt injection** via news content. As news content gets piped into prompts, a determined adversary could plant prompt-injection content on a high-traffic site. Current mitigation is the validate_order wall + ticker whitelist; revisit if attack vectors evolve.
