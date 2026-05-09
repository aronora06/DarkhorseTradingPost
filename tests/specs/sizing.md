# Specification: position sizing

**Module (future):** `src/darkhorse/risk/sizing.py`

Computations use latest **account snapshot** + doctrine constants.

---

## SZ-01 — Core single-name cap

Default **≤12%** Core NAV per new risk unless documented exception path (`doctrine/core_sleeve.md`).

| NAV | Max $ |
|---:|---:|
| $900 | $108 |

Partial fills must still respect cap on **intended** exposure.

---

## SZ-02 — Sector cap

≤ **25%** Core NAV per GICS sector — reject if breach.

---

## SZ-03 — Satellite concentration

≤ **50%** Satellite NAV (**$50**) hard cap.

First tranche post-earnings playbook ≤ **25%** (**$25**) until add-on rules satisfied (`doctrine/satellite_sleeve.md`).

---

## SZ-04 — Cash & BP feasibility

Reject if **qty × limit_price** exceeds **buying_power − buffer**.

Buffer Phase 3 constant (fail-closed).

---

## Cross-links

- `tests/specs/validate_order.md`  
- `RESEARCH/practitioner_dossiers/sizing_and_pdt.md`
