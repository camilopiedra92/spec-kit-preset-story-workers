# Held-out review: the `checkout` fixture

The fresh-context review that spec FR-002 requires before the `without` set: every held-out test
checked against the spec text it quotes, the closed list of difficulty sources, and the ambiguity
test. Reviewer: a fresh-context agent that did not write the fixture, 2026-10-14. It computed
every expected value by hand from the fixture's spec, not from the reference implementation.

## Result

- 46 of 46 test cases (33 functions) verified: each names an existing `US<n>-<m>` and quotes it
  verbatim (checked by script); its expected values follow from the spec alone; no two readings of
  the spec give a different asserted value; each uses only the plan's interface.
- Coverage, the closed list of difficulty sources, tie-breaks, intermediate rounding, the order of
  same-kind promotions and of units taken on returns: no findings.

## Findings and resolutions

| ID | Finding | Resolution | Closed |
|---|---|---|---|
| F1 (medium) | The `co` fixture imported all five modules for every test, so one missing module errored all 46 (observed: without `returns.py`, 46 errors) and an arm's score would read 0/46 instead of 36/46. | `co` imports each module when a test first touches it. Observed after the change: without `returns.py`, 10 failed (US3's), 36 passed; the oracle still passes 46/46. | yes |
| F2 (low) | US2-6's aside "the cap is reached partway through the fixed amount" suggests the cap cuts the discount off in stacking order, against the stated rule (the cap is allocated over each line's pre-cap discount). No asserted value rests on it. | The aside now reads "900 in all, more than the cap", in the spec and in the docstring that quotes it. | yes |
| F3 (low) | Two buy-X-get-Y promotions on one SKU are not settled; the reference clamps a line at zero. No held-out test uses it. | Stated as an input the feature does not cover: at most one buy-X-get-Y per SKU in a call. | yes |
| F4 (low) | Parameter ranges are unstated (`buy + get = 0`, a percentage over 100%, negative amounts). No held-out test uses them. | Stated as inputs not covered: X and Y at least 1, a percentage 0–100%, amounts and the cap at least 0. | yes |
| F5 (low) | Which error wins when a call breaks two rules at once is unstated. No held-out test combines them. | Stated as not specified: one of their errors, and no scenario uses such inputs. | yes |

Closure, 2026-10-14: the same reviewer, which did not write the changes, re-checked them: every
docstring quote still verbatim, 46 of 46 passing against the reference, 10 failed and 36 passed
without `returns.py`; F1–F5 closed, no new finding. The reference's clamp of a line's net at zero,
there only for the input F3 now rules out, was removed; the held-out tests still pass 46 of 46.

## Hardening 1 (attempt 2)

Attempt 1's gate closed: three `without` runs each passed 46 of 46. The fixture was hardened in
commit 866a3bc (bulk price US1-9; free units at the bulk price US2-9; a minimum net on a fixed
amount US2-10, US2-11; free units never capped US2-12, US2-13; a restocking fee US3-8, US3-9): 59
held-out tests, task lines per story phase 10, 10 and 9. Each new rule's wrong reading, applied to a
copy of the reference, turned its tests red (re-run by the author after the builder).

A fresh-context reviewer, who wrote none of it, checked the 13 new test cases and every interaction
of the new rules with the old ones, 2026-10-14: every value recomputed by hand from the spec and
matching; every docstring quote verbatim (a script, 0 mismatches); no second reading of any asserted
value; no existing scenario made inconsistent but for H1's prose.

| ID | Finding | Resolution | Closed |
|---|---|---|---|
| H1 (low) | "gets back exactly what those units cost" and US3-3's "a full return refunds all of it" read as general rules, false once a restocking fee exists; no asserted value rests on them. | Now "…tax included, less any restocking fee" and "without a restocking fee, a full return refunds all of it", in the spec and the docstring quoting it; the quote script finds 0 mismatches and the oracle passes 59 of 59. | yes |
| H2 (info) | "A rejected return charges no fee" is guarded only nominally by `test_us3_9_fee_cap_across_returns`. | Left as is: a test strength note, not an ambiguity; no expected value is at stake. | yes |

Closure of H1, 2026-10-14: a fresh-context reviewer, who did not write the change, found it
settled: the new text agrees with the fee rule and with US3-3, US3-8 and US3-9; the docstring still
quotes the spec verbatim; no expected value is affected; no new second reading; the oracle passes 59
of 59. Its cosmetic note (the two rewritten lines past the 100-column wrap) was fixed by rewrapping
them, which leaves the whitespace-normalised quote unchanged.
