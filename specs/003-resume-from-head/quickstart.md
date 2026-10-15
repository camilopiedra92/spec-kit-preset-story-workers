# Quickstart: the resume eval

Before: `tests/check.sh` green; `tests/eval/probes.sh "$A/probes" > "$A/probes.txt"` all ok;
`tests/eval/oracle.sh checkout` passes; the owner has confirmed the spend (three `with` runs on this branch and one on `v0.1.0`, about $10,
priced from 002's runs).

```bash
A=/tmp/resume-eval; mkdir -p "$A"
tests/eval/run.sh --state phase-2-done checkout with "$A/with-1"   # rerun at most twice if not counted
uv run python tests/eval/resume_check.py "$A/with-1" | tee "$A/with-1/resume.txt"
# The arm without the rule (research R3): expected to fail its checks.
tests/eval/run.sh --state phase-2-done --preset v0.1.0 checkout with "$A/v010-1"
uv run python tests/eval/resume_check.py "$A/v010-1" | tee "$A/v010-1/resume.txt"
# The rule's other parts (research R3): a feature-directory task; a dirty tree outside it.
tests/eval/run.sh --state phase-2-done-doc-task checkout with "$A/doc-1"
uv run python tests/eval/resume_check.py "$A/doc-1" | tee "$A/doc-1/resume.txt"
tests/eval/run.sh --state phase-2-done-dirty checkout with "$A/dirty-1"
uv run python tests/eval/resume_check.py "$A/dirty-1" | tee "$A/dirty-1/resume.txt"
# A fresh run, with and without the rule (T026, constitution III: what it must not make worse).
tests/eval/run.sh checkout with "$A/fresh-1"
uv run python tests/eval/resume_check.py "$A/fresh-1" | tee "$A/fresh-1/resume.txt"
tests/eval/run.sh --preset v0.1.0 checkout with "$A/fresh-v010-1"
uv run python tests/eval/resume_check.py "$A/fresh-v010-1" | tee "$A/fresh-v010-1/resume.txt"
```

Passes when `resume_check.py` exits 0 on `with-1`, `doc-1` and `dirty-1` (its nine checks:
contract `resume_check.py`);
`v010-1`'s output is recorded beside it, whatever it is. `attribution.py` is not run: its "each phase opens a
worker's brief" reads the final `tasks.md`, whose Phases 1–2 never get a worker here by design.
Record: copy the run's committed files (no stream, no transcripts) and `repo/<feature>/tasks.md` to
`tests/eval/results/003-resume-from-head/`, write the README's Eval 003 entry, then
release `0.2.0`.
