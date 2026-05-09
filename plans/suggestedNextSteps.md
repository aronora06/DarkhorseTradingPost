# Suggested Next Steps

My recommendations on how to move from "steering docs written" to "Phase 1 underway." This is a working document — overwrite or strike through items as decisions land.

## 0. Recent framing changes

After the initial steering pass, two changes were locked in:

- **Real money from day 1 of trading.** No extended paper-only phase. Costs (tokens, subscriptions) accrue only when the agent runs, and when the agent runs it trades real money — starting at $50 of $900 Core deployed, ramping over Phase 4–8 to full size. Paper-shadow runs concurrently for free as a divergence detector. See `devPhaseChecklist.md` Phases 4–8 for the ramp schedule.
- **Three retrospective cadences (monthly / quarterly / annual) with year-1 publication readiness.** Year-1 annual report is designed from day 1 to support an arXiv preprint or workshop submission. Anonymization plan baked into data schemas from the start, not retrofitted. See `researchCharter.md` "Publication Readiness."
- **Monthly competitive landscape review** added to the learning system — a dedicated routine that web-reviews other agentic trading systems and proposes adoptions. See `learningSystem.md` §5.

## 1. Things to validate in the docs before locking them

These are design calls I made unilaterally that you should consciously sign off on (or push back on) before they ossify into code.

**Status: signed off (2026-05-08).** All validation items below were reviewed and accepted as-written. Any future changes to these decisions go through ADRs and PR review like any other doctrine change — they are no longer unilateral.

### 1.1 In `learningSystem.md`

- [x] (2026-05-08) **Doctrine promotion path is slow on purpose.** Lessons need 3 re-validations (~18 months) before being promoted to doctrine. This is deliberately conservative — rules that earn permanence should earn it. If you'd rather have a faster path (e.g., 2 re-validations), say so now; this number is hard to change after lessons start accumulating with a specific lifecycle baked in.
- [x] (2026-05-08) **Reasoning audits are for you, not the agent.** I decided not to feed the quarterly reasoning-pattern snapshots back into the agent's prompt because compounding feedback ("the agent reads its own reasoning style and over-corrects") has bad equilibria. The cost is that the agent doesn't directly see how its style drifts. Confirm you're comfortable with this asymmetry.
- [x] (2026-05-08) **Sunset default of 6 months.** Every lesson expires in 6 months absent re-validation. Long enough to gather evidence, short enough to force re-examination. If you want a different default, change it before any lessons exist.

### 1.2 In `frontendAndHosting.md`

- [x] (2026-05-08) **systemd timers on the VPS as primary scheduler, Claude Code routines as backup.** This trades the ergonomics of Claude Code's cloud cron for full visibility/logs/model-flexibility. Reverse if you'd rather start with Claude Code routines and only move to systemd if their reliability disappoints.
- [x] (2026-05-08) **HTMX + Alpine + Tailwind, not Next.js.** Right call for a single-user dashboard but constrains future interactive viz. If you imagine wanting heavy interactivity (custom chart drag-to-zoom, multi-pane layouts, etc.), Next.js is worth the build pipeline cost upfront.
- [x] (2026-05-08) **Tailscale-only access at launch.** Most secure default but requires the Tailscale app on every device. Cloudflare Access (free tier) is a one-step add-on if you want browser-anywhere later.
- [x] (2026-05-08) **SQLite for v1, Postgres later.** Fine at this scale; the journal-as-source-of-truth design means SQLite is just a fast query mirror. Confirm you don't want Postgres from day one to avoid a future migration.

### 1.3 In `riskMitigation.md`

- [x] (2026-05-08) **Hard-pass on China-hosted models** (DeepSeek/Kimi/Qwen). Saves a few dollars/month, costs you data residency. Already discussed; just want this consciously locked.
- [x] (2026-05-08) **Hard-pass on self-hosting.** Doesn't pencil at $1k AUM. If you happen to acquire 36GB+ Apple Silicon for unrelated reasons, revisit.
- [x] (2026-05-08) **Wind-down rule** (`riskMitigation.md` §6) is not negotiable in the moment. If 6-month rolling Sharpe vs SPY < 0, Core converts to SPY automatically. The discipline only works if it's pre-committed. Confirm.

### 1.4 In `initialPlan.md`

- [x] (2026-05-08) **No options/futures/crypto in v1.** Deferred until each gets a written policy. This is conservative; if you have a strong prior that, say, covered calls in Satellite are obviously safe, lock it in now rather than later (later means after the agent already has habits).
- [x] (2026-05-08) **Earnings policy** (the open question in §9). Core excludes names with earnings within 2 trading days. Satellite gets an *explicit* post-earnings drift playbook rather than case-by-case treatment, because "case-by-case" with an LLM is a recipe for inconsistent behavior. Playbook to be drafted in Phase 1 as part of `doctrine/satellite_sleeve.md`.

## 2. Things you specifically need to do (no one else can)

### 2.1 The Satellite watchlist (~25 names)

The plan specifies a curated extension list of up to 25 names for Satellite. **This is your domain-knowledge contribution** — the agent can challenge but not originate. Each name needs a one-paragraph thesis: why it's worth higher-conviction concentration.

Suggested approach: rough-draft 30 candidates, write theses for the strongest 25, the agent challenges them in Phase 1, you converge on a final list before Phase 4 (paper agent).

### 2.2 Open questions in `initialPlan.md` §9

These three need decisions before Phase 1 wraps:

- Options policy for Satellite (when/if reintroduced)
- Tax-lot accounting (defer to v2 is the current position — confirm)
- Earnings policy for Satellite

### 2.3 Account setups with lead times — start these THIS WEEK

These have approval delays; starting them now means they're ready when Phase 3 needs them.

- [ ] **SnapTrade → Fidelity read-only link.** Fidelity-side approval is 1-2 days. Start at snaptrade.com today.
- [ ] **Alpaca account — both paper and live.** ~10 min for paper keys; live account opening + ACH funding is ~3-5 business days. Start the live application now so the account is ready to fund $1,000 by end of Phase 3.
- [ ] **Anthropic Console — confirm:** Opus 4.7, Sonnet 4.6, Haiku 4.5 all accessible; structured-outputs beta enabled (`anthropic-beta: structured-outputs-2025-11-13`); 1-hour prompt cache available; spend cap set to $10/mo.
- [ ] **Perplexity Sonar API.** Verify Finance Search + Sonar Deep Research access (the Deep Research endpoint is what powers the monthly competitive landscape review).
- [x] (2026-05-08) **GitHub repo created**, private. Direct pushes to `main` permitted; agent-proposed doctrine changes still flow through draft PRs as the doctrine-drift mitigation (see `riskMitigation.md` §3 R8).
- [ ] **Discord server.** 2 minutes. Single channel + webhook URL. Save the webhook URL to a password manager.

The rest (Tavily, Finnhub, Linode) can wait until their respective phases.

## 3. A concrete sequence for the first two weeks

### Week 1 — Doc lock + accounts

Day 1-2:
- You read all the steering docs end-to-end with a critical eye
- Mark up the validations from §1 above
- We revise based on your feedback
- Lock the docs (commit to `main`)

Day 3-5:
- All §2.3 account setups kicked off in parallel (most have idle waiting time)
- You start drafting the Satellite watchlist (~25 names with theses)

### Week 2 — Phase 1 deliverables

- Practitioner research dossiers (drawdown halts, universe selection)
- Adversarial input vector catalog
- Doctrine drafts: `risk_policy.md`, `core_sleeve.md`, `satellite_sleeve.md`, `universe.md`, `style_guide.md`, `anti_patterns.md` (initial), `news_sources.md`
- Test specs for `validate_order`, `kill_switch`, `drawdown`, `sizing`, `idempotency`, `adversarial`

End of week 2: doctrine drafted, tests specced, ready for Phase 2 architecture work.

## 4. Lower-priority improvements I'd suggest queuing

These aren't blockers; logging them so they don't get lost:

- **`plans/decisions/0000-template.md`** — set up the ADR template now so when Phase 2 ADRs land they have a consistent shape
- **`RESEARCH/README.md`** — describes the research directory structure (papers/, hypotheses/, practitioner_dossiers/, quarterly/)
- **A `CONTRIBUTING.md`** — even though it's a one-person repo, the contribution rules (PR-only doctrine edits, hypothesis registration for prompt changes, etc.) deserve a single page someone can find later
- **A `CHANGELOG.md`** — tracking material doctrine and architecture changes alongside `git log` is helpful when reasoning about what changed when calibration shifts

## 5. Things I genuinely don't know that you might

These are questions where my reasoning is incomplete and your judgment matters more than mine:

- **How much of your time per week** is the right budget for this? My sequencing assumes you can do the daily Discord check (~2 min) plus a weekly ~30-min doctrine review without it becoming a burden. If your real budget is much less, the auto-pause-after-14-days mitigation matters more and we should make it tighter (e.g., 7 days).
- **Is "research" framing for you, or is it shareable?** The current plan defaults to private with opt-in publication. If you're imagining co-authors, advisors, or a public writeup at month-12, the data schemas and journal formats should be more deliberately publishable from day one (e.g., position sizes anonymized as percentages from the start, not retrofitted).
- **What's your tolerance for total experiment loss?** The plan treats $1,000 as fully expendable, plus ~$100/year in operational costs — total worst-case ~$1,100. If actually losing the full $1k would be more emotionally costly than I'm modeling, the live ramp should be slower (e.g., $25 first instead of $50) and the wind-down rule should be tighter.
- **Do you want a mid-experiment "pause" budget?** 1-2 weeks per quarter where the system runs but you actively don't look at it, to test the auto-pause and recover-from-stale-doctrine paths. Useful research, but only if you'd actually do it.

## 6. My single highest-priority recommendation

If you do nothing else this week: **read `learningSystem.md` and `researchCharter.md` together, in one sitting, with coffee.** Those two are the load-bearing intellectual contributions of this project. Everything else is implementation. If those aren't right, the implementation will be a beautiful execution of the wrong idea.

The other docs you can skim and accept; those two deserve real attention.
