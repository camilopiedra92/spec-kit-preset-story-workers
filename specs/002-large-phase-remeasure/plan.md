# Implementation Plan: Large-phase remeasure

**Branch**: `002-large-phase-remeasure` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-large-phase-remeasure/spec.md`

## Summary

Remeasure 001's fragment, unchanged, on a new fixture (`checkout`) built so delegation has work to
absorb and core has room to fail: three story phases of 6 to 10 tasks each, money rules that
interact, held-out tests proven by a reference implementation. The harness learns three things:
which fixture to run (`run.sh <fixture> <arm> <out-dir>`), where every token went (the run's session
transcripts, reconciled to `modelUsage` and `costUSD` on every run, split by phase for `with`), and
the verdict across three runs per arm (`compare.py`, medians and spread). A driver, `runs.sh`, runs
each confirmed step of the eval and checks the probes' version and the gate before every try. The `without` runs go
first and gate the rest on core missing at least one held-out test. Then the README records a release
or a second "measured and not adopted".

## Technical Context

**Language/Version**: bash (`tests/eval/run.sh`); Python 3.11+ for `tests/eval/usage.py`,
`tests/eval/compare.py` and the existing `attribution.py` and `bounded.py`; the `checkout` fixture is
Python 3.12 under uv, as `wordstats`.

**Primary Dependencies**: as 001 — Spec Kit CLI (1.1.0 pinned in CI, 1.1.3 locally), Claude Code
(whatever the eval runs on, in `versions.txt`), `jq`; dev: ruff, mypy, pytest, pytest-timeout via uv.
No new dependency: `usage.py` and `compare.py` use the standard library.

**Storage**: files in each run's `<out-dir>`: `transcripts/` (copied), `usage.txt`, `usage.json`;
every attempt's outputs committed under `tests/eval/results/002-large-phase-remeasure/` (spec FR-012).

**Testing**: `tests/check.sh` (ruff, mypy, pytest, `tests/compose.sh`), unchanged as a command; new
pytest modules for `usage.py` and `compare.py` against synthetic transcripts and run directories,
and `test_run.py` extended for the fixture argument and the transcript copy. The `checkout`
fixture's oracle is proven by running its held-out tests against `fixtures/checkout/reference/`.
The eval and probes run by hand: they spend usage.

**Target Platform**: macOS (the owner's machine) for eval runs; CI (ubuntu) for `tests/check.sh`.

**Project Type**: Spec Kit preset, with its eval harness under `tests/`.

**Performance Goals**: SC-001, the `with` median at least 30% below `without`'s.

**Constraints**: the fragment unchanged (FR-006); nothing new in the release archive; each arm's
set of runs confirmed by the owner first (FR-008); a run whose usage does not reconcile exactly is not
counted (SC-008); Claude Code's auto-updater disabled in the runs (FR-004).

**Scale/Scope**: one new fixture (~25–30 tasks, ~15–20 acceptance scenarios, held-out tests and a
reference implementation of 7 modules), two new Python modules with tests, `run.sh` changes, 001's
fixture moved; 9 counted runs plus up to 2 reruns each; README entry; on a pass, a release and
001's rollout steps.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Append, never replace | No fragment change (FR-006); `tests/compose.sh` and `tests/core-anchors.sh` keep checking 001's anchors. |
| II. Verified against the real CLI | Unchanged: CI runs `tests/check.sh` pinned and latest; the eval installs the preset from a tag-shaped archive. |
| III. Behaviour is measured, not asserted | This feature is the measurement: a committed fixture under `tests/`, run headless in three arms, three runs per arm (no longer directional), with every tool's version recorded; a fail is recorded as not adopted with its reason. The usage attribution is itself reconciled on every run, not trusted. |
| IV. Degrades to core | Unchanged fragment; the `fallback` arm runs again on the new fixture (SC-005). |
| V. Released by tag | On a pass: `preset.yml` version, CHANGELOG entry, tag together; `fixtures/` lives under `tests/`, already `export-ignore`, and `tests/compose.sh` still fails if `tests/` reaches the archive. |

Re-checked after Phase 1: no violation; Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-large-phase-remeasure/
├── spec.md
├── plan.md
├── research.md          # R1 where usage can be read, R2 001 attributed, R3–R8 decisions
├── data-model.md        # fixture, run directory, usage attribution, comparison
├── heldout-review.md    # the fresh-context review of the held-out tests' traceability (FR-002)
├── quickstart.md        # the eval's whole sequence, gate and reruns included
├── contracts/
│   └── harness.md       # run.sh, usage.py, compare.py interfaces (deltas on 001's contract)
├── checklists/
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
tests/eval/
├── run.sh                       # now <fixture> <arm> <out-dir>; DISABLE_AUTOUPDATER; copies
│                                #   transcripts; usage.py reconciles before the suite
├── runs.sh                      # NEW: one confirmed step: 3 counted runs per arm, probes and
│                                #   gate checked before every try (research R11)
├── oracle.sh                    # NEW: a fixture's held-out tests against its reference, vs heldout/N
├── usage.py                     # NEW: reconcile transcripts, attribute by part and phase
├── compare.py                   # NEW: medians, spread, gate, SC-001/002/003/005/006/007/008;
│                                #   --gate, --spent <root> --next
├── probes.sh                    # DISABLE_AUTOUPDATER added
├── test_usage.py                # NEW
├── test_compare.py              # NEW
├── test_runs.py                 # NEW: runs.sh against a stub run.sh and stub claude
├── test_oracle.py               # NEW: oracle.sh against a one-function fixture
├── test_run.py                  # extended: fixture argument, versions.txt keys, transcript copy
├── attribution.py, bounded.py, test_attribution.py, test_bounded.py   # unchanged
├── fixtures/
│   ├── wordstats/               # 001's fixture/, heldout/, reference/, moved unchanged
│   │   ├── project/
│   │   ├── heldout/
│   │   └── reference/
│   └── checkout/                # NEW
│       ├── project/             # uv project, CLAUDE.md (001's two rules), specs/001-checkout/
│       │                        # {spec,plan,tasks}.md, .specify/feature.json, uv.lock
│       ├── heldout/             # ≥1 test per acceptance scenario
│       └── reference/           # correct implementation, proves the held-out tests
└── results/
    ├── 2026-10-14/              # 001's committed outputs, unchanged
    └── 002-large-phase-remeasure/
        └── attempt-<k>/         # every attempt: runs, statuses, probes, gate, compare, sc004
pyproject.toml                   # pytest norecursedirs: fixtures
README.md                        # the remeasure entry beside 001's
CHANGELOG.md, preset.yml         # only on a pass: created / release 0.1.0, tag v0.1.0
CLAUDE.md                        # Commands: the new run.sh call, compare.py
```

**Structure Decision**: one directory per fixture (research R6), harness modules flat beside 001's,
each with its tests. `usage.py` and `compare.py` are separate because they run at different times
(per run against per set) on different inputs.

## Complexity Tracking

No violations.
