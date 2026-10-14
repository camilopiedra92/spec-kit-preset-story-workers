# spec-kit-preset-story-workers

A Spec Kit preset that has `/speckit-implement` hand each phase of a feature's
tasks to a worker subagent on a smaller model, while the main session
verifies, reviews and decides. Measured on 2026-10-14 and not adopted: no
release exists until an eval passes (`README.md`). Projects would install it
from a tag's archive. This repository is itself developed with Spec Kit.

## Commands

```bash
tests/check.sh        # the checks CI runs
tests/eval/probes.sh [out-dir]                         # reruns research R1; ~$1.40 of usage
tests/eval/run.sh <without|with|fallback> <out-dir>    # one eval arm; spends real usage
uv run python tests/eval/attribution.py <out-dir>      # SC-003 on a `with` arm
```

The eval's whole sequence, reruns included, is in
`specs/001-story-workers/quickstart.md`.

## Where things live

- `docs/decisions/`: decisions later features build on (MADR). Read the record before reopening a
  decision it covers.

## Invariants

@.specify/memory/constitution.md

---

When something here stops being true, correct it in the same commit that made
it false.
