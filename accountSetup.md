# Account Setup Checklist

This is the consolidated, end-to-end guide for setting up every external account, service, and credential the Darkhorse system depends on. It is a **living checklist** — check items off as accounts are provisioned, leave them as a reference for future-Aaron when keys need rotation.

**Audience:** Aaron (or a future-Aaron returning to the project after time away). This document assumes you may have limited operational experience with some of these services and so spells out the steps explicitly.

**Source of truth for env-var names:** [`plans/decisions/0012-configuration-and-secrets.md`](plans/decisions/0012-configuration-and-secrets.md). When in doubt about what to name a variable in `.env`, check that ADR.

---

## How to use this document

1. Work top-to-bottom. Accounts are ordered by **lead time × phase priority** — start the slowest-to-approve ones first.
2. Each account section has:
   - **What it's for** — one line
   - **Required for** — which phase it unblocks
   - **Lead time / cost** — how long approval/funding takes, and what it costs
   - **Steps** — numbered, explicit, with URLs
   - **Info to capture** — exact env-var names plus where to store them now
   - **Verification** — how to test it works
   - **Gotchas** — known traps
3. Check the box once an account is fully set up AND verified. Date the check: `[x] (2026-05-09)`.
4. **Do not paste API keys or secrets into this file or any committed file.** Store them in your password manager (or an offline encrypted note) until Phase 3 creates the `.env` flow.

---

## Where to store secrets right now (before Phase 3)

Phase 3 will create the canonical secret-handling flow per ADR-0012:
- **Dev:** `.env` at project root, gitignored, loaded by `pydantic-settings`
- **Production:** `/etc/darkhorse/.env`, mode 600, root-owned, on the Hetzner host

Until Phase 3 lands, **secrets live in your password manager** (1Password, Bitwarden, KeePassXC, or whatever you already use). Use a single Darkhorse-specific entry — or one entry per service, your choice — and capture each secret with the **exact env-var name** from this document. That way, when Phase 3 asks you to populate `.env`, you already have a 1:1 mapping.

Suggested format inside your password manager (one secure note titled "Darkhorse Secrets"):

```
ANTHROPIC_API_KEY=sk-ant-...
ALPACA_PAPER_API_KEY=...
ALPACA_PAPER_SECRET_KEY=...
(etc.)
```

**What you must never do:**
- Paste secrets into this `accountSetup.md` file.
- Paste secrets into any committed file in the repo (a pre-commit gitleaks hook will block this once Phase 3 lands, but the discipline starts now).
- Send secrets in plain text over Discord, email, Slack, or chat with an AI assistant.
- Reuse the same key across services (each service gets a fresh key).

---

## Quick-reference table

Status as of the latest run-through. Update as you complete items.

| # | Service | Status | Lead time | Cost | Env var(s) |
|---|---|---|---|---|---|
| 1 | GitHub (private repo) | ✅ done | — | $0 | _none in .env_ |
| 2 | Anthropic Console | [ ] pending | minutes | usage-based, $10/mo cap | `ANTHROPIC_API_KEY` |
| 3 | Discord (server + webhook) | ⚠ rotate then ✅ | 2 min | $0 | `DISCORD_WEBHOOK_URL` |
| 4 | Alpaca paper account | [ ] pending | ~10 min | $0 | `ALPACA_PAPER_API_KEY`, `ALPACA_PAPER_SECRET_KEY` |
| 5 | Alpaca live account | [ ] pending | **3–5 business days** (ACH funding) | $0 fees, $1,000 funding | `ALPACA_LIVE_API_KEY`, `ALPACA_LIVE_SECRET_KEY` |
| 6 | SnapTrade → Fidelity | [ ] pending | **1–2 days** (Fidelity approval) | $0 | `SNAPTRADE_CLIENT_ID`, `SNAPTRADE_CONSUMER_KEY` |
| 7 | Perplexity Sonar API | [ ] pending | minutes | ~$5 initial deposit, ~$1/mo target | `PERPLEXITY_API_KEY` |
| 8 | Tavily | [ ] pending | minutes | $0 (free tier 1k/mo) | `TAVILY_API_KEY` |
| 9 | Finnhub | [ ] pending | minutes | $0 (free tier) | `FINNHUB_API_KEY` |
| **Phase 3+ accounts (start when you provision the server, not now)** | | | | | |
| 10 | Hetzner Cloud | [ ] pending | minutes (instant) | ~$4.20/mo | _server-side_ |
| 11 | Tailscale | [ ] pending | minutes | $0 (free tier covers 3 users / 100 devices) | _server-side_ |
| 12 | Backblaze B2 | [ ] pending | minutes | <$0.10/mo | `B2_KEY_ID`, `B2_APPLICATION_KEY` |
| 13 | Cloudflare (DNS / Workers / Access) | [ ] pending | minutes | $0 (free tiers) | _account-level, no env_ |
| 14 | Domain name (optional) | [ ] pending | minutes | ~$10–15/yr | _DNS_ |

**Action items right now:**
- ✅ #5 (Alpaca live) and #6 (SnapTrade) are the longest lead times. **Start these today**, even before the others, because everything else completes faster than they will.

---

## 1. GitHub — DONE

**Status:** Already complete. The repo is private at `aronora06/DarkhorseTradingPost.git` with direct-push to `main` allowed (per ADR — branch protection deliberately not enforced).

No env vars in `.env`. The deploy flow uses SSH-via-Tailscale; GitHub Actions uses `actions/checkout` which is unauthenticated for public clone of a private repo only because it runs inside the repo's CI context.

**Verification:**
- [ ] You can `git push origin main` from your dev machine and it succeeds.
- [ ] The repo's "Settings → General → Visibility" shows "Private."

If/when you want to add a personal access token for any reason (CI deploy, gh CLI on a new machine), generate at `https://github.com/settings/personal-access-tokens` with the minimum scope needed. Don't use a classic PAT; use a fine-grained one limited to this repo.

---

## 2. Anthropic Console

**What it's for:** All LLM calls — the multi-agent debate (Opus 4.7 + Sonnet 4.6 + Haiku 4.5), prompt caching, structured outputs, the weekly review pass.

**Required for:** Phase 4 onward (live agent runs). Verify the account works end-to-end during Phase 1 so there are no surprises later.

**Lead time:** Minutes if you already have a Console account; otherwise minutes to sign up and add a payment method.

**Cost:** Pay-as-you-go usage. Per `plans/riskMitigation.md` §2 the target is ~$3/mo with the tiered+cached strategy. We set a **hard $10/mo cap** in the Console as a tripwire.

### Steps

- [ ] Go to https://console.anthropic.com and sign in (or create an account if you don't already have one for Claude Code billing).
- [ ] Navigate to **Settings → Billing**:
  - [ ] Confirm a payment method is on file.
  - [ ] **Set a monthly spending limit of $10.** Settings → Billing → Spend limits → Monthly. This is the tripwire from `plans/riskMitigation.md` §5.
- [ ] Navigate to **Settings → Members**:
  - [ ] Confirm only Aaron has access. Single-user system.
- [ ] Navigate to **Settings → API Keys**:
  - [ ] Click **Create Key**.
  - [ ] Name: `darkhorse-prod` (you'll create another `darkhorse-dev` later if you want separation; v1 can use a single key).
  - [ ] Copy the key — **this is your only chance to see it.**
  - [ ] Save to your password manager as `ANTHROPIC_API_KEY=sk-ant-...`.
- [ ] Navigate to **Models** (left nav) and confirm access to:
  - [ ] Claude Opus 4.7 (`claude-opus-4-7-20YYMMDD` or whatever the current dated alias is)
  - [ ] Claude Sonnet 4.6 (`claude-sonnet-4-6-20YYMMDD`)
  - [ ] Claude Haiku 4.5 (`claude-haiku-4-5-20YYMMDD`)
  - [ ] If any are missing, request access via the Console; usually instant for paid accounts.
- [ ] Navigate to **Settings → Beta features** (if Anthropic still uses beta enrollment for any features we use):
  - [ ] Verify prompt caching is available (1-hour TTL ephemeral cache).
  - [ ] Verify structured outputs are available (`output_config.format` JSON mode and `strict: true` tool use).
  - As of mid-2026 these features are GA and require no beta header. Verify per `RESEARCH/architecture/anthropic_sdk_features.md`.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `ANTHROPIC_API_KEY` | Console → Settings → API Keys | Password manager |

### Verification

After Phase 3 code exists you'll run `darkhorse smoke-test`. For now, manual:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-haiku-4-5-20250101",
    "max_tokens": 50,
    "messages": [{"role":"user","content":"Reply with the single word: ok"}]
  }'
```

(Substitute your actual key. Use Haiku because it's cheap.) A successful response with `"type":"message"` and content containing "ok" means the key works.

### Gotchas

- The `$10/mo` cap is enforced at the org level. If a routine bug ever generates runaway calls, it stops at the cap — no panic-call-Anthropic moment.
- Keys in the Console can be **revoked instantly** if you suspect they leaked. Generate a new one, update `.env`, restart the service. Annual rotation is good practice (per `plans/riskMitigation.md` §3.13).

---

## 3. Discord (server + webhook)

**What it's for:** All routine recap notifications, alert pages (kill-switch fired, halt triggered, deploy completed), Aaron's daily 2-minute check-in.

**Required for:** Phase 3 onward.

**Lead time:** 2 minutes.

**Cost:** $0.

### Steps

- [ ] Open Discord (desktop, web, or mobile — same outcome).
- [ ] Click the **+** in the server list → **Create My Own** → **For me and my friends** → name it "Darkhorse" (or whatever you like; only you will see it).
- [ ] Right-click the server icon → **Server Settings** → **Integrations** → **Webhooks** → **New Webhook**.
- [ ] Name the webhook "darkhorse-prod". Choose a channel (the default `#general` is fine; or create a `#agent` channel first).
- [ ] Click **Copy Webhook URL**.
- [ ] Save to your password manager as `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`.
- [ ] (Optional) Set the webhook avatar to something distinctive so notifications stand out on your phone.
- [ ] On your phone: install the Discord app, sign in, **enable push notifications** for this server (Server Settings → Notifications → All Messages).

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | Server Settings → Integrations → Webhooks | Password manager |

### Verification

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Darkhorse webhook test ✓"}' \
  "$DISCORD_WEBHOOK_URL"
```

(Substitute the URL.) The message should appear in your Discord channel within a second. A successful response is HTTP 204 (No Content).

### Status (2026-05-09)

- Server "Darkhorse Trading Post" created, webhook "Darkhorse Trading Post Report" provisioned, end-to-end verification message delivered (HTTP 204).
- ⚠ The original webhook URL was shared in chat with an AI assistant during setup, so it has been treated as compromised and **must be regenerated** before live use. Once regenerated, save the new URL only to your password manager — never to a committed file or chat transcript.

### Gotchas

- **Webhook URLs are credentials.** Anyone with the URL can post to your channel. Treat the webhook URL the same as an API key.
- If the webhook leaks (including: pasted into chat, committed to git, posted in a public channel), regenerate from Server Settings → Integrations → Webhooks → ··· → Delete, then create a new one.
- Discord rate-limits webhooks at ~30 requests/minute per webhook. Way more than we need.

---

## 4. Alpaca paper account

**What it's for:** The paper-shadow account (`plans/initialPlan.md`'s "free divergence detector"), local dev integration testing, and Phase 4–5's parallel paper run alongside live trading.

**Required for:** Phase 3 onward.

**Lead time:** ~10 minutes (instant after sign-up).

**Cost:** $0. No funding required for paper.

### Steps

- [ ] Go to https://alpaca.markets and click **Sign Up** (or sign in if you have an account).
- [ ] Complete account creation — you can use the same email as your live application (next section). Paper and live are linked under the same Alpaca account.
- [ ] Once in the dashboard, ensure you're in **Paper Trading** mode (top-right toggle should say "Paper").
- [ ] Navigate to **Paper Account** → **API Keys** (sidebar).
- [ ] Click **Generate New Key** (or **Show** if one already exists).
- [ ] Copy both:
  - The **Key ID** (looks like `PKABCDEFGHIJ123456`)
  - The **Secret Key** (looks like `abc123XYZ...`)
- [ ] Save to your password manager:
  - `ALPACA_PAPER_API_KEY=...`
  - `ALPACA_PAPER_SECRET_KEY=...`

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `ALPACA_PAPER_API_KEY` | Paper Trading → API Keys → Key ID | Password manager |
| `ALPACA_PAPER_SECRET_KEY` | Paper Trading → API Keys → Secret | Password manager |

### Verification

```bash
curl -H "APCA-API-KEY-ID: $ALPACA_PAPER_API_KEY" \
     -H "APCA-API-SECRET-KEY: $ALPACA_PAPER_SECRET_KEY" \
     https://paper-api.alpaca.markets/v2/account
```

You should see JSON with `"status": "ACTIVE"` and a paper account balance (default $100,000 paper money).

### Gotchas

- The paper API uses `paper-api.alpaca.markets`; live uses `api.alpaca.markets`. **Different keys, different URLs.** The Python `alpaca-py` SDK abstracts this with a `paper=True` flag, but be careful when curling.
- Paper accounts never have wash-sale or PDT enforcement — but our code does, because the live account does. Don't develop habits paper-only that won't survive live.

---

## 5. Alpaca live account ⚠ START NOW (3–5 day lead time)

**What it's for:** The actual brokerage account holding the $1,000 trading capital.

**Required for:** Phase 3.6 (account funding) and all live trading from Phase 4 onward.

**Lead time:** **3–5 business days for full ACH funding.** Account application is faster (often same-day approval), but ACH-pull funding takes the full window. **Start today.** Don't wait until Phase 3 to begin this.

**Cost:** $0 in account fees and commissions. You fund $1,000 from your bank account via ACH.

### Steps

- [ ] In the Alpaca dashboard, switch from **Paper Trading** to **Live Trading** (top-right toggle).
- [ ] Click **Open Live Account** (you'll see a prompt if you haven't applied yet).
- [ ] Complete the live application:
  - Personal details (SSN required — Alpaca is a US broker-dealer regulated by FINRA/SIPC).
  - Employment status, annual income range, net worth range, investment experience. Be honest. None of these answers gate access; they're regulatory disclosures.
  - Trading objectives — pick "Speculation" or "Active Trading" (matches what we're doing).
  - Tax-related W-9 info if US person.
- [ ] Submit. Alpaca usually approves within hours but quotes 1–2 business days.
- [ ] **Once approved:** initiate ACH funding from your linked bank.
  - Navigate to **Banking → Add Bank** (sidebar).
  - Plaid integration links most US banks instantly. Manual ACH (routing + account number + micro-deposits) takes 2–3 days for verification.
  - **Initial deposit: $1,000.** This is the full Phase 4–8 trading capital.
- [ ] Wait for the ACH transfer to settle (typically 3–5 business days from initiation, including bank verification).
- [ ] Once funds settle and the account shows `"buying_power": 1000` (or higher with margin):
  - Navigate to **Live Trading → API Keys**.
  - Generate keys.
  - Save to password manager:
    - `ALPACA_LIVE_API_KEY=...`
    - `ALPACA_LIVE_SECRET_KEY=...`

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `ALPACA_LIVE_API_KEY` | Live Trading → API Keys → Key ID | Password manager |
| `ALPACA_LIVE_SECRET_KEY` | Live Trading → API Keys → Secret | Password manager |

### Verification

```bash
curl -H "APCA-API-KEY-ID: $ALPACA_LIVE_API_KEY" \
     -H "APCA-API-SECRET-KEY: $ALPACA_LIVE_SECRET_KEY" \
     https://api.alpaca.markets/v2/account
```

You should see `"status": "ACTIVE"`, `"cash": "1000.00"` (or close to it), and `"buying_power": "1000.00"` (or higher if margin-enabled).

### Gotchas

- **The live key has different URLs than paper.** `api.alpaca.markets` vs `paper-api.alpaca.markets`. The Python SDK handles this via `paper=False`. Make sure the harness routes correctly to the right account based on the routine context.
- **Margin can be enabled or disabled.** For Darkhorse v1 you should **disable margin**: Account → Configuration → Margin Trading → Off. We don't use leverage; this prevents an accidental shorts/leverage path.
- **Day Trading flag.** Account → Configuration → Pattern Day Trader. Should be **off** (we're under $25k anyway, and `validate_order` enforces no day-trades). Confirm.
- **Funding "in_progress"** — if you check the account API and see `"buying_power": 0` while the ACH is pending, that's expected. Wait for it to settle before Phase 4.

---

## 6. SnapTrade → Fidelity ⚠ START NOW (1–2 day lead time)

**What it's for:** Read-only visibility into Aaron's existing Fidelity holdings, so the agent can size Darkhorse positions in the context of total portfolio exposure (without being able to trade Fidelity).

**Required for:** Phase 5 onward (when full sleeve operations need broader context).

**Lead time:** **1–2 days for Fidelity-side approval** of the read-only link. Start now.

**Cost:** $0 (SnapTrade is free for individual users).

### Steps

- [ ] Go to https://snaptrade.com and click **Sign Up** (or **Get Started**).
- [ ] Create an account using your normal email.
- [ ] Once in the SnapTrade dashboard, navigate to **Connections** (or **Brokerages**) → **Add Brokerage**.
- [ ] Select **Fidelity** from the list.
- [ ] You'll be redirected to Fidelity's OAuth flow:
  - Sign in to your Fidelity account.
  - Authorize SnapTrade to read holdings, positions, balances. **Verify the permissions are read-only — no trading scope.**
  - Confirm.
- [ ] Fidelity may take 1–2 business days to fully approve the connection. You'll see "pending" → "active" status in SnapTrade.
- [ ] Once active, navigate to **API → Credentials** in SnapTrade:
  - Generate a `client_id` and `consumer_key` for programmatic access.
  - Save to password manager:
    - `SNAPTRADE_CLIENT_ID=...`
    - `SNAPTRADE_CONSUMER_KEY=...`
- [ ] Note your SnapTrade `userId` (you'll see it in the dashboard) — the API uses this to identify whose accounts to read.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `SNAPTRADE_CLIENT_ID` | SnapTrade → API → Credentials | Password manager |
| `SNAPTRADE_CONSUMER_KEY` | SnapTrade → API → Credentials | Password manager |
| `SNAPTRADE_USER_ID` | SnapTrade → Account → Profile (your user ID) | Password manager (also useful) |

### Verification

After Phase 3 code exists, the `src/darkhorse/tools/snaptrade.py` wrapper will call SnapTrade's API. For a manual test, follow the SnapTrade Python SDK Quickstart (https://docs.snaptrade.com) — list accounts, list positions. You should see your Fidelity holdings.

### Gotchas

- **Read-only is enforced at the SnapTrade level.** The integration scope blocks any order-placement endpoint. Even if Darkhorse code accidentally tried to submit a trade through SnapTrade, it would fail. Belt-and-suspenders.
- If Fidelity changes their OAuth flow or revokes the link (e.g., after a Fidelity password change), you'll need to re-authorize. Plan for this — set a reminder to verify the link works monthly.
- SnapTrade's free tier should cover personal use indefinitely. If they ever introduce paid tiers, evaluate alternatives (Plaid Investments is the closest equivalent) before adding cost.

---

## 7. Perplexity Sonar API

**What it's for:** Finance-grounded news search (Sonar Finance Search), and the **monthly competitive-landscape review** routine (Sonar Deep Research).

**Required for:** Phase 4 (basic news), Phase 6 (monthly competitive review).

**Lead time:** Minutes.

**Cost:** Pay-as-you-go. ~$1/month target for routine news; ~$2 for the monthly Deep Research routine. Initial $5 credit deposit.

### Steps

- [ ] Go to https://www.perplexity.ai/api and sign up.
- [ ] Navigate to **API Keys** → **Generate Key**.
- [ ] Add a payment method and deposit **$5 initial credit**.
- [ ] Verify you have access to:
  - [ ] **Sonar Finance Search** — news with finance-specific grounding (Benzinga and others).
  - [ ] **Sonar Deep Research** — the slower, more thorough endpoint used for the monthly competitive-landscape review.
  - As of 2026 these are both available on standard accounts; if either requires explicit enablement, request via the API dashboard.
- [ ] Save to password manager: `PERPLEXITY_API_KEY=pplx-...`.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `PERPLEXITY_API_KEY` | Perplexity API dashboard → API Keys | Password manager |

### Verification

```bash
curl -X POST https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonar",
    "messages": [{"role":"user","content":"What is AAPL trading at today?"}]
  }'
```

Successful response indicates the key works.

### Gotchas

- Perplexity has multiple model tiers (`sonar`, `sonar-pro`, `sonar-deep-research`). The Deep Research model is much more expensive per call — reserve it for the monthly routine only.
- Set a low alert threshold in the Perplexity dashboard ($10/mo) to catch any runaway usage.

---

## 8. Tavily

**What it's for:** General-purpose web search as a fallback when Sonar fails or for non-finance queries.

**Required for:** Phase 4 onward (fallback path in `src/darkhorse/tools/news.py`).

**Lead time:** Minutes.

**Cost:** $0 on the free tier (1,000 credits/month). We expect to stay well under this.

### Steps

- [ ] Go to https://tavily.com and sign up.
- [ ] In the dashboard, navigate to **API Keys**.
- [ ] Copy the default API key (they generate one on signup).
- [ ] Save to password manager: `TAVILY_API_KEY=tvly-...`.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `TAVILY_API_KEY` | Tavily dashboard → API Keys | Password manager |

### Verification

```bash
curl -X POST https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$TAVILY_API_KEY\", \"query\": \"S&P 500 today\"}"
```

Successful response with `results` array indicates the key works.

### Gotchas

- Free tier resets monthly. If a routine bug bursts the budget, you'll get rate-limited until next month — not billed. Acceptable failure mode.

---

## 9. Finnhub

**What it's for:** Structured market data — quotes, fundamentals, earnings calendar, news. Cheaper than asking Sonar for "what's the price of AAPL."

**Required for:** Phase 3 onward (`src/darkhorse/tools/data.py`).

**Lead time:** Minutes.

**Cost:** $0 on the free tier (60 API calls/minute, sufficient for 5 routines/day).

### Steps

- [ ] Go to https://finnhub.io and sign up.
- [ ] Navigate to **Dashboard → API Keys**.
- [ ] Copy your default key.
- [ ] Save to password manager: `FINNHUB_API_KEY=...`.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `FINNHUB_API_KEY` | Finnhub dashboard → API Keys | Password manager |

### Verification

```bash
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_API_KEY"
```

You should see JSON with `c` (current price), `h` (high), `l` (low), `o` (open), etc.

### Gotchas

- Free tier limits: 60 calls/minute, no premium endpoints (institutional ownership, insider transactions). We don't need premium for v1.
- If we ever upgrade to a paid tier, the env-var name stays `FINNHUB_API_KEY`; just the key value changes.

---

# Phase 3+ accounts (provision when you stand up the server, not now)

These are needed for Phase 3.5 (hosting) and beyond. **Don't set them up yet** — wait until you're actively provisioning the production environment, so the credentials are fresh.

## 10. Hetzner Cloud (per ADR-0005)

**What it's for:** The VPS that hosts the agent, dashboard, scheduler, and SQLite mirror. Hetzner CX22 in Ashburn US.

**Required for:** Phase 3.5.

**Lead time:** Minutes (instant provisioning).

**Cost:** ~$4.20/month (€3.79).

### Steps (when you're ready)

- [ ] Go to https://www.hetzner.com/cloud and sign up.
- [ ] Add a payment method.
- [ ] Create a project named "darkhorse".
- [ ] Within the project: **Add Server**:
  - Location: **Ashburn (ash)**.
  - Image: **Ubuntu 24.04 LTS**.
  - Type: **CX22** (2 vCPU shared, 4 GB RAM, 40 GB NVMe, 20 TB bandwidth).
  - Networking: enable IPv4 (default is dual-stack); confirm IPv4 is included (it is on CX22 by default).
  - SSH Key: upload your SSH public key from your dev machine (`cat ~/.ssh/id_ed25519.pub` if you have one, or generate with `ssh-keygen -t ed25519 -C "darkhorse-deploy"`).
  - Name: `darkhorse-prod`.
- [ ] Click **Create & Buy now**. Server provisions in ~30 seconds.
- [ ] Note the public IPv4 address.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| Hetzner account email + 2FA | Hetzner login | Password manager |
| `darkhorse-prod` public IPv4 | Hetzner Cloud Console | `setup.md` (in `docs/`, when you write it) |
| SSH private key | Your dev machine | Local `~/.ssh/`, also backed up to encrypted password manager note |

### Verification

```bash
ssh root@<IPv4> "uptime"
```

Should print uptime info. If not, verify SSH key was correctly uploaded.

### Gotchas

- **Disable public SSH after Tailscale is up.** First SSH is over public internet to install Tailscale; thereafter, only Tailscale-routed SSH should work. Edit `/etc/ssh/sshd_config` to bind SSH to the Tailscale interface only.
- Hetzner bills monthly in EUR; auto-converted to your card's currency.

---

## 11. Tailscale

**What it's for:** The VPN that grants you and the heartbeat watchers access to the dashboard and SSH on the VPS. No public-internet exposure.

**Required for:** Phase 3.5.

**Lead time:** Minutes.

**Cost:** $0 (Personal plan: 100 devices, 3 users — well within v1 needs).

### Steps (when you're ready)

- [ ] Go to https://tailscale.com and sign up using your GitHub account (or Google/Apple — your choice).
- [ ] Choose **Personal** plan.
- [ ] On your dev Mac: install Tailscale (https://tailscale.com/download), sign in.
- [ ] On your phone: install the Tailscale app, sign in to the same account.
- [ ] On the Hetzner VPS (after first SSH):
  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up
  ```
  Authenticate via the URL it prints (open in browser, sign in to Tailscale).
- [ ] Note the tailnet hostname Hetzner picks (e.g., `darkhorse-prod`).
- [ ] In the Tailscale Admin Console: **Machines** → confirm the VPS appears with a tailnet IP.
- [ ] (Recommended) Enable **MagicDNS**: Admin Console → DNS → enable MagicDNS. Lets you SSH as `ssh root@darkhorse-prod` instead of typing IPs.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| Tailscale account email | Tailscale login | Password manager |
| Tailscale auth key (if you generate one for unattended setup) | Admin Console → Settings → Keys | Password manager |
| Tailscale-issued hostname for the VPS | Admin Console → Machines | `setup.md` |

### Verification

From your dev Mac (with Tailscale running):
```bash
ssh root@darkhorse-prod "uptime"
```

Works without specifying IPv4 — confirms Tailscale + MagicDNS.

### Gotchas

- Tailscale auth keys for unattended provisioning expire by default (90 days). For server installs, generate a **reusable** ephemeral-disabled key.
- The dashboard binds to the Tailscale interface only (per ADR-0004). When you start nginx/uvicorn, ensure they listen on the Tailscale IP, not `0.0.0.0`.

---

## 12. Backblaze B2

**What it's for:** Encrypted off-site backups of `memory/`, `doctrine/`, and the SQLite mirror. Daily, age-encrypted.

**Required for:** Phase 3.5.

**Lead time:** Minutes.

**Cost:** <$0.10/month at our volume.

### Steps (when you're ready)

- [ ] Go to https://www.backblaze.com/cloud-storage and sign up for B2.
- [ ] Verify email; enable 2FA.
- [ ] Create a bucket:
  - Name: `darkhorse-backups`.
  - Files in Bucket are **Private**.
  - Lifecycle: **Keep all versions of the file**, or set a retention rule for 30 daily / 12 monthly.
  - Default Encryption: server-side encryption optional (we encrypt with `age` client-side, so this is belt-and-suspenders).
- [ ] Create an Application Key:
  - Navigate to **App Keys** → **Add a New Application Key**.
  - Name: `darkhorse-prod-backup`.
  - Allow access to: **Specific bucket** → `darkhorse-backups`.
  - Type of access: **Read and Write**.
  - **Disable Delete** (you can't delete prior backups even if the prod machine is compromised).
  - Generate.
- [ ] Save to password manager:
  - `B2_KEY_ID=...`
  - `B2_APPLICATION_KEY=...`
  - `B2_BUCKET_NAME=darkhorse-backups`
- [ ] Generate an `age` keypair on the Hetzner host: `age-keygen -o /etc/darkhorse/backup_age.key`. Note the public key — that's what backups encrypt to. The private key never leaves the server.
- [ ] **Back up the `age` private key to your password manager.** If the VPS is destroyed, you need this key to decrypt backups.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| `B2_KEY_ID` | B2 → App Keys | Password manager |
| `B2_APPLICATION_KEY` | B2 → App Keys | Password manager |
| `B2_BUCKET_NAME` | B2 → Buckets | Password manager (or `settings.toml`) |
| `age` private key | Server `/etc/darkhorse/backup_age.key` | Password manager (encrypted) |

### Verification

After Phase 3.5 backup script lands:
```bash
sudo /opt/darkhorse/scripts/backup.sh
```
Should print "uploaded YYYY-MM-DD.tar.age to b2://darkhorse-backups/" and the file should appear in the B2 bucket browser.

Quarterly drill: spin a fresh test VPS, pull the latest backup, decrypt with the `age` private key, restore to a temporary location, confirm the agent runs against it. Per `plans/devPhaseChecklist.md` Phase 6.2.

### Gotchas

- **Lose the `age` private key, lose the backups.** Storing it only on the server defeats the point. Capture it to your password manager from day 1.
- B2 has a free egress allowance per month — we'll never approach it on a personal-scale backup.

---

## 13. Cloudflare (DNS / Workers / Access)

**What it's for:** (Optional but recommended)
- DNS for any public domain you want pointed at the tailnet.
- Cloudflare Workers for the heartbeat watcher (free tier).
- Cloudflare Access for browser-anywhere dashboard reach (Phase 6+ optional).

**Required for:** Phase 3.5 (heartbeat watcher); Phase 6+ (optional Access for browser-anywhere).

**Lead time:** Minutes.

**Cost:** $0 on free tiers.

### Steps (when you're ready)

- [ ] Go to https://www.cloudflare.com and sign up.
- [ ] (If you have a domain) Add the domain to Cloudflare and update nameservers at your registrar to point at Cloudflare.
- [ ] Navigate to **Workers & Pages** → **Create Worker**:
  - Name: `darkhorse-heartbeat`.
  - Code: a small fetch-and-alert script that pings your Tailscale-exposed `/healthz` endpoint via Tailscale Funnel or a public proxy you set up. (Or run the watcher externally without Cloudflare; Cloudflare just makes it convenient.)
  - **Wait until you've designed the heartbeat in Phase 3.5 before completing this.**
- [ ] (Phase 6+) For Cloudflare Access (browser-anywhere): Configure a Cloudflare Tunnel from the Hetzner host to Cloudflare Edge, gate the tunnel with Access (email allow-list of just your email).

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| Cloudflare account email + 2FA | Cloudflare login | Password manager |
| Cloudflare API token (if you script anything) | My Profile → API Tokens | Password manager |

### Verification

After heartbeat Worker is live, manually break the `/healthz` endpoint (`systemctl stop darkhorse-web`) and confirm a Discord alert fires within ~15 minutes.

### Gotchas

- Cloudflare's free tier is generous but rate-limited per minute. The heartbeat watcher polls every 5 minutes — well under any limit.

---

## 14. Domain name (optional)

**What it's for:** Pretty URL for the dashboard (`darkhorse.aaron.example`) and email-grounded TLS certs if you go beyond Tailscale TLS.

**Required for:** Optional. v1 works fine on the Tailscale-issued hostname (`darkhorse-prod.<tailnet>.ts.net`).

**Lead time:** Minutes.

**Cost:** ~$10–15/year at Cloudflare Registrar, Namecheap, or Porkbun.

### Steps (if you want a domain)

- [ ] Choose a registrar. Cloudflare Registrar is at-cost (no markup) if you already use Cloudflare.
- [ ] Pick a domain. A subdomain of one you own is fine.
- [ ] Point DNS at Cloudflare (if not already).
- [ ] Add an A record for `darkhorse` pointing at... well, you can't easily point public DNS at a Tailscale-only host. Use Cloudflare Tunnel + Access (see #13) so the public DNS points at Cloudflare Edge, which tunnels to your VPS, and Access gates who can hit it.

### Info to capture

| Variable | Source | Where to store |
|---|---|---|
| Domain registrar account | Registrar login | Password manager |

---

## Secret rotation policy

Per `plans/riskMitigation.md` §3 R14:

- **Annual rotation** for all API keys (Anthropic, Alpaca, Perplexity, Tavily, Finnhub, SnapTrade, Discord webhook).
  - Add a calendar reminder for the same week each year.
  - Generate new key, update `.env`, restart service, verify, then revoke old key.
- **Immediate rotation** if you suspect any key has leaked (committed to a repo, posted in chat, observed in logs that someone else can see).
- **Update the password manager** every time a key changes. The password manager remains the canonical store outside `/etc/darkhorse/.env`.

---

## Final verification checklist

Once all the Phase-1-now accounts are set up, you should be able to confirm each one with the curl commands above. Once they're all green:

- [ ] All 9 Phase-1-now accounts (#1–#9) verified end-to-end.
- [ ] All env-var values captured in your password manager with the **exact** names from this document.
- [ ] Spending caps set where applicable (Anthropic $10/mo).
- [ ] Discord webhook fires on test message (verified via curl).
- [ ] Alpaca paper API returns ACTIVE account.
- [ ] Alpaca live application **submitted** (approval may still be pending — that's OK; check daily until approved, then initiate ACH).
- [ ] SnapTrade Fidelity link **initiated** (Fidelity-side approval may still be pending — that's OK; check daily).

When live + SnapTrade are approved and funded/connected, you're unblocked for Phase 3.6 and beyond.

---

## Common gotchas across all services

- **Two-factor authentication** — enable on every account that supports it. Especially Anthropic, Alpaca, GitHub, Cloudflare, Backblaze.
- **Email account hygiene** — all of these go to the same email. If that email is compromised, every account is at risk. Use a unique strong password and 2FA on the email itself.
- **Browser autofill** — convenient for logging in; can be a leak vector if you autofill an API key into a form by mistake. Disable autofill on developer-tools sites if you're nervous.
- **Don't share a key with another machine** — each device that needs an API key gets its own (so rotation is targeted). Single-user system; you can centralize on the production VPS plus your dev Mac, no other devices.

---

## Where this checklist is referenced

- `README.md` — top-level pointer for the "what do I set up first" question
- `suggestedNextSteps.md` §2.3 — week-1 sequencing references this for the per-account detail
- `plans/devPhaseChecklist.md` Phase 3.6 — account funding step references this for the live Alpaca details
- `plans/decisions/0012-configuration-and-secrets.md` — env-var name source of truth

If you change an env-var name in this doc, update ADR-0012 too (and vice versa). Keep them in lockstep.
