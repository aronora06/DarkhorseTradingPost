# tests/specs/

Markdown **behavior specifications** for Phase 3 Python implementations. Each file is the contract `pytest` / Hypothesis tests will enforce.

**Phase 1 sign-off:** Reviewed and approved by **Aaron Parker** — **2026-05-09**.

## Index

| Spec | Maps to (planned) |
|---|---|
| [`validate_order.md`](validate_order.md) | `src/darkhorse/risk/validate_order.py` |
| [`kill_switch.md`](kill_switch.md) | `src/darkhorse/risk/kill_switch.py` + harness preamble |
| [`drawdown.md`](drawdown.md) | `src/darkhorse/risk/drawdown.py` |
| [`sizing.md`](sizing.md) | `src/darkhorse/risk/sizing.py` |
| [`idempotency.md`](idempotency.md) | Alpaca client + journal writer |
| [`adversarial.md`](adversarial.md) | `RESEARCH/adversarial_vectors.md` test IDs |

Doctrine inputs: [`../../doctrine/`](../../doctrine/) (especially [`../../doctrine/risk_policy.md`](../../doctrine/risk_policy.md)).
