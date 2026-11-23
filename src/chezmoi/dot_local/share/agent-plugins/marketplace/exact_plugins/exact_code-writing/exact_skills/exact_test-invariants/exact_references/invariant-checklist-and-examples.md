# Invariant checklist and examples

Use this guide when drafting a **Contract & Invariant Table** during interactive test scoping.

## Name the break gate

Before adding any row to the table, name the concrete production bug it would catch, such as a wrong branch, missing side effect, boundary off-by-one, or broken validation rule.
Reject change detectors that only verify constant values, exact internal log or error message wording, or framework wiring without a broken business contract.
Derive every expected outcome by hand from domain rules and inputs rather than transcribing calculations from implementation code.

## Invariant discovery checklist

- **Domain conservation rules**: Totals, balances, counts, or quotas that must be preserved across operations.
- **Boundary transitions**: Minimum, maximum, zero, empty, null/nil, and off-by-one thresholds where behavior flips.
- **Idempotency and state transitions**: Repeated calls, duplicate keys, or invalid state transitions that must reject or remain no-ops.
- **Error and rejection contracts**: Specific domain error types or status outcomes for malformed or unauthorized inputs.
- **Ordering vs. set equivalence**: Whether returned collections require exact sequence order, any-order element matching, or a single matching item.

## Contract & Invariant Table examples

| Case / input | Expected observable outcome | Collection / state inspector | Excluded tautology or internal detail |
|---|---|---|---|
| Split `$10.00` across `3` equal shares | Returns `[334, 333, 333]` cents; total equals `1000` (catches rounding loss or extra cent) | `containsExactly(334, 333, 333)` and sum equals `1000` | Do not assert internal remainder-loop counter or helper call |
| Apply duplicate idempotency key `k1` on settled order | Returns original receipt `r1`; ledger balance unchanged (catches double charge) | Single ledger entry for `k1` | Do not mock or verify internal `dedupeCache.put` |
| Filter active users from `[alice(active), bob(inactive), cara(active)]` | Returns `[alice, cara]` regardless of order (catches inverted predicate or dropped item) | `containsExactlyInAnyOrder(alice, cara)` | Do not assert `user.isActive()` call count or exact error string |

## Anti-patterns during interactive scoping

- Do not ask open-ended blank-slate questions when a concrete draft table can be proposed from public signatures and docs.
- Do not leak private helper names, internal cache keys, or branch labels into invariant rows.
- Do not propose rows whose expected outcome is computed by calling the function under test.
