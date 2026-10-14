# Implementation Plan: Resume from HEAD

**Branch**: `003-resume-from-head` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-resume-from-head/spec.md`

## Summary

Replace the fragment's Resume rule with one start rule for every run: the first phase with an
unmarked task, each phase verified from HEAD before its first worker, the worker told to check what
the repository already holds, and a clean tree outside the feature directory (else the run is core's); a fresh run on a
clean tree verifies and marks as before. Measure it with one resume run of the preset on 002's `checkout` fixture in a
"Phases 1–2 done" state (a `run.sh --state` overlay), judged by a script. Release `0.2.0`, then move
dotfiles' `sdd-init` and supertrader to it.

## Technical Context

**Language/Version**: Markdown (the fragment); bash (`run.sh`, `compose.sh`); Python 3.11+ for
`resume_check.py`.

**Primary Dependencies**: as 002: Spec Kit CLI, Claude Code, jq; dev ruff, mypy, pytest.

**Storage**: the state overlay `tests/eval/fixtures/checkout/states/phase-2-done/`; the run's
outputs under `tests/eval/results/003-resume-from-head/`.

**Testing**: `tests/check.sh`; new `test_resume_check.py`; `test_run.py` extended for `--state`;
`compose.sh` phrases per clause, seen red. The eval spends usage (one `with` run on this branch and one on `v0.1.0`, about $6),
confirmed by the owner first.

**Target Platform**: as 001 and 002.

**Project Type**: Spec Kit preset and its eval harness.

**Performance Goals**: none beyond 002's.

**Constraints**: a fresh run on a clean tree verifies and marks as before (FR-006); no question or stop added (constitution
IV); the release only on a passing resume eval (constitution III).

**Scale/Scope**: one fragment paragraph and a brief clause; one `run.sh` flag; one state overlay;
one check script with tests; one paid run; release and two adoptions.

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Append, never replace | The fragment stays appended; it still names the rules it narrows, and `compose.sh` anchors each new clause and refuses the 0.1.0 rule. |
| II. Real CLI | `compose.sh` pinned and latest, as before; the eval installs from a tag-shaped archive. |
| III. Measured | The changed rule ships with its eval (R2, R3): fixture under `tests/`, run headless with the preset, recorded in the README with date, runs (one, a behaviour check), versions. |
| IV. Degrades to core | No new capability is relied on; the change removes a stop the reviewed drafts added; without git or the Agent tool, the existing fallback applies. |
| V. Released by tag | `0.2.0` (MINOR: changed behaviour) with `preset.yml`, CHANGELOG and tag together; the archive allowlist unchanged. |

Re-checked after Phase 1: no violation.

## Project Structure

```text
specs/003-resume-from-head/   spec, plan, research, contracts/harness.md (entities included), quickstart, tasks
commands/speckit.implement.md                      Resume paragraph; the brief's resume clause; the report line
tests/compose.sh                                   phrases per clause; the 0.1.0 rule refused
tests/eval/run.sh, test_run.py                     --state <name>
tests/eval/resume_check.py, test_resume_check.py   the pass conditions (R3)
tests/eval/fixtures/checkout/states/phase-2-done/  Phases 1–2 done, T001–T011 marked
tests/eval/results/003-resume-from-head/           the run's committed outputs
README.md, CHANGELOG.md, preset.yml                Eval 003 entry, 0.2.0
specs/001-story-workers/{spec.md,contracts/fragment.md}   the resume rule they describe
```

**Structure Decision**: reuse 002's harness and fixture; add only the overlay, the flag and the
check (research R2, R3).

## Complexity Tracking

No violations.
