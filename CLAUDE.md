# spec-kit-preset-story-workers

A Spec Kit preset that has `/speckit-implement` hand each phase of a feature's
tasks to a worker subagent on a smaller model, while the main session
verifies, reviews and decides. Released as v0.1.0 on the owner's acceptance
after two evals that did not show its claimed effect, and as v0.2.0 with its
resume rule measured against v0.1.0 (`README.md`, Eval 003); projects
install it from a tag's archive. This repository is itself developed with
Spec Kit.

## Commands

```bash
tests/check.sh        # the checks CI runs
tests/eval/probes.sh [out-dir]                         # reruns research R1; ~$1.40 of usage
tests/eval/oracle.sh [--write-n] <fixture>             # held-out tests against the reference
tests/eval/run.sh [--state <s>] [--preset <ref>] <fixture> <without|with|fallback> <out-dir>  # one arm; spends usage
uv run python tests/eval/resume_check.py <out-dir>    # the resume eval's checks (003)
tests/eval/runs.sh <attempt-dir> <fixture> <arm>...    # three counted runs per arm; spends usage
uv run python tests/eval/attribution.py <out-dir>      # SC-003 on a `with` arm
uv run python tests/eval/usage.py <out-dir>            # a run's usage, reconciled and attributed
uv run python tests/eval/compare.py --help             # verdict, gate and spend across runs
```

An eval's whole sequence, reruns included: `specs/002-large-phase-remeasure/quickstart.md`
(three runs per arm, the gate, the spend; 001's single-run sequence is in
`specs/001-story-workers/quickstart.md`).

## Where things live

- `docs/decisions/`: decisions later features build on (MADR). Read the record before reopening a
  decision it covers.

## Invariants

@.specify/memory/constitution.md

---

When something here stops being true, correct it in the same commit that made
it false.
