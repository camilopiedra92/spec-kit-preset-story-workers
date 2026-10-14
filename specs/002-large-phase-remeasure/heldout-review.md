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
