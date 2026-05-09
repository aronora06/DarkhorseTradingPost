# Specification: idempotency & double-fire safety

**Targets:** Alpaca `client_order_id`, journal writers (`plans/riskMitigation.md` §3 R11)

---

## ID-01 — Deterministic client order id

Pattern (conceptual):

```
client_order_id = f"{routine}_{trade_date}_{sleeve}_{symbol}_{intent_hash}"
```

**intent_hash** stable hash of normalized Decision JSON (excluding transient timestamps).

---

## ID-02 — Broker retry semantics

| Scenario | Expect |
|---|---|
| Network timeout then retry with same id | Alpaca returns original order — **no duplicate exposure** |
| Changed qty same id | REJECT locally before submit (hash mismatch) |

---

## ID-03 — Journal dedupe

Journal append keyed by `(routine, trade_date, symbol, intent_hash)` — second write **no-op** with audit log entry.

---

## ID-04 — Crash mid-flight

If process dies after order but before journal: next routine **reconciles positions** before new risk (`plans/riskMitigation.md` §3 R6).

---

## Cross-links

- `RESEARCH/adversarial_vectors.md` OPS-01/02  
- `tests/specs/validate_order.md`
