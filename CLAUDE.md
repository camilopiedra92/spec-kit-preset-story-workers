# spec-kit-preset-story-workers

A Spec Kit preset that has `/speckit-implement` hand each phase of a feature's
tasks to a worker subagent on a smaller model, while the main session
verifies, reviews and decides. Projects install it from a tag's archive. This
repository is itself developed with Spec Kit.

## Commands

```bash
tests/check.sh        # the checks CI runs
tests/eval/run.sh <without|with|fallback> <out-dir>    # one eval arm; spends real usage
uv run python tests/eval/attribution.py <out-dir>      # SC-003 on a `with` arm
```

The eval's whole sequence, reruns included, is in
`specs/001-story-workers/quickstart.md`.

## Invariants

@.specify/memory/constitution.md

---

When something here stops being true, correct it in the same commit that made
it false.
