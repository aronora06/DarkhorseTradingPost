# Darkhorse Trading Outpost — Initial Build Plan

## 1. Intent

Darkhorse Trading Outpost is **Aaron Parker's personal AI trading assistant**. It is not a SaaS product, not a research demo, and not a generic "I made an AI trader" project. It will eventually be entrusted with **real money** drawn from Aaron's existing capital, and its job is to make trading decisions on Aaron's behalf within strict, code-enforced guardrails.

**Starting capital: $1,000, plus operational costs.** This is intentional — small enough that total loss is survivable as a learning expense, large enough that the system must respect costs, spreads, and the same risk discipline a real strategy would apply at $100k. The total experiment budget is $1,000 of trading capital plus an estimated ~$100/year in operational costs (LLM tokens, hosting, data subscriptions; see `riskMitigation.md` §2.5 for the breakdown).

**Real money from the moment the agent runs.** We do not run an extended paper-trading phase before going live. The reasoning: subscription and token costs accrue whether we're trading paper or real, and we'd rather every dollar of cost produce real signal. The agent goes live at micro-size ($50 of $900 Core deployed) the first day it runs a routine, with capital deployment ramping based on observed behavior. A paper-shadow account runs concurrently for free (using the same prompts, same routines) as a divergence detector, but we never gate progress on a paper-only milestone.

The portfolio is split **90/10**:

- **Core sleeve — $900, conservative.** Long-horizon, lower-turnover. Goal: meet or beat SPY net of costs, with drawdown discipline. Position sizes capped, no leverage, no options, no concentrated bets.
- **Satellite sleeve — $100, higher risk.** Risk capital. Permitted to take more concentrated, shorter-horizon, or thesis-driven trades — including options once a conservative options policy is written. **Loss of the entire satellite sleeve must be survivable; that is the design constraint, not an edge case.**

The two sleeves are managed by the same harness but with **different doctrine files, different position-sizing math, different risk limits, and separate journals**. They never cross-fund. The agent cannot move capital between sleeves without an explicit human-approved action.

The system's job is not to generate alpha out of nothing — it is to be a **disciplined research analyst and execution layer** that follows Aaron's doctrine without the emotional drift of a discretionary trader. Net alpha vs SPY is the ambition; not losing badly is the floor. See [`riskMitigation.md`](./riskMitigation.md) for the full cost/risk mitigation strategy that goes alongside this plan.

## 2. Design Principles

These are non-negotiable and should be referenced in code review:

1. **Risk lives in code, not prompts.** Every order passes through a Python `validate_order()` function that enforces position size, sleeve limits, daily loss kill-switch, drawdown halt, and asset-class allow-lists. You cannot prompt-engineer your way around an `if` statement.
2. **Stateless agents, durable memory.** Each routine wakes with no memory and reads its world from disk. Memory rot, recency bias, and silent state corruption are the failure modes — design against them.
3. **Tested before live; ramp by size, not by paper-vs-live.** Risk modules are unit-tested before any agent code exists. Once the agent runs, it runs against real money — but capital deployment ramps from micro-size ($50) to full size ($900) based on observed behavior. A paper-shadow account runs concurrently throughout as a divergence detector. Architectural changes (new prompt, new model, new tool) run in paper-shadow for ≥ 2 weeks before being merged into the live path; the live system continues unchanged during that window.
4. **Idempotent and reconstructable.** Every decision is journaled with enough context to reconstruct what the agent saw and why it acted. Every order carries an idempotency key. The system can crash and restart mid-routine without double-trading.
5. **Two sleeves, two policies, one harness.** Shared infrastructure, separate doctrine, separate journals, separate limits.
6. **The kill-switch is real.** A file flag, env var, or external endpoint that the harness checks every tick. The agent cannot disable it. Aaron can flip it from his phone.
7. **No options/futures/leverage/crypto until each is explicitly enabled by a written policy.** The agent's default action under uncertainty is **no trade**, not a small trade.
8. **Cost discipline.** At $1,000 AUM, model-spend and trading costs can dominate edge. See `riskMitigation.md` §2 for the tiered model strategy and prompt-caching approach. Target total monthly compute spend ≤ 0.5% of NAV.

## 3. Architecture (v1)

The v1 build deliberately stays close to the YouTube reference (Claude Code routines + Alpaca + file-based memory) so we can ship something working in weeks, not months. The improvements over the reference are called out in §7.

### 3.1 Components

```
DarkhorseTradingOutpost/
├── doctrine/                    # Read by every routine; the rules the agent must follow
│   ├── core_sleeve.md           # Conservative sleeve mandate, sizing, no-fly list
│   ├── satellite_sleeve.md      # Higher-risk sleeve mandate, sizing, allowed asset classes
│   ├── universe.md              # Tradable universe (S&P 500 + curated satellite extension)
│   ├── risk_policy.md           # Hard limits, kill-switch behavior, escalation
│   └── style_guide.md           # How the agent writes journal entries, decision JSON shape
├── memory/                      # Durable state, one folder per sleeve
│   ├── core/
│   │   ├── positions.json       # Latest snapshot, refreshed each routine
│   │   ├── journal/             # JSONL files, one per day
│   │   └── lessons.md           # Compiled by weekly reflection routine
│   └── satellite/
│       └── (same shape)
├── src/
│   ├── routines/                # Each is a Claude Code routine entry point
│   │   ├── pre_market.py
│   │   ├── market_open.py
│   │   ├── midday_scan.py
│   │   ├── end_of_day.py
│   │   └── weekly_review.py
│   ├── tools/                   # Functions the agent can call
│   │   ├── alpaca.py            # Account, positions, orders (with validate_order)
│   │   ├── data.py              # Quotes, bars, fundamentals (Finnhub / yfinance)
│   │   ├── news.py              # Sonar Finance Search + Tavily fallback
│   │   ├── snaptrade.py         # Read-only Fidelity holdings visibility
│   │   ├── journal.py           # Append-only JSONL writer
│   │   └── notify.py            # Discord webhook (free) for daily recaps + alerts
│   ├── risk/
│   │   ├── validate_order.py    # The wall every order must pass through
│   │   ├── sizing.py            # Per-sleeve position sizing math
│   │   ├── kill_switch.py       # Checks file flag + env var every tick
│   │   └── drawdown.py          # Tracks HWM, fires halt + uncle thresholds
│   ├── evaluation/
│   │   ├── backtest_finsaber.py # Walk-forward, post-cutoff, full-universe
│   │   └── calibration.py       # Stated confidence vs realized P&L
│   └── harness.py               # Shared session setup, doctrine loader, logging
├── prompts/
│   ├── system_core.md           # System prompt for core-sleeve agent
│   ├── system_satellite.md      # System prompt for satellite-sleeve agent
│   ├── researcher.md            # Sub-agent: fundamental + sentiment scan
│   ├── bull_analyst.md          # Sub-agent: bullish thesis
│   ├── bear_analyst.md          # Sub-agent: bearish thesis
│   ├── risk_manager.md          # Sub-agent: applies risk policy, makes final call
│   └── reflection.md            # Weekly review prompt
├── config/
│   ├── settings.toml            # Sleeve sizes, limits, schedule, providers
│   └── .env.example
├── tests/
│   ├── test_validate_order.py
│   ├── test_kill_switch.py
│   ├── test_drawdown.py
│   └── test_sizing.py
├── plans/
│   ├── architecture.md
│   ├── initialPlan.md           # this file
│   └── riskMitigation.md        # cost/risk mitigation playbook
└── KILLSWITCH                   # File-flag the harness checks each tick
```

### 3.2 Routine schedule (US Eastern, weekdays)

| Routine | Time | What it does |
|---|---|---|
| `pre_market.py` | 8:30 AM | Read overnight news, update watchlist, draft theses for the day |
| `market_open.py` | 9:35 AM | Execute high-conviction trades from pre-market draft, after first 5 min of price action |
| `midday_scan.py` | 12:30 PM | Review open positions vs theses, scan for new setups, no forced action |
| `end_of_day.py` | 4:05 PM | Close any day-trade flags, write the journal entry, refresh positions snapshot |
| `weekly_review.py` | Fri 5:00 PM | Compile lessons.md, calibration check, drift report, propose doctrine edits |

Per `riskMitigation.md` §3, this 5-routine cadence is deliberately conservative — most opportunities for cost reduction live in *not running* a routine when nothing has changed (event-driven gating).

### 3.3 Multi-agent decision flow (per trade idea)

This is the **TradingAgents-style debate pattern** — measurably better drawdowns in the published benchmarks than single-agent decisions:

```
researcher → [bull_analyst, bear_analyst] (parallel)
           → risk_manager (consumes both, applies policy, outputs decision JSON)
           → validate_order() (Python wall)
           → alpaca.submit_order()
           → journal.append()
```

Decision JSON is constrained via **Anthropic structured outputs** (beta header `structured-outputs-2025-11-13`) so the model literally cannot emit an invalid `side`, `qty`, or `time_in_force`. Confidence floor: act only if `confidence >= 0.7` AND every `risk_check` passes. Default action under any ambiguity: `NO_TRADE`.

Tiered model assignment per role: see `riskMitigation.md` §2. **Risk-manager runs Opus 4.7; researcher / bull / bear run Sonnet 4.6; journaling and reflection run Haiku 4.5.** Prompt caching is enabled across all roles.

### 3.4 Memory model

- **Doctrine** (`doctrine/`) — hand-written by Aaron, read-only to the agent. The constitution.
- **Episodic** (`memory/<sleeve>/journal/YYYY-MM-DD.jsonl`) — one decision per line, append-only. Captures what was seen, what was decided, why, confidence, and (later) realized P&L.
- **Semantic** (`memory/<sleeve>/lessons.md`) — compiled out-of-session by the weekly review. The reflection routine extracts patterns from the journal and proposes edits; **Aaron approves edits before they merge** (PR-style).
- **Recency-bias mitigation** — every routine prompt includes a "30-day base rate" section: what would you have decided 30 days ago with the same setup? This is forced, not optional.

## 4. Tech Stack & Provider Choices

| Concern | Choice | Why |
|---|---|---|
| Premium model (risk-manager) | Claude Opus 4.7 (1M context) | Best agentic + tool-use scores; only the final decision needs it |
| Workhorse model (sub-agents) | Claude Sonnet 4.6 | 5x cheaper than Opus, ~80% SWE-bench, shares cache with Opus |
| Cheap model (journal / reflection) | Claude Haiku 4.5 | $1/$5 per MTok, 4-5x faster than Sonnet |
| Prompt caching | Anthropic 1-hour cache | 0.10x read cost; doctrine + journal are stable across routines |
| Harness | Claude Code routines | Cloud cron, official MCP support, matches the reference video's primitives |
| Broker (execute) | Alpaca | Best DX, paper/live parity, $0 minimum, official MCP server |
| Broker (read-only) | SnapTrade or Plaid Investments → Fidelity | Visibility into existing Fidelity holdings without exposing them to execution |
| Market data (structured) | Finnhub (free tier → paid as needed); yfinance for historical | Cheap, structured. Don't pay Sonar to get a quote. |
| Market data (depth) | Alpaca IEX (free) for v1; upgrade to Algo Trader Plus / Polygon when strategy needs SIP | Avoid premature spend |
| News / web research | Perplexity Sonar Finance Search (Benzinga grounding) + Tavily as fallback | Sonar gives synthesized + cited finance news; Tavily is cheaper for general queries |
| Notifications | Discord webhook (free) | $0, persistent, mobile push, easy to wire. Beats ClickUp. |
| Backtesting | VectorBT (start) → NautilusTrader (when serious) | Industry standard, fast |
| Source control | GitHub | Doctrine edits go through PR review |

## 5. Accounts to Set Up (in this order)

**Free / no-funding required (do these now to unblock v1):**
1. **Alpaca** — sign up at alpaca.markets, generate **paper-trading** API keys. No funding needed for paper. Live keys come later, after the paper window passes.
2. **Anthropic API** — Claude Code billing already in place. Confirm Opus 4.7, Sonnet 4.6, Haiku 4.5 access and structured-outputs beta enrollment. Enable 1-hour prompt caching.
3. **Perplexity Sonar API** — register at perplexity.ai/api, fund $5 initial credit. Verify Finance Search access.
4. **Tavily** — free tier (1,000 credits/mo) is enough for fallback research.
5. **Finnhub** — free tier covers basic quotes/fundamentals. Upgrade later if needed.
6. **Discord** — create a private server with one channel and a webhook. Two minutes.
7. **GitHub** — repo created. Set up branch protection on `main` so doctrine changes go through PR.
8. **SnapTrade** — register, connect your Fidelity account read-only (Fidelity-side approval may take 1–2 days; start early).

**Funded (only when ready to go live — flagged for later):**
9. **Alpaca live trading** — fund the account with **$1,000** split $900 Core / $100 Satellite. *This is the "real money" gate. Do not fund until §6 paper milestones are met.*
10. **Algo Trader Plus** ($99/mo) — only if/when the strategy needs full SIP data. v1 stays on free IEX. (Note: $99/mo is ~10% of NAV/yr at $1k, so this is gated behind a clear demonstrated need.)

**Not needed for v1, possibly later:**
- Polygon (deeper data) — only if Alpaca + Finnhub prove insufficient.
- Interactive Brokers — only if we outgrow Alpaca's asset coverage (futures, international).
- Tastytrade — only if/when satellite sleeve adds active options strategies.

## 6. Build Phases & Milestones

This is the higher-level phase summary. The granular checklist with exit criteria is in `devPhaseChecklist.md`.

### Pre-trading (no costs accruing yet)

- **Phase 0 — Steering** (week 1). All steering documents written, reviewed, and committed.
- **Phase 1 — Risk mitigation R&D** (week 2). Doctrine drafted, test specs written.
- **Phase 2 — Architecture R&D** (week 3). ADRs filed, tool contracts typed, prompt skeletons in place.
- **Phase 3 — Foundations build** (weeks 4–5). Risk modules + tests + hosting on Linode + Discord wired. **No agent code, no LLM calls.** Account funding happens at the end of this phase.

### Live operation begins (costs accruing)

- **Phase 4 — Single-routine live at micro-size** (week 6). $50 of $900 Core deployed. Single-agent (no debate), `market_open` only. Paper-shadow account runs concurrently. Read every journal entry.
- **Phase 5 — Multi-agent debate + full schedule, still micro-size** (weeks 7–8). All five routines, debate flow, tiered model strategy, prompt caching. Capital deployment unchanged at $50.
- **Phase 6 — Learning system + dashboard live** (weeks 9–10). Calibration loop, weekly review, lessons proposed via PR, monthly competitive-landscape review online, dashboard fully functional on Linode. Capital still $50.
- **Phase 7 — Backtest + adversarial gate** (week 11). FINSABER-discipline backtest, adversarial test suite. Outcome gates the size ramp.
- **Phase 8 — Core ramp** (weeks 12–14). $50 → $200 → $500 → $900 Core deployed, one step per week, contingent on clean live-vs-paper diff and no halt firing.
- **Phase 9 — Satellite activation** (week 15+). Satellite goes live at $100, full size. Both sleeves running.
- **Phase 10 — Continuous iteration & research output**. Monthly / quarterly / annual retrospectives. Doctrine evolution. New asset classes only after written policy + paper-shadow validation window.

Total time from kickoff to fully-deployed at $1,000: ~15 weeks. Real-money trading begins at week 6.

## 7. Where the YouTube Approach Leaves Money on the Table

These are the deliberate divergences from the reference video:

### 7.1 Single-agent → multi-agent debate `[medium effort, high value]`
TradingAgents-style researcher → bull/bear → risk-manager flow has measurably better drawdown metrics than single-pass decisions. Baked in from Phase 2.

### 7.2 Risk in prompts → risk in code `[low effort, very high value]`
Most rules in `validate_order.py`, not the system prompt. Single most important divergence.

### 7.3 ClickUp → Discord webhook `[trivial effort, modest value]`
Free, instant mobile push, persistent history. Pushover ($5 one-time) is the alternative.

### 7.4 Cron-only triggers → cron + event-driven hybrid `[medium effort, high value]`
The video runs on cron only. We add cheap/free triggers alongside:
- **Alpaca WebSocket streams** (free) for price/trade events on open positions.
- **TradingView free-tier alerts → webhook → Cloudflare Worker (free)** for technical setup triggers.
- **News webhooks** (Finnhub, Benzinga) instead of polling.
- **GitHub Actions cron** as backup scheduler.
- **Cloudflare Workers Cron Triggers** for pre-warming and post-processing.
- **Local launchd heartbeat-watcher** that alerts if a cloud routine fails to log.

The pattern: cron handles the daily rhythm, events handle the surprises, and a cheap external watcher confirms the cron actually fired.

### 7.5 File memory only → file memory + structured journal + reflection loop `[medium effort, high value]`
`weekly_review.py` compiles JSONL → lessons.md and proposes doctrine edits via PR.

### 7.6 No calibration → calibration logging `[low effort, high value]`
Track stated confidence vs realized outcome. If confidence ≥ 0.7 trades aren't winning ≥ 60% of the time, freeze new live capital.

### 7.7 Sonar-only research → finance-tuned research stack `[low effort, medium value]`
Sonar Finance Search (Benzinga) for narrative + Finnhub for structured data + Tavily as cheap fallback.

### 7.8 No backtesting → FINSABER-style discipline `[high effort, very high value]`
Walk-forward, post-cutoff data, full universe including delistings, no peeking at future news.

### 7.9 No adversarial testing → ticker validation + Unicode/homoglyph defense `[low effort, high value]`
Validate every ticker against a known list, normalize Unicode, run a small adversarial suite each week.

### 7.10 No portfolio visibility → SnapTrade read-only Fidelity link `[low effort, medium value]`
Agent sees full portfolio context (Fidelity holdings) for sizing decisions even though it can only execute through Alpaca.

### 7.11 Single-account → two-sleeve mandate `[medium effort, very high value]`
Specific to Darkhorse. Core conservative + Satellite risk-capital, separate doctrine, separate journals.

### 7.12 No kill-switch → file-flag kill-switch `[trivial effort, very high value]`
A `KILLSWITCH` file in the repo root. Routines check it first.

### 7.13 No idempotency → idempotency keys on every order `[low effort, high value]`
Duplicate routine fires cannot double-trade.

### 7.14 All-Opus → tiered model strategy with prompt caching `[low effort, very high value]`
The reference uses Opus for everything. We use Opus only for the risk-manager final call, Sonnet 4.6 for sub-agents, Haiku 4.5 for journaling/reflection, and 1-hour prompt caching for stable context. **3x cost reduction with no capability loss** — see `riskMitigation.md` §2.

## 8. Decided Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Total starting capital | $1,000 | Aaron's decision — survivable as learning expense, large enough to respect costs |
| Core / Satellite split | 90 / 10 ($900 / $100) | Aaron's decision; conservative split keeps experimentation bounded |
| Working hours | US Eastern, market hours | Standard US equities schedule |
| Universe (Core) | S&P 500, $10 price floor, $25M ADV floor, 25% sector cap | See §8.1 below |
| Universe (Satellite) | S&P 500 + curated extension list (max 25 names), $5 price floor, $5M ADV floor | See §8.1 below |
| Daily loss kill (Core) | -2% of Core NAV ($18) | Tharp-style per-trade aggregate; bug/runaway protection |
| Daily loss kill (Satellite) | -10% of Satellite NAV ($10) | Catches single-day blowups without truncating winners |
| Drawdown halt (Core) | -15% peak-to-trough ($135 from HWM) | Below SPY 2022 DD; won't trigger on benchmark moves |
| Drawdown halt (Satellite) | NONE | Explicit risk capital — halting truncates the right tail you're paying for |
| Uncle point (Core) | -25% peak-to-trough ($225 from HWM) | Manual review required; HWM does not reset |
| Uncle point (Satellite) | -80% ($80 from HWM) | Near-total-loss tripwire for review |
| Recovery rule | Manual unfreeze by Aaron, HWM persists | Human-in-the-loop after any halt |

### 8.1 Universe (decided)

**Core: S&P 500 only.** With ~9–20 positions max at this account size, the binding constraint is bid-ask spread + slippage, not analytical breadth. Large-caps have tight spreads, deep liquidity, and exhaustive news flow Claude can reason about. Filters: $10 price floor, 20-day ADV ≥ $25M, 25% sector cap (GICS), exclude leveraged/inverse ETFs, exclude pending-M&A names with deal spread <2%, exclude names with earnings within next 2 trading days.

**Satellite: S&P 500 + curated extension list (max 25 names).** Aaron proposes the extension list, agent challenges, both must sign off; reviewed monthly with each name carrying a written thesis in `doctrine/satellite-watchlist.md`. Filters: $5 price floor, 20-day ADV ≥ $5M, max single position 50% of Satellite ($50). Satellite may explicitly take earnings risk with a thesis.

**Why not the Russell 1000 or all US equities:** for $1k, the marginal opportunity from names 501–1000 doesn't justify the doubled token cost on every research scan, and auditability degrades. We can revisit at $10k+.

**Refresh cadence:** weekly on Sunday pre-market routine; full reconstitution monthly.

### 8.2 Drawdown thresholds (decided) — explanation

Three related concepts, three numbers:

- **Daily loss kill** is "down X% in a single trading day → freeze that sleeve until tomorrow." Catches runaway agent behavior or a fat-finger immediately. Set at 2% Core / 10% Satellite (the larger Satellite tolerance recognizes that a single concentrated trade can move 10% legitimately).
- **Drawdown halt** is "down X% from the all-time-high of the sleeve → freeze that sleeve until Aaron manually reviews and unfreezes." Catches strategy decay or a regime change where the agent's edge has stopped working. Set at 15% Core (below SPY's 2022 max DD so it won't fire on benchmark moves) and intentionally NONE for Satellite (truncating risk capital defeats its purpose).
- **Uncle point** is "down X% from HWM → the system is broken, stop trusting it." This is the level where you say "okay, the agent is no longer trustworthy with this sleeve." Set at 25% Core (≈ SPY's worst non-2008 DD) and 80% Satellite (near-total-loss tripwire). Hitting the uncle point requires a full doctrine review before resuming, not just unfreeze.

Importantly: **HWM does not reset after a halt.** If the sleeve is halted at -15% and recovers to -5%, the high-water-mark is still the original peak. This prevents the "halt, unfreeze, halt again, unfreeze again" loop that defeats the discipline.

## 9. Open Questions (decide before Phase 1)

- **Options policy for Satellite.** Excluded from v1. When/if reintroduced, what strategies are allowed (covered calls only, defined-risk spreads, no naked)?
- **Tax-lot accounting.** Do we want the journal to reason about specific lots and harvest losses? Adds complexity; suggest deferring to v2.
- **Earnings policy.** Core excludes names with earnings within 2 trading days. Should Satellite have an explicit *positive* earnings playbook (post-earnings drift) or just allow it case-by-case?

## 10. Risks & Things That Will Bite Us

See `riskMitigation.md` for full risk catalogue and mitigation strategies. Top items:

- **Look-ahead bias from Claude's training data.** Backtesting on 2023 is meaningless because the model has read that news. Use post-cutoff data only.
- **Recency bias.** "30-day base rate" prompt section helps but doesn't eliminate.
- **Cost creep.** Tiered model strategy + prompt caching keeps spend at ~$3/month for v1 (see riskMitigation.md §2).
- **Strategic deception.** Agents have demonstrated this under pressure. We do not give the agent capabilities (account funding, etc.) it could misuse.
- **Alpaca outages.** Build retries; do not assume the broker is always there.
- **FINRA day-trade rules.** $1,000 is well below PDT $25k threshold — `validate_order` enforces no day trades.
- **Doctrine drift.** Weekly reviews can slowly liberalize the rules. Doctrine PRs require Aaron to merge with intent; never auto-apply.
- **The honest base rate.** Most personal AI traders do not beat SPY net of costs. Plan for the possibility that this becomes a beautifully-engineered way to underperform an index — riskMitigation.md §6 covers what we do if Phase 4 confirms that.

## 11. Out of Scope for v1

- Crypto trading (Alpaca supports it; we don't enable it).
- Options/futures/forex.
- Non-US securities.
- Tax-lot optimization.
- Multi-user / SaaS exposure.
- Any "fully autonomous, untouched for months" mode. The agent runs on a leash that Aaron periodically tightens.
